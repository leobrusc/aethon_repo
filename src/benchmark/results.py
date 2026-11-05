"""CSV and manifest persistence for benchmark executions."""

from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple
import csv
import json

import pandas as pd


RESULT_COLUMNS = [
    "run_id",
    "timestamp",
    "model_name",
    "model_version",
    "dataset_name",
    "dataset_source",
    "condition",
    "prompt_id",
    "prompt_text",
    "ground_truth",
    "heuristic_flag",
    "ml_prediction",
    "detection_score",
    "final_decision",
    "response",
    "latency_ms",
    "inference_latency_ms",
    "middleware_latency_ms",
    "heuristic_latency_ms",
    "classifier_latency_ms",
    "decision_latency_ms",
    "audit_latency_ms",
    "preprocessing_latency_ms",
    "asr_judge_latency_ms",
    "runtime_seconds",
    "seed",
    "temperature",
    "host",
    "epsilon",
    "noisy_audit_count",
    "blocked",
    "allowed",
    "asr_eligible",
    "asr_judge",
    "asr_result",
    "attack_success",
    "judge_reason",
    "error",
]


class ResultsStore:
    def __init__(self, output_root: Path):
        self.output_root = output_root
        self.aggregated_dir = output_root / "aggregated"
        self.per_model_dir = output_root / "per_model"
        self.tables_dir = output_root / "tables"
        for directory in (self.output_root, self.aggregated_dir, self.per_model_dir, self.tables_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self.master_csv = self.aggregated_dir / "master_results.csv"
        self.failure_csv = self.aggregated_dir / "failures.csv"
        self.manifest_jsonl = self.aggregated_dir / "benchmark_manifest.jsonl"
        self.progress_json = self.aggregated_dir / "progress.json"

    def completed_keys(self, run_id: str) -> Set[Tuple[str, str, str, str]]:
        if not self.master_csv.exists():
            return set()
        frame = pd.read_csv(self.master_csv, usecols=["run_id", "model_name", "dataset_name", "condition", "prompt_id"])
        frame = frame[frame["run_id"] == run_id]
        return set(zip(frame["model_name"], frame["dataset_name"], frame["condition"], frame["prompt_id"].astype(str)))

    def append_records(self, records: List[Dict[str, object]], model_name: str) -> None:
        if not records:
            return
        self._upgrade_schema(self.master_csv, RESULT_COLUMNS)
        self._upgrade_schema(self.per_model_dir / f"{model_name}.csv", RESULT_COLUMNS)
        self._append_csv(self.master_csv, records, RESULT_COLUMNS)
        self._append_csv(self.per_model_dir / f"{model_name}.csv", records, RESULT_COLUMNS)

    def append_failure(self, failure: Dict[str, object]) -> None:
        columns = ["run_id", "timestamp", "model_name", "dataset_name", "condition", "error"]
        self._append_csv(self.failure_csv, [failure], columns)

    def append_manifest(self, entry: Dict[str, object]) -> None:
        with self.manifest_jsonl.open("a", encoding="utf-8") as manifest:
            manifest.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def write_progress(self, progress: Dict[str, object]) -> None:
        self.progress_json.write_text(json.dumps(progress, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _upgrade_schema(path: Path, columns: List[str]) -> None:
        if not path.exists():
            return
        existing = pd.read_csv(path)
        if list(existing.columns) == columns:
            return
        for column in columns:
            if column not in existing.columns:
                existing[column] = None
        existing[columns].to_csv(path, index=False)

    @staticmethod
    def _append_csv(path: Path, records: Iterable[Dict[str, object]], columns: List[str]) -> None:
        write_header = not path.exists()
        with path.open("a", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
            if write_header:
                writer.writeheader()
            writer.writerows(records)
