import pandas as pd
import json

from benchmark.config import BenchmarkConfig
from benchmark.results import RESULT_COLUMNS, ResultsStore
from benchmark.runner import run_benchmark
from model_registry import LLAMA_BENCHMARK_MODELS, MODEL_REGISTRY, OPEN_BENCHMARK_MODELS, get_model_version, normalize_model_name
from run_benchmark import build_config


def test_prioritized_benchmark_models_are_registered_with_hf_aliases():
    expected = {
        "llama-2-7b-chat": "meta-llama/Llama-2-7b-chat-hf",
        "llama-3.2-1b-instruct": "meta-llama/Llama-3.2-1B-Instruct",
        "llama-3.2-3b-instruct": "meta-llama/Llama-3.2-3B-Instruct",
        "phi-3-mini-4k-instruct": "microsoft/Phi-3-mini-4k-instruct",
        "qwen2.5-3b-instruct": "Qwen/Qwen2.5-3B-Instruct",
        "qwen2.5-7b-instruct": "Qwen/Qwen2.5-7B-Instruct",
    }

    for key, hf_model_id in expected.items():
        assert key in MODEL_REGISTRY
        assert get_model_version(key) == hf_model_id
        assert get_model_version(hf_model_id) == hf_model_id
        assert normalize_model_name(hf_model_id) == key

    assert list(LLAMA_BENCHMARK_MODELS) == [
        "llama-2-7b-chat",
        "llama-3.2-1b-instruct",
        "llama-3.2-3b-instruct",
    ]
    assert list(OPEN_BENCHMARK_MODELS) == [
        "llama-2-7b-chat",
        "llama-3.2-1b-instruct",
        "llama-3.2-3b-instruct",
        "qwen2.5-3b-instruct",
        "qwen2.5-7b-instruct",
        "phi-3-mini-4k-instruct",
    ]


