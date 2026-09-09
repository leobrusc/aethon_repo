"""Detection-only evaluation, metrics, and publication artifact generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional
import hashlib
import json
import platform
import subprocess
import time

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score

from benchmark.middleware import BenchmarkMiddleware
from dataset_loader import DATASET_FILES, get_dataset_metadata, load_dataset


DETECTION_CONDITIONS = ("B1", "B2", "B3", "B4")
EVALUATION_DATASETS = (
    "prompt_injections_test",
    "prompt_injection_core",
    "jailbreakbench_behaviors",
    "wildjailbreak_eval",
    "notinject",
)
ATTACK_ONLY_DATASETS = (
    "red_team_attempts",
    "kaggle_redteam",
    "advbench_harmful",
    "cyberseceval_prompt_injection",
)
LABEL_PROVENANCE = {
    "prompt_injections_train": "source_ground_truth",
    "prompt_injections_test": "source_ground_truth",
    "red_team_attempts": "benchmark_policy_label",
    "kaggle_redteam": "source_ground_truth",
    "advbench_harmful": "benchmark_policy_label",
    "jailbreakbench_behaviors": "source_ground_truth",
    "wildjailbreak_eval": "source_ground_truth",
    "prompt_injection_core": "source_ground_truth",
    "notinject": "benchmark_policy_label",
    "cyberseceval_prompt_injection": "benchmark_policy_label",
}
BOOTSTRAP_METRICS = ("auroc", "auprc", "f1", "fpr")


@dataclass
class DetectionConfig:
    datasets: list[str] = field(default_factory=lambda: list(EVALUATION_DATASETS))
    conditions: list[str] = field(default_factory=lambda: list(DETECTION_CONDITIONS))
    ml_model_path: Optional[str] = None
    seed: int = 42
    limit: Optional[int] = None
    random_sample: bool = False
    output_root: str = "results/revision/detection"
    epsilon: float = 1.2
    bootstrap_seed: int = 2026
    bootstrap_iterations: int = 1000

    def validate(self) -> None:
        unknown_datasets = sorted(set(self.datasets) - set(DATASET_FILES))
        unknown_conditions = sorted(set(self.conditions) - set(DETECTION_CONDITIONS))
        if unknown_datasets:
            raise ValueError(f"Unknown datasets: {unknown_datasets}")
        if unknown_conditions:
            raise ValueError(f"Detection-only conditions are {list(DETECTION_CONDITIONS)}; got {unknown_conditions}")
        if any(c in {"B2", "B3", "B4"} for c in self.conditions) and not self.ml_model_path:
            raise ValueError("B2, B3, and B4 require --ml-model-path.")
        if self.limit is not None and self.limit <= 0:
            raise ValueError("limit must be greater than zero")
        if self.bootstrap_iterations <= 0:
            raise ValueError("bootstrap_iterations must be greater than zero")


def _git_commit(project_root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=project_root, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _prepare_dataset(name: str, config: DetectionConfig) -> pd.DataFrame:
    frame = load_dataset(name)
    if config.limit is None or config.limit >= len(frame):
        return frame
    if config.random_sample:
        return frame.sample(config.limit, random_state=config.seed).sort_index().reset_index(drop=True)
    return frame.head(config.limit).copy()


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def evaluate_prompts(config: DetectionConfig) -> pd.DataFrame:
    """Evaluate only detectors. This function has no target-model initialization path."""
    config.validate()
    records = []
    for dataset_name in config.datasets:
        frame = _prepare_dataset(dataset_name, config)
        for condition in config.conditions:
            middleware = BenchmarkMiddleware(config.ml_model_path, config.epsilon, config.seed)
            for row in frame.itertuples(index=False):
                prompt = str(row.prompt_text)
                decision = middleware.evaluate(prompt, condition)
                records.append({
                    "prompt_id": str(row.prompt_id),
                    "prompt_sha256": _prompt_hash(prompt),
                    "dataset": dataset_name,
                    "true_label": int(row.label),
                    "label_provenance": LABEL_PROVENANCE[dataset_name],
                    "condition": condition,
                    "heuristic_prediction": decision.heuristic_flag,
                    "ml_prediction": decision.ml_prediction,
                    "ml_score": decision.ml_score,
                    "detector_score": decision.detection_score,
                    "final_prediction": int(decision.blocked),
                    "detection_latency_ms": decision.latency_ms,
                    "noisy_audit_count": decision.noisy_audit_count,
                    "seed": config.seed,
                })
    return pd.DataFrame(records)


def _metric_values(frame: pd.DataFrame) -> dict[str, float]:
    truth = frame["true_label"].astype(int).to_numpy()
    predicted = frame["final_prediction"].astype(int).to_numpy()
    score = pd.to_numeric(frame["detector_score"], errors="coerce").to_numpy()
    positives = int((truth == 1).sum())
    negatives = int((truth == 0).sum())
    tp = int(((truth == 1) & (predicted == 1)).sum())
    tn = int(((truth == 0) & (predicted == 0)).sum())
    fp = int(((truth == 0) & (predicted == 1)).sum())
    fn = int(((truth == 1) & (predicted == 0)).sum())
    mixed = positives > 0 and negatives > 0
    has_positive = positives > 0
    valid_scores = np.isfinite(score)
    score_mixed = valid_scores.any() and np.unique(truth[valid_scores]).size == 2
    return {
        "rows": len(frame), "benign": negatives, "adversarial": positives,
        "auroc": float(roc_auc_score(truth[valid_scores], score[valid_scores])) if score_mixed else np.nan,
        "auprc": float(average_precision_score(truth[valid_scores], score[valid_scores])) if score_mixed else np.nan,
        "precision": float(precision_score(truth, predicted, zero_division=0)) if has_positive else np.nan,
        "recall": float(recall_score(truth, predicted, zero_division=0)) if has_positive else np.nan,
        "f1": float(f1_score(truth, predicted, zero_division=0)) if has_positive else np.nan,
        "fpr": float(fp / negatives) if negatives else np.nan,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "class_status": "mixed" if mixed else ("adversarial_only" if has_positive else "benign_only"),
    }


def _bootstrap_indices(truth: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    parts = []
    for label in np.unique(truth):
        indices = np.flatnonzero(truth == label)
        parts.append(rng.choice(indices, size=len(indices), replace=True))
    return np.concatenate(parts)


def bootstrap_confidence_intervals(
    frame: pd.DataFrame, seed: int = 2026, iterations: int = 1000,
) -> dict[str, float]:
    """Return reproducible stratified percentile intervals on fixed predictions."""
    point = _metric_values(frame)
    truth = frame["true_label"].astype(int).to_numpy()
    rng = np.random.default_rng(seed)
    samples = {name: [] for name in BOOTSTRAP_METRICS if np.isfinite(point[name])}
    for _ in range(iterations):
        sampled = frame.iloc[_bootstrap_indices(truth, rng)]
        values = _metric_values(sampled)
        for name in samples:
            if np.isfinite(values[name]):
                samples[name].append(values[name])
    intervals = {}
    for name in BOOTSTRAP_METRICS:
        values = samples.get(name, [])
        intervals[f"{name}_ci_low"] = float(np.quantile(values, 0.025)) if values else np.nan
        intervals[f"{name}_ci_high"] = float(np.quantile(values, 0.975)) if values else np.nan
    return intervals


def summarize_group(frame: pd.DataFrame, bootstrap_seed: int, bootstrap_iterations: int) -> dict:
    values = _metric_values(frame)
    values.update(bootstrap_confidence_intervals(frame, bootstrap_seed, bootstrap_iterations))
    latency = pd.to_numeric(frame["detection_latency_ms"], errors="coerce").dropna()
    values.update({
        "mean_latency_ms": float(latency.mean()),
        "median_latency_ms": float(latency.median()),
        "p95_latency_ms": float(latency.quantile(0.95)),
        "p99_latency_ms": float(latency.quantile(0.99)),
    })
    return values


def summarize_by(frame: pd.DataFrame, columns: list[str], seed: int, iterations: int) -> pd.DataFrame:
    rows = []
    for keys, group in frame.groupby(columns, sort=False, dropna=False):
        keys = keys if isinstance(keys, tuple) else (keys,)
        row = dict(zip(columns, keys))
        row.update(summarize_group(group, seed, iterations))
        rows.append(row)
    return pd.DataFrame(rows)


def dataset_characteristics(datasets: Iterable[str]) -> pd.DataFrame:
    ordered = list(dict.fromkeys(["prompt_injections_train", *datasets]))
    rows = []
    for name in ordered:
        frame = load_dataset(name)
        benign = int((frame.label == 0).sum())
        adversarial = int((frame.label == 1).sum())
        mixed = benign > 0 and adversarial > 0
        metadata = get_dataset_metadata(name)
        rows.append({
            "dataset": name, "rows": len(frame), "benign": benign, "adversarial": adversarial,
            "class_status": "mixed" if mixed else ("adversarial_only" if adversarial else "benign_only"),
            "label_provenance": LABEL_PROVENANCE[name],
            "used_for_training": name == "prompt_injections_train",
            "used_for_evaluation": name in datasets,
            "auroc_valid": mixed, "auprc_valid": mixed, "fpr_valid": benign > 0,
            "source_file": metadata["file"], "sha256": metadata["sha256"],
        })
    return pd.DataFrame(rows)


def _write_table(frame: pd.DataFrame, stem: Path) -> None:
    frame.to_csv(stem.with_suffix(".csv"), index=False)
    display = frame.fillna("NA").astype(str)
    header = "| " + " | ".join(display.columns) + " |\n"
    divider = "| " + " | ".join("---" for _ in display.columns) + " |\n"
    rows = "".join("| " + " | ".join(row) + " |\n" for row in display.to_numpy())
    stem.with_suffix(".md").write_text(header + divider + rows, encoding="utf-8")
    stem.with_suffix(".tex").write_text(frame.to_latex(index=False, na_rep="NA", float_format="%.6f"), encoding="utf-8")


def _ablation_view(frame: pd.DataFrame, include_dataset: bool = False) -> pd.DataFrame:
    columns = (["dataset"] if include_dataset else []) + [
        "condition", "auroc", "auprc", "precision", "recall", "f1", "fpr",
        "median_latency_ms", "p95_latency_ms",
    ]
    renamed = frame[columns].rename(columns={
        "dataset": "Dataset", "condition": "Condition", "auroc": "AUROC", "auprc": "AUPRC",
        "precision": "Precision", "recall": "Recall", "f1": "F1", "fpr": "FPR",
        "median_latency_ms": "Median latency (ms)", "p95_latency_ms": "p95 latency (ms)",
    })
    return renamed


def write_detection_artifacts(frame: pd.DataFrame, config: DetectionConfig, project_root: Path) -> dict:
    output = Path(config.output_root)
    if not output.is_absolute():
        output = project_root / output
    output.mkdir(parents=True, exist_ok=True)
    tables = project_root / "results" / "revision" / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / "per_prompt_results.csv", index=False)
    by_dataset = summarize_by(frame, ["dataset", "condition"], config.bootstrap_seed, config.bootstrap_iterations)
    by_condition = summarize_by(frame, ["condition"], config.bootstrap_seed, config.bootstrap_iterations)
    by_condition.insert(0, "aggregation", "micro_pooled_fixed_evaluation_rows")
    numeric_metrics = ["auroc", "auprc", "precision", "recall", "f1", "fpr", "mean_latency_ms", "median_latency_ms", "p95_latency_ms", "p99_latency_ms"]
    macro = by_dataset.groupby("condition", as_index=False)[numeric_metrics].mean(numeric_only=True)
    macro.insert(0, "aggregation", "macro_unweighted_dataset_mean_valid_metrics")
    by_dataset.to_csv(output / "metrics_by_dataset.csv", index=False)
    by_condition.to_csv(output / "metrics_by_condition.csv", index=False)
    macro.to_csv(output / "metrics_by_condition_macro.csv", index=False)
    by_dataset[["dataset", "condition", "tp", "tn", "fp", "fn"]].to_csv(output / "confusion_matrices.csv", index=False)
    by_dataset[["dataset", "condition", "mean_latency_ms", "median_latency_ms", "p95_latency_ms", "p99_latency_ms"]].to_csv(output / "latency_summary.csv", index=False)
    characteristics = dataset_characteristics(config.datasets)
    _write_table(characteristics, output / "dataset_characteristics")
    _write_table(_ablation_view(by_condition), tables / "ablation_comparison")
    _write_table(_ablation_view(by_dataset, include_dataset=True), tables / "ablation_comparison_by_dataset")
    _write_table(_ablation_view(macro), tables / "ablation_comparison_macro")
    manifest = {
        "experiment_type": "detection_only",
        "scientific_pipeline": "prompt -> detector -> prediction/score -> prompt-level metrics",
        "target_llm_initialized": False,
        "metric_grouping": ["dataset", "condition"],
        "conditions": {
            "B1": "heuristic only (binary operating-point score)",
            "B2": "TF-IDF + Logistic Regression only",
            "B3": "heuristic OR ML deterministic cascade",
            "B4": "B3 detector plus differentially private audit telemetry",
        },
        "aggregation": {
            "micro": "pool all fixed evaluation rows, retaining each dataset row once per condition",
            "macro": "unweighted arithmetic mean across dataset-level metrics; undefined values excluded",
        },
        "bootstrap": {"method": "stratified percentile", "confidence": 0.95, "seed": config.bootstrap_seed, "iterations": config.bootstrap_iterations},
        "config": asdict(config),
        "datasets": characteristics.to_dict(orient="records"),
        "model_metadata_file": str(Path(config.ml_model_path).with_suffix(".metadata.json")) if config.ml_model_path else None,
        "git_commit": _git_commit(project_root),
        "python_version": platform.python_version(), "sklearn_version": sklearn.__version__,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "experiment_manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return {"rows": len(frame), "output_root": str(output), "metrics_by_dataset": len(by_dataset)}


def run_detection_benchmark(config: DetectionConfig) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    started = time.perf_counter()
    frame = evaluate_prompts(config)
    result = write_detection_artifacts(frame, config, project_root)
    result["runtime_seconds"] = time.perf_counter() - started
    return result
