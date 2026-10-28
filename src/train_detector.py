"""Train the lightweight TF-IDF + Logistic Regression AETHON classifier."""

import argparse
import json
from pathlib import Path

import pandas as pd

from aethon_ml_pipeline import train_tfclf
from dataset_loader import load_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Train an AETHON ML detector for B2-B4 benchmark conditions.")
    parser.add_argument("--datasets", nargs="+", default=["prompt_injections_train"])
    parser.add_argument("--save-name", default="aethon_tfidf_lr.pkl")
    args = parser.parse_args()

    if set(args.datasets) != {"prompt_injections_train"}:
        parser.error("Only prompt_injections_train is authorized for selection; reference evaluation sources are excluded.")

    frames = [load_dataset(name) for name in args.datasets]
    training = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["prompt_text", "label"])
    if training["label"].nunique() < 2:
        raise ValueError("Training data must contain both benign and adversarial labels.")
    result = train_tfclf(training["prompt_text"].tolist(), training["label"].tolist(), save_name=args.save_name)
    result["datasets"] = args.datasets
    result["n_samples"] = int(len(training))
    metadata_path = Path(result["path"]).with_suffix(".json")
    metadata_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