def test_benchmark_full_prioritizes_validated_models():
    with open("configs/benchmark_full.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    assert config["models"] == list(OPEN_BENCHMARK_MODELS)
    assert config["conditions"] == ["B0", "B1", "B2", "B3", "B4"]
    assert config["asr_judge_type"] == "rule"


def _cli_args(**overrides):
    values = {
        "config": None,
        "models": None,
        "all_models": None,
        "llama_only": None,
        "open_models_only": None,
        "datasets": ["notinject"],
        "all_datasets": None,
        "conditions": None,
        "condition_filter": None,
        "seed": None,
        "temperature": None,
        "epsilon": None,
        "max_tokens": None,
        "limit": None,
        "dataset_limit": None,
        "fast_validation": None,
        "random_sample": None,
        "dry_run": None,
        "ml_model_path": None,
        "output_root": None,
        "run_id": None,
        "resume": None,
        "no_tables": None,
        "asr_judge_type": None,
        "asr_judge_model": None,
    }
    values.update(overrides)
    return type("Args", (), values)()


def test_cli_model_selectors_choose_benchmark_groups():
    llama_config = build_config(_cli_args(llama_only=True))
    open_config = build_config(_cli_args(open_models_only=True))

    assert llama_config.models == list(LLAMA_BENCHMARK_MODELS)
    assert open_config.models == list(OPEN_BENCHMARK_MODELS)


def test_cli_rejects_multiple_model_selectors():
    try:
        build_config(_cli_args(models=["qwen2.5-3b-instruct"], open_models_only=True))
    except ValueError as error:
        assert "Choose only one model selector" in str(error)
    else:
        raise AssertionError("Expected conflicting model selectors to fail.")


def test_cli_dataset_limit_condition_filter_and_fast_validation():
    filtered = build_config(
        _cli_args(
            models=["qwen2.5-3b-instruct", "qwen2.5-7b-instruct"],
            datasets=["notinject", "cyberseceval_prompt_injection"],
            dataset_limit=12,
            condition_filter=["B1", "B3"],
        )
    )
    fast = build_config(
        _cli_args(
            models=["qwen2.5-3b-instruct", "qwen2.5-7b-instruct"],
            datasets=["notinject", "cyberseceval_prompt_injection"],
            condition_filter=["B1", "B3"],
            dataset_limit=12,
            fast_validation=True,
        )
    )

    assert filtered.limit == 12
    assert filtered.conditions == ["B1", "B3"]
    assert fast.models == ["qwen2.5-3b-instruct"]
    assert fast.datasets == ["notinject"]
    assert fast.conditions == ["B0"]
    assert fast.limit == 5


def test_dry_run_writes_master_per_model_metrics_and_tables(tmp_path):
    config = BenchmarkConfig(
        models=["gpt-5.4-nano"],
        datasets=["notinject"],
        conditions=["B0", "B1"],
        limit=3,
        dry_run=True,
        output_root=str(tmp_path),
        run_id="pytest_smoke",
    )

    result = run_benchmark(config)
    master = pd.read_csv(tmp_path / "aggregated" / "master_results.csv")

    assert result["rows_written"] == 6
    assert set(master["condition"]) == {"B0", "B1"}
    assert (tmp_path / "per_model" / "gpt-5.4-nano.csv").exists()
    assert (tmp_path / "aggregated" / "metrics_summary_pytest_smoke.csv").exists()
    assert (tmp_path / "tables" / "pytest_smoke" / "ablation_comparison.tex").exists()


def test_progress_json_and_csv_checkpoints_are_written(tmp_path, monkeypatch):
    append_sizes = []
    original_append_records = ResultsStore.append_records

    def spy_append_records(self, records, model_name):
        append_sizes.append(len(records))
        return original_append_records(self, records, model_name)

    monkeypatch.setattr(ResultsStore, "append_records", spy_append_records)
    config = BenchmarkConfig(
        models=["gpt-5.4-nano"],
        datasets=["notinject"],
        conditions=["B0"],
        limit=51,
        dry_run=True,
        output_root=str(tmp_path),
        run_id="checkpoint_test",
        generate_tables=False,
    )

    result = run_benchmark(config)
    master = pd.read_csv(tmp_path / "aggregated" / "master_results.csv")
    with open(tmp_path / "aggregated" / "progress.json", "r", encoding="utf-8") as progress_file:
        progress = json.load(progress_file)

    assert result["rows_written"] == 51
    assert len(master) == 51
    assert append_sizes == [50, 1]
    assert progress["current_model"] == "gpt-5.4-nano"
    assert progress["current_dataset"] == "notinject"
    assert progress["current_condition"] == "B0"
    assert progress["prompt_index"] == 51
    assert progress["processed_prompts"] == 51


def test_resume_does_not_duplicate_completed_rows(tmp_path):
    config = BenchmarkConfig(
        models=["gpt-5.4-nano"],
        datasets=["notinject"],
        conditions=["B0"],
        limit=2,
        dry_run=True,
        output_root=str(tmp_path),
        run_id="resume_test",
    )
    run_benchmark(config)
    config.resume = True
    second_result = run_benchmark(config)
    master = pd.read_csv(tmp_path / "aggregated" / "master_results.csv")

    assert second_result["rows_written"] == 0
    assert len(master) == 2


def test_dry_run_records_unjudged_asr_for_allowed_attack(tmp_path):
    config = BenchmarkConfig(
        models=["gpt-5.4-nano"],
        datasets=["cyberseceval_prompt_injection"],
        conditions=["B0"],
        limit=1,
        dry_run=True,
        output_root=str(tmp_path),
        run_id="asr_dry_run",
    )

    run_benchmark(config)
    master = pd.read_csv(tmp_path / "aggregated" / "master_results.csv")

    assert bool(master.loc[0, "asr_eligible"])
    assert master.loc[0, "asr_result"] == "not_evaluated"
    assert pd.isna(master.loc[0, "attack_success"])


def test_existing_pre_asr_csv_is_upgraded_before_append(tmp_path):
    aggregated = tmp_path / "aggregated"
    aggregated.mkdir(parents=True)
    asr_fields = {"dataset_source", "asr_judge_latency_ms", "asr_eligible", "asr_judge", "asr_result", "attack_success", "judge_reason"}
    old_columns = [column for column in RESULT_COLUMNS if column not in asr_fields]
    old_record = {column: None for column in old_columns}
    old_record.update(
        {
            "run_id": "old",
            "model_name": "gpt-5.4-nano",
            "dataset_name": "notinject",
            "condition": "B0",
            "prompt_id": "0",
            "ground_truth": 0,
            "blocked": False,
            "latency_ms": 0,
            "inference_latency_ms": 0,
            "middleware_latency_ms": 0,
        }
    )
    pd.DataFrame([old_record], columns=old_columns).to_csv(aggregated / "master_results.csv", index=False)
    config = BenchmarkConfig(
        models=["gpt-5.4-nano"],
        datasets=["notinject"],
        conditions=["B0"],
        limit=1,
        dry_run=True,
        output_root=str(tmp_path),
        run_id="new",
    )

    run_benchmark(config)
    master = pd.read_csv(aggregated / "master_results.csv")

    assert "asr_result" in master.columns
    assert len(master) == 2


def test_rule_asr_judge_scores_downstream_response_in_runner(tmp_path, monkeypatch):
    class CompliantTarget:
        def infer(self, prompt, max_tokens, temperature):
            return "Here is how to proceed. Step-by-step instructions:"

    monkeypatch.setattr("benchmark.runner._initialize_model", lambda model, dry_run: (CompliantTarget(), None))
    config = BenchmarkConfig(
        models=["gpt-5.4-nano"],
        datasets=["cyberseceval_prompt_injection"],
        conditions=["B0"],
        limit=1,
        dry_run=False,
        output_root=str(tmp_path),
        run_id="asr_compliance",
        asr_judge_type="rule",
    )

    run_benchmark(config)
    master = pd.read_csv(tmp_path / "aggregated" / "master_results.csv")
    metrics = pd.read_csv(tmp_path / "aggregated" / "metrics_summary_asr_compliance.csv")

    assert master.loc[0, "asr_result"] == "succeeded"
    assert bool(master.loc[0, "attack_success"])
    assert metrics.loc[0, "asr"] == 1.0
    assert metrics.loc[0, "residual_asr"] == 1.0


def test_unavailable_model_is_preflight_skipped_without_result_rows(tmp_path, monkeypatch):
    def unavailable(model, dry_run):
        return None, "model weights are not available in the current environment"

    monkeypatch.setattr("benchmark.runner._initialize_model", unavailable)
    config = BenchmarkConfig(
        models=["microsoft/Phi-3-mini-4k-instruct"],
        datasets=["notinject"],
        conditions=["B0", "B1"],
        limit=1,
        dry_run=False,
        output_root=str(tmp_path),
        run_id="skip_unavailable",
    )

    result = run_benchmark(config)
    failures = pd.read_csv(tmp_path / "aggregated" / "failures.csv")

    assert result["rows_written"] == 0
    assert result["failures"] == 2
    assert not (tmp_path / "aggregated" / "master_results.csv").exists()
    assert set(failures["model_name"]) == {"phi-3-mini-4k-instruct"}
    assert set(failures["condition"]) == {"B0", "B1"}


def test_api_model_without_credentials_is_skipped_before_execution(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = BenchmarkConfig(
        models=["gpt-5.4-nano"],
        datasets=["notinject"],
        conditions=["B0"],
        limit=1,
        dry_run=False,
        output_root=str(tmp_path),
        run_id="skip_missing_api_key",
    )

    result = run_benchmark(config)
    failures = pd.read_csv(tmp_path / "aggregated" / "failures.csv")

    assert result["rows_written"] == 0
    assert result["failures"] == 1
    assert failures.loc[0, "model_name"] == "gpt-5.4-nano"
    assert "OPENAI_API_KEY" in failures.loc[0, "error"]
