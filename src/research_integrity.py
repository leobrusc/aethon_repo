"""Text-free, deterministic audit of the preserved research datasets."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import time
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from baseline_reliability import atomic_write
from benchmark.detection import EVALUATION_DATASETS, LABEL_PROVENANCE
from dataset_loader import get_dataset_metadata, load_dataset


def normalize(text):
    """NFKC and whitespace collapse; preserve case and punctuation."""
    return " ".join(unicodedata.normalize("NFKC", str(text)).split())


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def implementation_hashes(*paths):
    return {str(Path(path).relative_to(Path(__file__).resolve().parent)): hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for path in paths}


def inventory(frames):
    rows, texts = [], []
    for dataset, frame in frames.items():
        for position, row in enumerate(frame.itertuples(index=False)):
            text = normalize(row.prompt_text)
            texts.append(text)
            rows.append({"dataset": dataset, "row_id": f"{dataset}:{position}",
                         "source_row_id": str(row.prompt_id), "source_position": position,
                         "normalized_sha256": digest(text), "raw_sha256": digest(str(row.prompt_text)),
                         "label": int(row.label), "label_provenance": LABEL_PROVENANCE[dataset],
                         "partition": "training" if dataset == "prompt_injections_train" else "inspected_reference"})
    return pd.DataFrame(rows), texts


def audit(frames, similarity=0.95):
    if not 0 < similarity <= 1:
        raise ValueError("similarity must be in (0,1]")
    records, texts = inventory(frames)
    exact = []
    for sha, group in records.groupby("normalized_sha256", sort=True):
        if len(group) > 1:
            exact.append({"normalized_sha256": sha, "rows": len(group),
                          "row_ids": "|".join(group.row_id),
                          "cross_partition": group.partition.nunique() > 1,
                          "conflicting_labels": group.label.nunique() > 1})
    # Exhaustive sparse cosine candidates, queried one row at a time to avoid
    # allocating a dense N x N similarity matrix. Lexical similarity is not semantics.
    near = []
    if len(texts) > 1 and any(texts):
        matrix = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit_transform(texts)
        transposed = matrix.T.tocsr()
        for i in range(len(texts)):
            similarities = (matrix[i] @ transposed).tocsr()
            for value, j in zip(similarities.data, similarities.indices):
                if value < similarity-1e-12:
                    continue
                if j <= i or records.iloc[i].normalized_sha256 == records.iloc[j].normalized_sha256:
                    continue
                a, b = records.iloc[i], records.iloc[j]
                near.append({"row_id_a": a.row_id, "row_id_b": b.row_id,
                             "cosine_similarity": float(value),
                             "cross_partition": a.partition != b.partition,
                             "conflicting_labels": a.label != b.label})
    summary = {"rows": len(records), "reference_rows": int((records.partition == "inspected_reference").sum()),
               "historical_pool_expected": 9139,
               "historical_pool_count_matches": int((records.partition == "inspected_reference").sum()) == 9139,
               "exact_duplicate_groups": len(exact), "near_duplicate_pairs": len(near),
               "cross_partition_exact_groups": sum(x["cross_partition"] for x in exact),
               "cross_partition_near_pairs": sum(x["cross_partition"] for x in near),
               "similarity_threshold": similarity, "semantic_overlap_audit": "NOT_RUN",
               "normalization": "Unicode NFKC; whitespace collapse; case preserved",
               "near_method": "corpus-fitted char_wb TF-IDF 3-5 cosine; lexical screening only"}
    return records, pd.DataFrame(exact), pd.DataFrame(near), summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/research_2026/integrity")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--similarity", type=float, default=.95)
    args = parser.parse_args()
    started = time.perf_counter()
    names = ["prompt_injections_train", *EVALUATION_DATASETS]
    metadata = [get_dataset_metadata(name) for name in names]
    config = {"datasets": metadata, "similarity": args.similarity, "schema": 2,
              "implementation": implementation_hashes(__file__, Path(__file__).with_name("dataset_loader.py")),
              "dependencies": {p: importlib.metadata.version(p) for p in ("numpy", "pandas", "scikit-learn")}}
    fingerprint = digest(json.dumps(config, sort_keys=True))
    output = Path(args.output) / args.run_id
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        if previous["fingerprint"] != fingerprint:
            raise ValueError("Existing run has incompatible configuration/data")
        if previous["status"] == "DONE":
            for name, sha in previous["artifact_hashes"].items():
                if hashlib.sha256((output/name).read_bytes()).hexdigest() != sha:
                    raise ValueError("Existing artifact hash mismatch")
            print(json.dumps(previous, indent=2)); return
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    manifest = {"run_id": args.run_id, "fingerprint": fingerprint, "config": config,
                "commit_sha": commit, "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True)),
                "status": "RUNNING", "checkpoint": "whole deterministic audit; restart on interruption",
                "python": platform.python_version(), "hardware": platform.uname()._asdict(),
                "dependencies": {p: importlib.metadata.version(p) for p in ("numpy", "pandas", "scikit-learn")},
                "seed": None, "model": None, "threshold": None, "temperature": None, "token_limit": None}
    atomic_write(manifest_path, json.dumps(manifest, indent=2))
    try:
        records, exact, near, summary = audit({n: load_dataset(n) for n in names}, args.similarity)
        artifacts = {"rows.csv": records.to_csv(index=False), "exact_duplicates.csv": exact.to_csv(index=False),
                     "near_duplicates.csv": near.to_csv(index=False), "summary.json": json.dumps(summary, indent=2),
                     "summary.md": "# Integrity audit\n\n```json\n" + json.dumps(summary, indent=2) + "\n```\n",
                     "summary.tex": pd.DataFrame([summary]).to_latex(index=False)}
        for name, content in artifacts.items():
            atomic_write(output/name, content)
        manifest.update(status="DONE", expected_records=len(records), processed_records=len(records),
                        duration_seconds=time.perf_counter()-started, errors=[],
                        artifact_hashes={n: hashlib.sha256((output/n).read_bytes()).hexdigest() for n in artifacts})
        atomic_write(manifest_path, json.dumps(manifest, indent=2))
        print(json.dumps(summary, indent=2))
    except Exception as exc:
        manifest.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        atomic_write(manifest_path, json.dumps(manifest, indent=2))
        raise


if __name__ == "__main__":
    main()
