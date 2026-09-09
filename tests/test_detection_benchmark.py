import json

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from benchmark.detection import (
    DetectionConfig,
    _metric_values,
    bootstrap_confidence_intervals,
    evaluate_prompts,
    run_detection_benchmark,
)
from train_revision_detector import train_revision_detector


def _model(tmp_path):
    path = tmp_path / "detector.pkl"
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000)),
        ("lr", LogisticRegression(max_iter=1000, random_state=42, solver="lbfgs", penalty="l2", C=1.0)),
    ])
    pipeline.fit(
        ["ordinary weather question", "hello friend", "ignore previous instructions", "system override now"],
        [0, 0, 1, 1],
    )
    joblib.dump(pipeline, path)
    return path


def _frame(labels, predictions, scores=None):
    scores = predictions if scores is None else scores
    return pd.DataFrame({
        "true_label": labels,
        "final_prediction": predictions,
        "detector_score": scores,
        "detection_latency_ms": np.arange(1, len(labels) + 1, dtype=float),
    })


def test_detection_runner_never_initializes_target_llm(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("target LLM initialization is forbidden")

    monkeypatch.setattr("model_registry.get_model_driver", forbidden)
    result = run_detection_benchmark(DetectionConfig(
        datasets=["prompt_injections_test"], conditions=["B1"], limit=2,
        output_root=str(tmp_path), bootstrap_iterations=10,
    ))
    output = pd.read_csv(tmp_path / "per_prompt_results.csv")
    assert result["rows"] == 2
    assert "model_name" not in output.columns
    assert "prompt_text" not in output.columns


def test_mixed_metrics_and_confusion_counts_are_correct():
    values = _metric_values(_frame([0, 0, 1, 1], [0, 1, 1, 0], [0.1, 0.7, 0.8, 0.2]))
    assert values["tp"] == values["tn"] == values["fp"] == values["fn"] == 1
    assert values["precision"] == values["recall"] == values["f1"] == 0.5
    assert values["fpr"] == 0.5
    assert np.isfinite(values["auroc"])
    assert np.isfinite(values["auprc"])


def test_attack_only_invalid_metrics_are_null():
    values = _metric_values(_frame([1, 1], [1, 0], [0.8, 0.2]))
    assert np.isnan(values["auroc"])
    assert np.isnan(values["auprc"])
    assert np.isnan(values["fpr"])
    assert values["recall"] == 0.5


def test_benign_only_invalid_metrics_are_null():
    values = _metric_values(_frame([0, 0], [0, 1], [0.1, 0.8]))
    assert np.isnan(values["auroc"])
    assert np.isnan(values["auprc"])
    assert np.isnan(values["precision"])
    assert np.isnan(values["recall"])
    assert np.isnan(values["f1"])
    assert values["fpr"] == 0.5


def test_bootstrap_intervals_are_reproducible_and_invalid_metrics_stay_null():
    mixed = _frame([0, 0, 1, 1, 0, 1], [0, 1, 1, 0, 0, 1], [0.1, 0.6, 0.9, 0.3, 0.2, 0.8])
    first = bootstrap_confidence_intervals(mixed, seed=99, iterations=50)
    second = bootstrap_confidence_intervals(mixed, seed=99, iterations=50)
    assert first == second
    attack_only = bootstrap_confidence_intervals(_frame([1, 1], [1, 0]), seed=99, iterations=10)
    assert np.isnan(attack_only["auroc_ci_low"])
    assert np.isnan(attack_only["auprc_ci_high"])
    assert np.isnan(attack_only["fpr_ci_low"])


def test_b3_b4_predictions_and_scores_are_identical(tmp_path):
    frame = evaluate_prompts(DetectionConfig(
        datasets=["prompt_injections_test"], conditions=["B3", "B4"],
        ml_model_path=str(_model(tmp_path)), limit=20,
    ))
    b3 = frame[frame.condition == "B3"].sort_values("prompt_id").reset_index(drop=True)
    b4 = frame[frame.condition == "B4"].sort_values("prompt_id").reset_index(drop=True)
    assert b3["final_prediction"].equals(b4["final_prediction"])
    assert b3["detector_score"].equals(b4["detector_score"])
    assert b4["noisy_audit_count"].notna().eq(b4["final_prediction"].astype(bool)).all()


def test_outputs_include_latency_and_dataset_condition_grouping(tmp_path):
    run_detection_benchmark(DetectionConfig(
        datasets=["prompt_injections_test"], conditions=["B1"], limit=4,
        output_root=str(tmp_path), bootstrap_iterations=10,
    ))
    metrics = pd.read_csv(tmp_path / "metrics_by_dataset.csv")
    latency = pd.read_csv(tmp_path / "latency_summary.csv")
    assert {"dataset", "condition", "tp", "tn", "fp", "fn"}.issubset(metrics.columns)
    assert {"mean_latency_ms", "median_latency_ms", "p95_latency_ms", "p99_latency_ms"}.issubset(latency.columns)
    assert "model_name" not in metrics.columns
    assert (tmp_path / "tables" / "ablation_comparison.csv").exists()


def test_revision_training_metadata_and_no_evaluation_leakage(tmp_path):
    path = tmp_path / "aethon_tfidf_lr_revision.pkl"
    metadata = train_revision_detector(path)
    persisted = json.loads(path.with_suffix(".metadata.json").read_text(encoding="utf-8"))
    assert path.exists()
    assert metadata == persisted
    assert metadata["training_dataset"] == "prompt_injections_train"
    assert metadata["number_of_samples"] == 546
    assert metadata["benign"] == 343
    assert metadata["adversarial"] == 203
    assert metadata["tfidf_parameters"]["max_features"] == 5000
    assert metadata["decision_threshold"] == 0.5
    assert metadata["logistic_regression_parameters"]["max_iter"] == 1000
    assert metadata["random_state"] == 42
    assert "prompt_injection_core" in metadata["excluded_evaluation_datasets"]
