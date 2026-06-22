"""Publication-oriented table exporters for AETHON benchmark summaries."""

from pathlib import Path
from typing import Dict

import pandas as pd


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "No data available.\n"
    display = frame.copy()
    for column in display.select_dtypes(include="float").columns:
        display[column] = display[column].map(lambda value: "" if pd.isna(value) else f"{value:.4f}")
    header = "| " + " | ".join(display.columns) + " |\n"
    divider = "| " + " | ".join("---" for _ in display.columns) + " |\n"
    rows = "".join("| " + " | ".join(str(value) for value in row) + " |\n" for row in display.itertuples(index=False, name=None))
    return header + divider + rows


def export_tables(metrics: pd.DataFrame, output_dir: Path) -> Dict[str, Path]:
    if metrics.empty:
        return {}
    output_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "auroc_per_model": metrics[["model_name", "dataset_name", "condition", "auroc", "f1_score"]],
        "fpr_comparison": metrics[["model_name", "dataset_name", "condition", "false_positive_rate", "false_negative_rate"]],
        "latency_comparison": metrics[["model_name", "dataset_name", "condition", "mean_latency_ms", "p95_latency_ms", "p99_latency_ms"]],
        "ablation_comparison": metrics[["model_name", "dataset_name", "condition", "accuracy", "precision", "recall", "f1_score", "mitigation_ratio"]],
        "asr_comparison": metrics[
            [
                "model_name",
                "dataset_name",
                "condition",
                "asr_eligible_prompts",
                "asr_evaluated_prompts",
                "asr_evaluation_coverage",
                "asr",
                "blocked_asr",
                "residual_asr",
                "defense_success_rate",
            ]
        ],
        "dataset_comparison": metrics.groupby(["dataset_name", "condition"], as_index=False)[
            [
                "auroc",
                "false_positive_rate",
                "false_negative_rate",
                "mean_latency_ms",
                "mitigation_ratio",
                "asr",
                "residual_asr",
                "defense_success_rate",
            ]
        ].mean(),
    }
    paths = {}
    for name, frame in tables.items():
        csv_path = output_dir / f"{name}.csv"
        md_path = output_dir / f"{name}.md"
        tex_path = output_dir / f"{name}.tex"
        frame.to_csv(csv_path, index=False)
        md_path.write_text(_markdown_table(frame), encoding="utf-8")
        tex_path.write_text(frame.to_latex(index=False, float_format="%.4f"), encoding="utf-8")
        paths[name] = csv_path
    return paths
