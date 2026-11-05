"""Paired scientific comparisons of unique detector predictions, without text."""
import argparse
import json
from pathlib import Path
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, recall_score
from analysis_utils import mcnemar_test, paired_bootstrap_difference
from baseline_reliability import atomic_write

KEYS = ["dataset", "prompt_id", "prompt_sha256"]


def align(first, second):
    required = set(KEYS + ["true_label", "prediction"])
    if not required <= set(first) or not required <= set(second):
        raise ValueError("Expected dataset, prompt_id, prompt_sha256, true_label, prediction")
    for frame in (first, second):
        if frame[KEYS].isna().any().any() or frame.duplicated(KEYS).any():
            raise ValueError("Missing or duplicate paired identities")
    merged = first[list(required)].merge(second[list(required)], on=KEYS, how="outer", validate="one_to_one", indicator=True)
    if not (merged._merge == "both").all():
        raise ValueError("Methods evaluated different row sets")
    if not (merged.true_label_x == merged.true_label_y).all():
        raise ValueError("Inconsistent true labels")
    return merged


def compare(first, second, seed=2026, iterations=2000, cluster=False):
    paired = align(first, second)
    y, a, b = paired.true_label_x.to_numpy(), paired.prediction_x.to_numpy(), paired.prediction_y.to_numpy()
    results = {"hypothesis": "equal paired correctness; two-sided exact McNemar",
               "n_pairs": len(paired), "mcnemar_p": float(mcnemar_test(y, a, b)),
               "multiplicity": "unadjusted exploratory; prespecify family before confirmatory interpretation"}
    for name, metric in (("accuracy", accuracy_score), ("f1", lambda y, p: f1_score(y, p, zero_division=0)),
                         ("recall", lambda y, p: recall_score(y, p, zero_division=0))):
        results[name] = paired_bootstrap_difference(y, a, b, metric, seed=seed, n=iterations,
                                                   clusters=paired.dataset.to_numpy() if cluster else None)
    return results


def main():
    p = argparse.ArgumentParser(); p.add_argument("first"); p.add_argument("second")
    p.add_argument("--output", required=True); p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--iterations", type=int, default=2000); p.add_argument("--cluster-dataset", action="store_true")
    a = p.parse_args()
    first, second = [pd.read_csv(path, dtype={"prompt_id": str}) for path in (a.first, a.second)]
    result = compare(first, second, a.seed, a.iterations, a.cluster_dataset)
    output = Path(a.output)
    if output.exists(): raise ValueError("Refusing to overwrite existing comparison")
    atomic_write(output/"comparison.json", json.dumps(result, indent=2))
    table = pd.json_normalize(result)
    atomic_write(output/"comparison.csv", table.to_csv(index=False))
    atomic_write(output/"comparison.tex", table.to_latex(index=False))
    atomic_write(output/"comparison.md", "# Paired comparison\n\n"+json.dumps(result, indent=2))


if __name__ == "__main__": main()
