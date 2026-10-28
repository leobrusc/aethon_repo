"""Nested training-only selection. Never loads the inspected reference pool."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, precision_recall_curve, roc_curve
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline

from aethon_heuristic import is_adversarial_heuristic
from baseline_reliability import atomic_write
from dataset_loader import get_dataset_metadata, load_dataset
from model_selection import build_pipeline, metric
from research_integrity import digest, normalize

CANDIDATES = (("word_bigram", "logistic_regression"),
              ("char_3_5", "logistic_regression"),
              ("char_3_5", "linear_svm"),
              ("char_3_5", "calibrated_linear_svm"),
              ("word_char_union", "logistic_regression"))


def grouped_splits(texts, labels, folds, seed):
    groups = np.asarray([digest(normalize(t)) for t in texts])
    for group in np.unique(groups):
        if len(np.unique(labels[groups == group])) != 1:
            raise ValueError("Conflicting labels on normalized duplicate training texts")
    for label in (0, 1):
        if len(np.unique(groups[labels == label])) < folds:
            raise ValueError("Insufficient independent groups for requested folds")
    splits = list(StratifiedGroupKFold(folds, shuffle=True, random_state=seed).split(texts, labels, groups))
    for train, valid in splits:
        if set(groups[train]) & set(groups[valid]) or len(np.unique(labels[train])) < 2 or len(np.unique(labels[valid])) < 2:
            raise ValueError("Invalid grouped fold; change prespecified fold count")
    return splits


def fit_model(candidate, texts, labels, seed):
    rep, classifier = candidate
    if classifier == "calibrated_linear_svm":
        # Calibrate the WHOLE pipeline so calibration validation never fits TF-IDF.
        base = build_pipeline(rep, "linear_svm")
        cv = grouped_splits(texts, labels, 3, seed)
        model = CalibratedClassifierCV(base, cv=cv, method="sigmoid", n_jobs=1)
    else:
        model = build_pipeline(rep, classifier)
    return model.fit(texts, labels)


def scores(model, texts):
    return model.predict_proba(texts)[:, 1] if hasattr(model, "predict_proba") else model.decision_function(texts)


def threshold_under_cap(labels, values, heuristic, cap):
    """Optimize full OR decision, including a threshold above all OOF scores."""
    if not 0 <= cap <= 1:
        raise ValueError("FPR cap outside [0,1]")
    if not np.isfinite(values).all() or not np.isin(labels, [0, 1]).all():
        raise ValueError("Invalid scores/labels")
    if not (labels == 0).any():
        raise ValueError("Threshold selection requires benign validation examples")
    best = None
    ranking = np.where(heuristic, values.max()+1, values)
    for threshold in np.r_[np.nextafter(values.max(), np.inf), np.unique(values)]:
        prediction = np.logical_or(heuristic, values >= threshold)
        values_metric = metric(labels, prediction, ranking)
        if values_metric["fpr"] <= cap:
            key = (values_metric["f1"], values_metric["recall"], -values_metric["fpr"])
            if best is None or key > best[0]:
                best = key, float(threshold), values_metric
    return None if best is None else {"threshold": best[1], **best[2]}


def select(texts, labels, candidates, folds, seed, cap):
    splits = grouped_splits(texts, labels, folds, seed)
    heuristic = np.asarray([is_adversarial_heuristic(t) for t in texts], bool)
    choices, oof = [], []
    for candidate in candidates:
        values = np.full(len(texts), np.nan)
        for train, valid in splits:
            model = fit_model(candidate, texts[train], labels[train], seed)
            values[valid] = scores(model, texts[valid])
        selected = threshold_under_cap(labels, values, heuristic, cap)
        name = "__".join(candidate)
        choices.append({"candidate": candidate, "status": "selected" if selected else "infeasible_heuristic_floor",
                        **(selected or {})})
        oof.extend({"candidate": name, "training_position": i, "label": int(y), "score": float(s)}
                   for i, (y, s) in enumerate(zip(labels, values)))
    feasible = [c for c in choices if c["status"] == "selected"]
    winner = max(feasible, key=lambda c: (c["f1"], c["recall"], -c["fpr"])) if feasible else None
    return winner, choices, oof


def calibration_report(labels, values, bins=10):
    if not np.isfinite(values).all() or (values < 0).any() or (values > 1).any():
        raise ValueError("Calibration requires probabilities, not SVM margins")
    indices = np.minimum((values * bins).astype(int), bins-1)
    rows = []
    for i in range(bins):
        mask = indices == i
        rows.append({"bin": i, "left": i/bins, "right": (i+1)/bins, "count": int(mask.sum()),
                     "mean_probability": float(values[mask].mean()) if mask.any() else None,
                     "positive_fraction": float(labels[mask].mean()) if mask.any() else None})
    ece = sum(r["count"] * abs(r["mean_probability"]-r["positive_fraction"]) for r in rows if r["count"]) / len(labels)
    return {"brier": float(brier_score_loss(labels, values)), "ece": ece, "bins": bins}, rows


def nested_evaluation(texts, labels, candidates=CANDIDATES, outer_folds=5, inner_folds=3, seed=2026, cap=.10):
    texts, labels = np.asarray(texts, dtype=object), np.asarray(labels, int)
    rows, selections = [], []
    for fold, (train, valid) in enumerate(grouped_splits(texts, labels, outer_folds, seed)):
        selected, choices, _ = select(texts[train], labels[train], candidates, inner_folds, seed+fold, cap)
        selections.append({"outer_fold": fold, "selected": selected, "candidates": choices})
        if selected is None:
            raise ValueError("FPR constraint infeasible for full OR decision; no model promoted")
        model = fit_model(selected["candidate"], texts[train], labels[train], seed+fold)
        values = scores(model, texts[valid])
        for position, value in zip(valid, values):
            heuristic = bool(is_adversarial_heuristic(texts[position]))
            rows.append({"training_position": int(position), "outer_fold": fold,
                         "normalized_sha256": digest(normalize(texts[position])), "label": int(labels[position]),
                         "candidate": "__".join(selected["candidate"]), "score": float(value),
                         "is_probability": selected["candidate"][1] != "linear_svm",
                         "threshold": selected["threshold"], "heuristic": heuristic,
                         "prediction": int(heuristic or value >= selected["threshold"])})
    # AUC cannot pool margins and probabilities from different selected models.
    frame = pd.DataFrame(rows).sort_values("training_position")
    summary = metric(frame.label, frame.prediction, np.zeros(len(frame)))
    summary.pop("auroc"); summary.pop("auprc")
    summary["ranking_metrics"] = "report within outer fold; heterogeneous score scales cannot be pooled"
    return frame, selections, summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--output", default="results/research_2026/generalization")
    p.add_argument("--outer-folds", type=int, default=5)
    p.add_argument("--inner-folds", type=int, default=3)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--fpr-cap", type=float, default=.10)
    p.add_argument("--smoke", action="store_true", help="Two candidates and two outer folds, not a publication estimate")
    a = p.parse_args(); output = Path(a.output)/a.run_id
    config = vars(a) | {"dataset": get_dataset_metadata("prompt_injections_train"), "candidates": CANDIDATES}
    fingerprint = digest(json.dumps(config, sort_keys=True))
    manifest_path = output/"manifest.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        if old["fingerprint"] != fingerprint:
            raise ValueError("Run configuration changed")
        if old["status"] == "DONE":
            for name, sha in old["artifact_hashes"].items():
                if hashlib.sha256((output/name).read_bytes()).hexdigest() != sha:
                    raise ValueError("Artifact integrity mismatch")
            print(json.dumps(old, indent=2)); return
    started = time.perf_counter()
    manifest = {"run_id": a.run_id, "fingerprint": fingerprint, "config": config,
                "commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True)),
                "environment": platform.platform(), "python": platform.python_version(),
                "hardware": platform.uname()._asdict(), "dependencies": {p: importlib.metadata.version(p) for p in ("numpy", "pandas", "scikit-learn", "joblib")},
                "status": "RUNNING", "model": None, "temperature": None, "token_limit": None,
                "checkpoint": "deterministic restart; no partial model reuse", "seed": a.seed}
    atomic_write(manifest_path, json.dumps(manifest, indent=2))
    try:
        training = load_dataset("prompt_injections_train")
        texts, labels = training.prompt_text.to_numpy(), training.label.to_numpy(int)
        candidates = CANDIDATES[:2] if a.smoke else CANDIDATES
        frame, selections, summary = nested_evaluation(texts, labels, candidates, 2 if a.smoke else a.outer_folds, a.inner_folds, a.seed, a.fpr_cap)
        summary["smoke_only"] = a.smoke
        artifacts = {"outer_predictions.csv": frame.to_csv(index=False),
                     "nested_selection.json": json.dumps(selections, indent=2),
                     "summary.json": json.dumps(summary, indent=2),
                     "summary.md": "# Training-only nested evaluation\n\n"+json.dumps(summary, indent=2),
                     "summary.tex": pd.DataFrame([summary]).to_latex(index=False)}
        curve_rows, bin_rows, fold_metrics = [], [], []
        for fold, g in frame.groupby("outer_fold"):
            ranking = np.where(g.heuristic, np.inf, g.score)
            # Replace infinity by a value larger than all finite scores for ranking metrics.
            ranking = np.where(np.isinf(ranking), g.score.max()+1, ranking)
            fold_metrics.append({"outer_fold": int(fold), **metric(g.label, g.prediction, ranking)})
            fpr, tpr, _ = roc_curve(g.label, ranking)
            precision, recall, _ = precision_recall_curve(g.label, ranking)
            curve_rows.extend({"outer_fold": int(fold), "curve": "ROC", "x": float(x), "y": float(y)} for x, y in zip(fpr, tpr))
            curve_rows.extend({"outer_fold": int(fold), "curve": "PR", "x": float(x), "y": float(y)} for x, y in zip(recall, precision))
            if g.is_probability.all():
                calibration, bins = calibration_report(g.label.to_numpy(), g.score.to_numpy())
                fold_metrics[-1].update(calibration)
                bin_rows.extend({"outer_fold": int(fold), **b} for b in bins)
        artifacts.update({"curves.csv": pd.DataFrame(curve_rows).to_csv(index=False),
                          "reliability.csv": pd.DataFrame(bin_rows).to_csv(index=False),
                          "fold_metrics.csv": pd.DataFrame(fold_metrics).to_csv(index=False)})
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        curves, reliability = pd.DataFrame(curve_rows), pd.DataFrame(bin_rows)
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
        for fold in curves.outer_fold.unique():
            for curve, axis in (("ROC", axes[0]), ("PR", axes[1])):
                g = curves[(curves.outer_fold == fold) & (curves.curve == curve)]
                axis.plot(g.x, g.y, label=f"outer {fold}")
        axes[0].set(xlabel="False positive rate", ylabel="True positive rate", title="Outer-fold ROC")
        axes[1].set(xlabel="Recall", ylabel="Precision", title="Outer-fold PR")
        if len(reliability):
            for fold, group in reliability.groupby("outer_fold"):
                valid = group[group["count"] > 0]
                axes[2].plot(valid.mean_probability, valid.positive_fraction, "o-", label=f"outer {fold}")
        axes[2].plot([0, 1], [0, 1], "k--")
        axes[2].set(xlabel="Mean probability", ylabel="Positive fraction", title="Statistical branch calibration")
        for axis in axes:
            axis.set_xlim(0, 1); axis.set_ylim(0, 1)
            if axis.get_legend_handles_labels()[0]: axis.legend(fontsize=7)
        fig.tight_layout()
        from io import StringIO
        buffer = StringIO(); fig.savefig(buffer, format="svg"); plt.close(fig)
        artifacts["diagnostic_curves.svg"] = buffer.getvalue()
        # Selection on all authorized training data is separate from unbiased outer evaluation.
        selected, choices, oof = select(texts, labels, candidates, a.inner_folds, a.seed, a.fpr_cap)
        artifacts["frozen_selection.json"] = json.dumps({"selected": selected, "candidates": choices, "not_promoted_over_historical_B3": True}, indent=2)
        artifacts["selection_oof.csv"] = pd.DataFrame(oof).to_csv(index=False)
        for name, content in artifacts.items(): atomic_write(output/name, content)
        manifest.update(status="DONE", duration_seconds=time.perf_counter()-started, expected_records=len(training), processed_records=len(frame),
                        errors=[], exclusions=[], artifact_hashes={n: hashlib.sha256((output/n).read_bytes()).hexdigest() for n in artifacts})
        atomic_write(manifest_path, json.dumps(manifest, indent=2)); print(json.dumps(summary, indent=2))
    except Exception as exc:
        manifest.update(status="FAILED", error=f"{type(exc).__name__}: {exc}", duration_seconds=time.perf_counter()-started)
        atomic_write(manifest_path, json.dumps(manifest, indent=2)); raise


if __name__ == "__main__": main()
