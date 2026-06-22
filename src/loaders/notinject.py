"""Normalizer for NotInject benign hard-negative examples."""

import pandas as pd


def normalize_notinject(df: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame()
    result["prompt_id"] = df.index.astype(str)
    result["prompt_text"] = df["prompt"].astype(str)
    result["label"] = 0
    return result
