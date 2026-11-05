"""CLI for the target-LLM-independent AETHON detection benchmark."""

import argparse
import json

from benchmark.detection import DETECTION_CONDITIONS, EVALUATION_DATASETS, DetectionConfig, run_detection_benchmark


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run detection only; no target LLM is initialized.")
    datasets = parser.add_mutually_exclusive_group(required=False)
    datasets.add_argument("--datasets", nargs="+")
    datasets.add_argument("--all-evaluation-datasets", action="store_true")
    parser.add_argument("--conditions", nargs="+", choices=DETECTION_CONDITIONS, default=list(DETECTION_CONDITIONS))
    parser.add_argument("--ml-model-path")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--random-sample", action="store_true")
    parser.add_argument("--output-root", default="results/revision/detection")
    parser.add_argument("--bootstrap-seed", type=int, default=2026)
    parser.add_argument("--bootstrap-iterations", type=int, default=1000)
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> DetectionConfig:
    selected = list(EVALUATION_DATASETS) if args.all_evaluation_datasets or not args.datasets else args.datasets
    return DetectionConfig(
        datasets=selected, conditions=args.conditions, ml_model_path=args.ml_model_path,
        seed=args.seed, limit=args.limit, random_sample=args.random_sample,
        output_root=args.output_root, bootstrap_seed=args.bootstrap_seed,
        bootstrap_iterations=args.bootstrap_iterations,
    )


def main() -> None:
    result = run_detection_benchmark(build_config(parse_args()))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
