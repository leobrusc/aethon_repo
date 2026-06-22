"""Normalizer for Meta CyberSecEval textual prompt-injection cases."""

import pandas as pd


def normalize_cyberseceval(df: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame()
    result["prompt_id"] = df["prompt_id"].astype(str) if "prompt_id" in df.columns else df.index.astype(str)
    result["prompt_text"] = df["test_case_prompt"].astype(str) + "\n\n" + df["user_input"].astype(str)
    result["label"] = 1
    return result
