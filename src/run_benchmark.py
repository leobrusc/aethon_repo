"""Command-line entry point for publication-oriented AETHON benchmarks."""

import argparse
import json
import logging

from benchmark.config import ASR_JUDGE_TYPES, BenchmarkConfig, CONDITIONS
from benchmark.runner import run_benchmark
from dataset_loader import ALL_DATASETS
from model_registry import LLAMA_BENCHMARK_MODELS, MODEL_REGISTRY, OPEN_BENCHMARK_MODELS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AETHON reproducible benchmark pipeline.")
    parser.add_argument("--config", type=str, help="JSON benchmark configuration file.")
    parser.add_argument("--models", nargs="+", help="Model registry keys to evaluate.")
    parser.add_argument("--all-models", action="store_true", default=None, help="Evaluate all registered models.")
    parser.add_argument("--llama-only", action="store_true", default=None, help="Evaluate only the validated Meta Llama benchmark models.")
    parser.add_argument("--open-models-only", action="store_true", default=None, help="Evaluate only the prioritized non-API benchmark models.")
    parser.add_argument("--datasets", nargs="+", help="Dataset aliases to evaluate.")
    parser.add_argument("--all-datasets", action="store_true", default=None, help="Evaluate all canonical datasets.")
    parser.add_argument("--conditions", nargs="+", choices=CONDITIONS, help="Ablation conditions.")
    parser.add_argument("--condition-filter", nargs="+", choices=CONDITIONS, help="Alias for selecting a subset of ablation conditions.")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--epsilon", type=float)
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--limit", type=int, help="Optional deterministic sample size; omitted means full dataset.")
    parser.add_argument("--dataset-limit", type=int, help="Limit rows loaded per dataset.")
    parser.add_argument("--fast-validation", action="store_true", default=None, help="Run first model, first dataset, B0 only, limit 5.")
    parser.add_argument("--random-sample", action="store_true", default=None)
    parser.add_argument("--dry-run", action="store_true", default=None)
    parser.add_argument("--ml-model-path", type=str)
    parser.add_argument("--output-root", type=str)
    parser.add_argument("--run-id", type=str, help="Explicit run id, required to resume an earlier run.")
    parser.add_argument("--resume", action="store_true", default=None)
    parser.add_argument("--no-tables", action="store_true", default=None)
    parser.add_argument("--asr-judge-type", choices=ASR_JUDGE_TYPES, help="ASR judging protocol.")
    parser.add_argument("--asr-judge-model", type=str, help="Registered model key for optional LLM judging.")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> BenchmarkConfig:
    model_selector_count = sum(bool(value) for value in (args.models, args.all_models, args.llama_only, args.open_models_only))
    if model_selector_count > 1:
        raise ValueError("Choose only one model selector: --models, --all-models, --llama-only, or --open-models-only.")
    if args.limit is not None and args.dataset_limit is not None:
        raise ValueError("Choose only one row limit option: --limit or --dataset-limit.")
    if args.conditions is not None and args.condition_filter is not None:
        raise ValueError("Choose only one condition selector: --conditions or --condition-filter.")

    if args.config:
        config = BenchmarkConfig.from_json(args.config)
    else:
        config = BenchmarkConfig(models=args.models or [], datasets=args.datasets or [])

    selected_models = args.models
    if args.all_models:
        selected_models = list(MODEL_REGISTRY.keys())
    elif args.llama_only:
        selected_models = list(LLAMA_BENCHMARK_MODELS)
    elif args.open_models_only:
        selected_models = list(OPEN_BENCHMARK_MODELS)

    selected_conditions = args.condition_filter if args.condition_filter is not None else args.conditions
    selected_limit = args.dataset_limit if args.dataset_limit is not None else args.limit

    overrides = {
        "models": selected_models,
        "datasets": list(ALL_DATASETS) if args.all_datasets else args.datasets,
        "conditions": selected_conditions,
        "seed": args.seed,
        "temperature": args.temperature,
        "epsilon": args.epsilon,
        "max_tokens": args.max_tokens,
        "limit": selected_limit,
        "random_sample": args.random_sample,
        "dry_run": args.dry_run,
        "ml_model_path": args.ml_model_path,
        "output_root": args.output_root,
        "run_id": args.run_id,
        "resume": args.resume,
        "generate_tables": False if args.no_tables else None,
        "asr_judge_type": args.asr_judge_type,
        "asr_judge_model": args.asr_judge_model,
    }
    config = config.update(overrides)
    if args.fast_validation:
        config = config.update(
            {
                "models": config.models[:1],
                "datasets": config.datasets[:1],
                "conditions": ["B0"],
                "limit": 5,
            }
        )
    return config


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = run_benchmark(build_config(parse_args()))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
