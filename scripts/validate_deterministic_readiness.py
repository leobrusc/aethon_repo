"""Replay immutable detection fixtures, not a new scientific benchmark."""
import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity_index(frame):
    indexed = frame.set_index(["prompt_id", "prompt_sha256"], drop=False)
    if not indexed.index.is_unique:
        raise ValueError("Duplicate compound historical identity")
    return indexed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--environment", choices=["maintained", "historical"], required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Evidence exists; use a new path")
    os.environ.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    import numpy as np
    import pandas as pd
    from benchmark.detection import _metric_values
    from benchmark.middleware import BenchmarkMiddleware
    from dataset_loader import load_dataset
    fixture_path = ROOT / "tests/fixtures/readiness_deterministic.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    for name, allowed in fixture["artifacts"].items():
        if digest(ROOT / name) not in allowed:
            raise ValueError(f"Untrusted or changed reference artifact: {name}")
    model_path = ROOT / "src/models/aethon_tfidf_lr_revision.pkl"
    source = pd.read_csv(ROOT / "results/revision/detection/per_prompt_results.csv", dtype={"prompt_id": str})
    report = {"status": "FAIL", "environment": args.environment, "purpose": fixture["purpose"],
              "fixture_sha256": digest(fixture_path), "script_sha256": digest(Path(__file__)),
              "python": platform.python_version(), "versions": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scipy", "scikit-learn", "joblib"]},
              "seed": fixture["seed"], "epsilon": fixture["epsilon"], "threshold": fixture["threshold"],
              "score_atol": fixture["score_atol"], "metric_atol": fixture["metric_atol"],
              "comparisons": [], "mismatches": [], "dp": [], "new_llm_inference": False}
    started = time.perf_counter()
    # Only the hash-verified, maintainer-trained versioned model is loaded.
    trusted = BenchmarkMiddleware(str(model_path), fixture["epsilon"], fixture["seed"]).ml_model
    count = 0
    for dataset in source.dataset.unique():
        frame = load_dataset(dataset)
        expected = identity_index(source[(source.dataset == dataset) & (source.condition == "B3")])
        if len(frame) != len(expected) or not expected.index.is_unique:
            raise ValueError("Dataset cardinality or identity changed")
        count += len(frame)
        for row in frame.itertuples(index=False):
            record = expected.loc[(str(row.prompt_id), hashlib.sha256(str(row.prompt_text).encode()).hexdigest()), :]
            if hashlib.sha256(str(row.prompt_text).encode()).hexdigest() != record.prompt_sha256 or int(row.label) != int(record.true_label):
                raise ValueError("Normalization, prompt identity or label changed")
        for condition in ["B0", "B1", "B2", "B3", "B4"]:
            middleware = BenchmarkMiddleware(None, fixture["epsilon"], fixture["seed"])
            middleware.ml_model = trusted
            actual_rows = []
            for row in frame.itertuples(index=False):
                result = middleware.evaluate(str(row.prompt_text), condition)
                fields = asdict(result)
                if any(value < 0 for name, value in fields.items() if name.endswith("latency_ms")):
                    raise ValueError("Negative middleware timing metadata")
                if condition == "B0" and (result.blocked or result.heuristic_flag is not None or result.ml_prediction is not None):
                    raise ValueError("B0 no longer bypasses defenses")
                actual_rows.append({"prompt_id": str(row.prompt_id), "prompt_sha256": hashlib.sha256(str(row.prompt_text).encode()).hexdigest(), "true_label": int(row.label),
                                    "final_prediction": int(result.blocked), "detector_score": result.detection_score,
                                    "ml_score": result.ml_score, "noisy_audit_count": result.noisy_audit_count})
            if condition == "B0":
                report["comparisons"].append({"dataset": dataset, "condition": condition, "rows": len(frame), "bypass_contract": "PASS"})
                continue
            actual = identity_index(pd.DataFrame(actual_rows))
            reference = identity_index(source[(source.dataset == dataset) & (source.condition == condition)]).loc[actual.index]
            decisions = int((actual.final_prediction != reference.final_prediction).sum())
            score_equal = bool(np.allclose(actual.detector_score, reference.detector_score, rtol=0, atol=fixture["score_atol"], equal_nan=True))
            ml_equal = bool(np.allclose(actual.ml_score.astype(float), reference.ml_score.astype(float), rtol=0, atol=fixture["score_atol"], equal_nan=True))
            point, old = _metric_values(actual), _metric_values(reference)
            metrics = {key: {"actual": None if not np.isfinite(point[key]) else point[key],
                              "reference": None if not np.isfinite(old[key]) else old[key],
                              "equal": bool(np.isclose(point[key], old[key], rtol=0, atol=fixture["metric_atol"], equal_nan=True))}
                       for key in ["f1", "fpr", "auroc", "auprc"]}
            comparison = {"dataset": dataset, "condition": condition, "rows": len(actual), "decision_mismatches": decisions,
                          "score_equal": score_equal, "ml_score_equal": ml_equal, "metrics": metrics}
            if condition == "B4":
                comparison["seeded_noise_replay_equal"] = bool(np.allclose(actual.noisy_audit_count, reference.noisy_audit_count, rtol=0, atol=fixture["score_atol"]))
                comparison["noise_replay_scope"] = "Controlled RNG replay only; not an equality requirement for independent stochastic releases"
            if decisions or not score_equal or not ml_equal or not all(v["equal"] for v in metrics.values()):
                report["mismatches"].append({"dataset": dataset, "condition": condition, "kind": "deterministic_reference"})
            report["comparisons"].append(comparison)
    settings = fixture["dp_statistical"]
    for epsilon in settings["epsilons"]:
        values = np.random.default_rng(settings["seed"]).laplace(0, 1 / epsilon, settings["draws"])
        theoretical = 2 / epsilon**2
        mean_ok = abs(float(values.mean())) <= settings["mean_standard_errors"] * np.sqrt(theoretical / len(values))
        variance_ok = abs(float(values.var()) / theoretical - 1) <= settings["variance_relative_tolerance"]
        report["dp"].append({"epsilon": epsilon, "draws": len(values), "seed": settings["seed"],
                             "mean": float(values.mean()), "variance": float(values.var()), "theoretical_variance": theoretical,
                             "status": "PASS" if mean_ok and variance_ok else "FAIL", "scope": "Synthetic noise distribution, not system/text DP proof"})
    report.update(reference_rows=count, duration_seconds=time.perf_counter()-started)
    report["status"] = "PASS" if count == fixture["expected_pairs"] and not report["mismatches"] and all(x["status"] == "PASS" for x in report["dp"]) else "FAIL"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "reference_rows": count, "comparisons": len(report["comparisons"]), "mismatches": report["mismatches"]}))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
