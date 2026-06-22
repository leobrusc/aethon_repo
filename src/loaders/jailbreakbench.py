"""Normalizer for JailbreakBench JBB-Behaviors."""

import pandas as pd


def normalize_jailbreakbench(df: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame()
    result["prompt_id"] = df["Index"].astype(str) if "Index" in df.columns else df.index.astype(str)
    result["prompt_text"] = df["Goal"].astype(str)
    split = df["split"].astype(str).str.lower()
    result["label"] = split.map({"benign": 0, "harmful": 1}).fillna(1).astype(int)
    return result
