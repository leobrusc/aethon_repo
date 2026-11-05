from pathlib import Path

import pandas as pd

from benchmark.asr import LLMASRJudge, RuleBasedASRJudge, is_asr_eligible
from benchmark.metrics import compute_metrics


def test_asr_is_limited_to_supported_adversarial_sources():
    assert is_asr_eligible("jailbreakbench_behaviors", "jailbreakbench_behaviors", 1)
    assert is_asr_eligible("all", "red_team_attempts", 1)
    assert not is_asr_eligible("notinject", "notinject", 0)
    assert not is_asr_eligible("prompt_injection_core", "prompt_injection_core", 1)


def test_rule_judge_marks_blocked_attack_as_prevented():
    result = RuleBasedASRJudge().judge(
        "request",
        "[BLOCKED_BY_AETHON]",
        True,
        "cyberseceval_prompt_injection",
        "cyberseceval_prompt_injection",
        1,
    )

    assert result.asr_result == "prevented"
    assert result.attack_success is False


def test_rule_judge_detects_refusal_and_clear_compliance():
    judge = RuleBasedASRJudge()
    refusal = judge.judge(
        "request",
        "I can't assist with that request.",
        False,
        "jailbreakbench_behaviors",
        "jailbreakbench_behaviors",
        1,
    )
    compliance = judge.judge(
        "request",
        "Here is how to proceed. Step-by-step instructions:",
        False,
        "jailbreakbench_behaviors",
        "jailbreakbench_behaviors",
        1,
    )

    assert refusal.attack_success is False
    assert compliance.attack_success is True


def test_llm_judge_accepts_structured_json(monkeypatch):
    class StubDriver:
        response_contract = "continuation-v1"
        def infer(self, prompt, max_tokens, temperature):
            return '{"attack_success": false, "judge_reason": "Target refused."}'

    monkeypatch.setattr("benchmark.asr.get_model_driver", lambda model: StubDriver())
    result = LLMASRJudge("stub").judge(
        "request",
        "response",
        False,
        "red_team_attempts",
        "red_team_attempts",
        1,
    )

    assert result.asr_result == "failed"
    assert result.attack_success is False


def test_metrics_export_asr_rates(tmp_path: Path):
    master = tmp_path / "master.csv"
    pd.DataFrame(
        [
            {
                "model_name": "model",
                "dataset_name": "jailbreakbench_behaviors",
                "condition": "B3",
                "ground_truth": 1,
                "blocked": True,
                "detection_score": 1,
                "latency_ms": 1,
                "inference_latency_ms": 0,
                "middleware_latency_ms": 1,
                "asr_eligible": True,
                "attack_success": False,
            },
            {
                "model_name": "model",
                "dataset_name": "jailbreakbench_behaviors",
                "condition": "B3",
                "ground_truth": 1,
                "blocked": False,
                "detection_score": 0,
                "latency_ms": 2,
                "inference_latency_ms": 1,
                "middleware_latency_ms": 1,
                "asr_eligible": True,
                "attack_success": True,
            },
        ]
    ).to_csv(master, index=False)

    metrics = compute_metrics(master, tmp_path)
    row = metrics.iloc[0]

    assert row["asr"] == 0.5
    assert row["blocked_asr"] == 0.0
    assert row["residual_asr"] == 1.0
    assert row["defense_success_rate"] == 0.5
    assert row["asr_evaluation_coverage"] == 1.0


def test_metrics_preserve_missing_asr_judgments_and_export_diagnostics(tmp_path: Path):
    master = tmp_path / "master.csv"
    pd.DataFrame(
        [
            {
                "model_name": "model",
                "dataset_name": "jailbreakbench_behaviors",
                "condition": "B0",
                "ground_truth": 1,
                "blocked": False,
                "detection_score": 0.2,
                "latency_ms": 1,
                "inference_latency_ms": 0,
                "middleware_latency_ms": 1,
                "asr_eligible": True,
                "attack_success": None,
            },
            {
                "model_name": "model",
                "dataset_name": "jailbreakbench_behaviors",
                "condition": "B0",
                "ground_truth": 0,
                "blocked": False,
                "detection_score": 0.1,
                "latency_ms": 1,
                "inference_latency_ms": 0,
                "middleware_latency_ms": 1,
                "asr_eligible": False,
                "attack_success": None,
            },
        ]
    ).to_csv(master, index=False)

    metrics = compute_metrics(master, tmp_path, run_id=None)
    diagnostics = pd.read_csv(tmp_path / "diagnostics.csv")
    row = metrics.iloc[0]

    assert row["auroc"] == 1.0
    assert bool(row["auroc_computable"])
    assert row["asr_eligible_prompts"] == 1
    assert row["asr_evaluated_prompts"] == 0
    assert pd.isna(row["asr"])
    assert not bool(diagnostics.loc[0, "asr_computable"])
    assert bool(diagnostics.loc[0, "auroc_computable"])
    assert (tmp_path / "benchmark_readiness_report.md").exists()


def test_metrics_warn_when_auroc_is_undefined_for_one_class(tmp_path: Path):
    master = tmp_path / "master.csv"
    pd.DataFrame(
        [
            {
                "model_name": "model",
                "dataset_name": "notinject",
                "condition": "B1",
                "ground_truth": 0,
                "blocked": False,
                "detection_score": 0.0,
                "latency_ms": 1,
                "inference_latency_ms": 0,
                "middleware_latency_ms": 1,
                "asr_eligible": False,
                "attack_success": None,
            },
            {
                "model_name": "model",
                "dataset_name": "notinject",
                "condition": "B1",
                "ground_truth": 0,
                "blocked": True,
                "detection_score": 1.0,
                "latency_ms": 1,
                "inference_latency_ms": 0,
                "middleware_latency_ms": 1,
                "asr_eligible": False,
                "attack_success": None,
            },
        ]
    ).to_csv(master, index=False)

    metrics = compute_metrics(master, tmp_path, run_id="one_class")
    diagnostics = pd.read_csv(tmp_path / "diagnostics_one_class.csv")
    report = (tmp_path / "benchmark_readiness_report_one_class.md").read_text(encoding="utf-8")
    canonical_report = (tmp_path / "benchmark_readiness_report.md").read_text(encoding="utf-8")
    row = metrics.iloc[0]

    assert pd.isna(row["auroc"])
    assert not bool(row["auroc_computable"])
    assert "sample size < 20" in row["metric_warnings"]
    assert "only one class present" in row["metric_warnings"]
    assert "AUROC undefined" in row["metric_warnings"]
    assert diagnostics.loc[0, "positive_labels"] == 0
    assert diagnostics.loc[0, "negative_labels"] == 2
    assert not bool(diagnostics.loc[0, "auroc_computable"])
    assert "Ready for publication-level claims: no" in report
    assert "Ready for publication-level claims: no" in canonical_report
