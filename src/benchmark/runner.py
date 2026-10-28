"""End-to-end benchmark execution orchestration."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
import gc
import hashlib
import json
import logging
import os
import random
import time

import numpy as np
import pandas as pd

from benchmark.config import BenchmarkConfig
from benchmark.asr import ASRJudgment, build_asr_judge, is_asr_eligible
from benchmark.metadata import environment_metadata
from benchmark.metrics import compute_metrics
from benchmark.middleware import BenchmarkMiddleware, MissingClassifierError
from benchmark.results import ResultsStore
from benchmark.tables import export_tables
from dataset_loader import get_dataset_metadata, load_dataset
from model_registry import get_model_availability_error, get_model_driver, get_model_version, normalize_model_name


LOGGER = logging.getLogger("aethon.benchmark")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _new_run_id(config: BenchmarkConfig) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(json.dumps(config.to_dict(), sort_keys=True).encode("utf-8")).hexdigest()[:8]
    return f"aethon_{timestamp}_{digest}"


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def _prepare_dataset(name: str, config: BenchmarkConfig) -> pd.DataFrame:
    frame = load_dataset(name)
    if config.limit is None or config.limit >= len(frame):
        return frame
    if config.random_sample:
        return frame.sample(n=config.limit, random_state=config.seed).sort_index().reset_index(drop=True)
    return frame.head(config.limit).copy()


def _initialize_model(model_name: str, dry_run: bool):
    if dry_run:
        return None, None
    availability_error = get_model_availability_error(model_name, dry_run=dry_run)
    if availability_error:
        return None, availability_error
    try:
        driver = get_model_driver(model_name)
        if hasattr(driver, "gen") and driver.gen is None:
            return None, "model weights are not available in the current environment"
        return driver, None
    except Exception as error:
        return None, str(error)


def _deduplicate_models(models):
    normalized = []
    seen = set()
    for model_name in models:
        key = normalize_model_name(model_name)
        if key in seen:
            continue
        normalized.append(key)
        seen.add(key)
    return normalized


def _preflight_models(models, dry_run: bool):
    available = set()
    unavailable = {}
    for model_name in models:
        driver, model_error = _initialize_model(model_name, dry_run)
        if model_error:
            unavailable[model_name] = model_error
            continue
        available.add(model_name)
        del driver
        gc.collect()
    return available, unavailable


def _is_error_response(response: str) -> bool:
    prefixes = ("[OPENAI_ERROR]", "[DEEPSEEK_ERROR]", "[MODEL_NOT_LOADED]", "[INFER_ERROR]")
    return response.startswith(prefixes)


def _failure(run_id: str, model: str, dataset: str, condition: str, error: str) -> Dict[str, object]:
    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_name": model,
        "dataset_name": dataset,
        "condition": condition,
        "error": error,
    }


def _format_eta(seconds: Optional[float]) -> str:
    if seconds is None:
        return "unknown"
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _estimate_eta(started_at: float, processed_prompts: int, total_prompts: int) -> Optional[float]:
    if processed_prompts <= 0:
        return None
    elapsed = time.perf_counter() - started_at
    remaining = max(0, total_prompts - processed_prompts)
    return (elapsed / processed_prompts) * remaining


def _print_progress(model_name: str, dataset_name: str, condition: str, prompt_index: int, prompt_total: int, eta: str) -> None:
    print(f"[MODEL] {model_name}", flush=True)
    print(f"[DATASET] {dataset_name}", flush=True)
    print(f"[CONDITION] {condition}", flush=True)
    print(f"[PROMPT] {prompt_index}/{prompt_total}", flush=True)
    print(f"[ETA] {eta}", flush=True)


def _progress_payload(
    run_id: str,
    models,
    model_name: Optional[str],
    dataset_name: Optional[str],
    condition: Optional[str],
    prompt_index: int,
    prompt_total: int,
    processed_prompts: int,
    total_prompts: int,
    eta: str,
) -> Dict[str, object]:
    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "active_models": list(models),
        "current_model": model_name,
        "current_dataset": dataset_name,
        "current_condition": condition,
        "prompt_index": prompt_index,
        "prompt_total": prompt_total,
        "processed_prompts": processed_prompts,
        "total_prompts": total_prompts,
        "eta": eta,
    }


def _write_progress(
    store: ResultsStore,
    run_id: str,
    models,
    model_name: Optional[str],
    dataset_name: Optional[str],
    condition: Optional[str],
    prompt_index: int,
    prompt_total: int,
    processed_prompts: int,
    total_prompts: int,
    eta: str,
) -> None:
    store.write_progress(
        _progress_payload(
            run_id,
            models,
            model_name,
            dataset_name,
            condition,
            prompt_index,
            prompt_total,
            processed_prompts,
            total_prompts,
            eta,
        )
    )


def _flush_records(records, store: ResultsStore, model_name: str, runtime_seconds: float) -> int:
    if not records:
        return 0
    for record in records:
        record["runtime_seconds"] = runtime_seconds
    written = len(records)
    store.append_records(records, model_name)
    records.clear()
    return written


def run_benchmark(config: BenchmarkConfig) -> dict:
    config.validate()
    _set_seed(config.seed)
    run_id = config.run_id or _new_run_id(config)
    output_root = PROJECT_ROOT / config.output_root if not Path(config.output_root).is_absolute() else Path(config.output_root)
    store = ResultsStore(output_root)
    completed = store.completed_keys(run_id) if config.resume else set()
    environment = environment_metadata(PROJECT_ROOT)
    models = _deduplicate_models(config.models)
    available_models, unavailable_models = _preflight_models(models, config.dry_run)
    datasets = {name: _prepare_dataset(name, config) for name in config.datasets}
    dataset_metadata = {name: get_dataset_metadata(name) for name in config.datasets}
    active_models = [model_name for model_name in models if model_name in available_models]
    total_prompt_work = sum(len(frame) for frame in datasets.values()) * len(config.conditions) * len(active_models)
    processed_prompts = 0
    benchmark_start = time.perf_counter()
    last_progress_write = 0.0
    print(f"[MODELS] {', '.join(active_models) if active_models else 'none'}", flush=True)
    _write_progress(store, run_id, active_models, None, None, None, 0, 0, 0, total_prompt_work, "unknown")
    judge_error = None
    try:
        asr_judge = build_asr_judge(config.asr_judge_type, config.asr_judge_model)
    except Exception as error:
        asr_judge = None
        judge_error = str(error)
        LOGGER.warning("ASR judge unavailable: %s", judge_error)
    total_written = 0
    total_failures = 0

    for model_name in models:
        if model_name in unavailable_models:
            model_error = unavailable_models[model_name]
            LOGGER.warning("Skipping unavailable model %s before benchmark execution: %s", model_name, model_error)
            for dataset_name in config.datasets:
                for condition in config.conditions:
                    store.append_failure(_failure(run_id, model_name, dataset_name, condition, model_error))
                    total_failures += 1
            continue
        driver, model_error = _initialize_model(model_name, config.dry_run)
        if model_error:
            LOGGER.warning("Skipping unavailable model %s after preflight: %s", model_name, model_error)
            for dataset_name in config.datasets:
                for condition in config.conditions:
                    store.append_failure(_failure(run_id, model_name, dataset_name, condition, model_error))
                    total_failures += 1
            continue

        for dataset_name, frame in datasets.items():
            for condition in config.conditions:
                combination_start = time.perf_counter()
                try:
                    middleware = BenchmarkMiddleware(config.ml_model_path, config.epsilon, config.seed)
                    if condition in {"B2", "B3", "B4"} and middleware.ml_model is None:
                        raise MissingClassifierError("B2, B3 and B4 require --ml-model-path.")
                except (MissingClassifierError, FileNotFoundError) as error:
                    store.append_failure(_failure(run_id, model_name, dataset_name, condition, str(error)))
                    total_failures += 1
                    processed_prompts += int(len(frame))
                    continue

                records = []
                condition_written = 0
                prompt_total = int(len(frame))
                for prompt_index, (_, source_row) in enumerate(frame.iterrows(), start=1):
                    eta = _format_eta(_estimate_eta(benchmark_start, processed_prompts, total_prompt_work))
                    _print_progress(model_name, dataset_name, condition, prompt_index, prompt_total, eta)
                    now = time.perf_counter()
                    if now - last_progress_write >= 30:
                        _write_progress(
                            store,
                            run_id,
                            active_models,
                            model_name,
                            dataset_name,
                            condition,
                            prompt_index,
                            prompt_total,
                            processed_prompts,
                            total_prompt_work,
                            eta,
                        )
                        last_progress_write = now
                    prompt_id = str(source_row["prompt_id"])
                    completion_key = (model_name, dataset_name, condition, prompt_id)

                    preprocess_started = time.perf_counter()
                    prompt = str(source_row["prompt_text"])
                    ground_truth = int(source_row["label"])
                    source_name = str(source_row["source"])
                    preprocessing_latency = (time.perf_counter() - preprocess_started) * 1000

                    decision = middleware.evaluate(prompt, condition)
                    if completion_key in completed:
                        processed_prompts += 1
                        continue

                    inference_latency = 0.0
                    error_text = ""
                    if decision.blocked:
                        response = "[BLOCKED_BY_AETHON]"
                    elif config.dry_run:
                        response = "[DRY_RUN_ALLOWED]"
                    else:
                        inference_started = time.perf_counter()
                        try:
                            response = driver.infer(prompt, max_tokens=config.max_tokens, temperature=config.temperature)
                        except Exception as error:
                            response = f"[INFER_ERROR] {error}"
                        inference_latency = (time.perf_counter() - inference_started) * 1000
                        if _is_error_response(str(response)):
                            error_text = str(response)

                    judge_started = time.perf_counter()
                    if asr_judge is None:
                        eligible = is_asr_eligible(dataset_name, source_name, ground_truth)
                        asr = ASRJudgment(
                            "not_evaluated" if eligible else "not_applicable",
                            None,
                            judge_error or "ASR judging is disabled for this run.",
                            config.asr_judge_type,
                            eligible,
                        )
                    else:
                        asr = asr_judge.judge(
                            prompt=prompt,
                            response=str(response),
                            blocked=decision.blocked,
                            dataset_name=dataset_name,
                            source=source_name,
                            ground_truth=ground_truth,
                        )
                    asr_judge_latency = (time.perf_counter() - judge_started) * 1000

                    total_latency = preprocessing_latency + decision.latency_ms + inference_latency
                    records.append(
                        {
                            "run_id": run_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "model_name": model_name,
                            "model_version": get_model_version(model_name),
                            "dataset_name": dataset_name,
                            "dataset_source": source_name,
                            "condition": condition,
                            "prompt_id": prompt_id,
                            "prompt_text": prompt,
                            "ground_truth": ground_truth,
                            "heuristic_flag": decision.heuristic_flag,
                            "ml_prediction": decision.ml_prediction,
                            "detection_score": decision.detection_score,
                            "final_decision": decision.final_decision,
                            "response": response,
                            "latency_ms": total_latency,
                            "inference_latency_ms": inference_latency,
                            "middleware_latency_ms": decision.latency_ms,
                            "heuristic_latency_ms": decision.heuristic_latency_ms,
                            "classifier_latency_ms": decision.classifier_latency_ms,
                            "decision_latency_ms": decision.decision_latency_ms,
                            "audit_latency_ms": decision.audit_latency_ms,
                            "preprocessing_latency_ms": preprocessing_latency,
                            "asr_judge_latency_ms": asr_judge_latency,
                            "runtime_seconds": None,
                            "seed": config.seed,
                            "temperature": config.temperature,
                            "host": environment["host"],
                            "epsilon": config.epsilon if condition == "B4" else None,
                            "noisy_audit_count": decision.noisy_audit_count,
                            "blocked": decision.blocked,
                            "allowed": not decision.blocked,
                            "asr_eligible": asr.eligible,
                            "asr_judge": asr.judge_type,
                            "asr_result": asr.asr_result,
                            "attack_success": asr.attack_success,
                            "judge_reason": asr.judge_reason,
                            "error": error_text,
                        }
                    )
                    processed_prompts += 1

                    if prompt_index % 50 == 0:
                        runtime_so_far = time.perf_counter() - combination_start
                        written = _flush_records(records, store, model_name, runtime_so_far)
                        condition_written += written
                        total_written += written

                runtime_seconds = time.perf_counter() - combination_start
                written = _flush_records(records, store, model_name, runtime_seconds)
                condition_written += written
                total_written += written
                final_eta = _format_eta(_estimate_eta(benchmark_start, processed_prompts, total_prompt_work))
                _write_progress(
                    store,
                    run_id,
                    active_models,
                    model_name,
                    dataset_name,
                    condition,
                    prompt_total,
                    prompt_total,
                    processed_prompts,
                    total_prompt_work,
                    final_eta,
                )
                last_progress_write = time.perf_counter()
                store.append_manifest(
                    {
                        "run_id": run_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "model_name": model_name,
                        "model_version": get_model_version(model_name),
                        "dataset_name": dataset_name,
                        "dataset_metadata": dataset_metadata[dataset_name],
                        "condition": condition,
                        "n_source_samples": int(len(frame)),
                        "n_written_samples": condition_written,
                        "runtime_seconds": runtime_seconds,
                        "config": config.to_dict(),
                        "environment": environment,
                    }
                )

    metrics = pd.DataFrame()
    if store.master_csv.exists():
        metrics = compute_metrics(store.master_csv, store.aggregated_dir, run_id=run_id)
        if config.generate_tables:
            export_tables(metrics, store.tables_dir / run_id)

    return {
        "run_id": run_id,
        "rows_written": total_written,
        "failures": total_failures,
        "master_csv": str(store.master_csv),
        "metrics_rows": int(len(metrics)),
    }
