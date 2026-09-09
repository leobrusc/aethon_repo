"""Train the leakage-free BRACIS revision TF-IDF + LR publication model."""

from datetime import datetime, timezone
from pathlib import Path
import json
import platform
import subprocess

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from dataset_loader import get_dataset_metadata, load_dataset


TRAINING_DATASET = "prompt_injections_train"
MODEL_FILENAME = "aethon_tfidf_lr_revision.pkl"
THRESHOLD = 0.5


def train_revision_detector(output_path: Path | None = None) -> dict:
    project_root = Path(__file__).resolve().parents[1]
    output_path = output_path or project_root / "src" / "models" / MODEL_FILENAME
    frame = load_dataset(TRAINING_DATASET)
    tfidf_parameters = {
        "max_features": 5000, "analyzer": "word", "ngram_range": (1, 1),
        "lowercase": True, "min_df": 1, "max_df": 1.0, "sublinear_tf": False,
        "norm": "l2", "use_idf": True, "smooth_idf": True,
    }
    lr_parameters = {
        "max_iter": 1000, "random_state": 42, "solver": "lbfgs", "penalty": "l2",
        "C": 1.0, "class_weight": None, "fit_intercept": True, "tol": 1e-4,
    }
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(**tfidf_parameters)),
        ("lr", LogisticRegression(**lr_parameters)),
    ])
    pipeline.fit(frame["prompt_text"], frame["label"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output_path)
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project_root, check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unavailable"
    dataset_metadata = get_dataset_metadata(TRAINING_DATASET)
    metadata = {
        "model_path": str(output_path), "training_dataset": TRAINING_DATASET,
        "excluded_evaluation_datasets": [
            "prompt_injections_test", "prompt_injection_core", "jailbreakbench_behaviors",
            "wildjailbreak_eval", "notinject", "cyberseceval_prompt_injection",
            "red_team_attempts", "kaggle_redteam", "advbench_harmful",
        ],
        "number_of_samples": int(len(frame)), "benign": int((frame.label == 0).sum()),
        "adversarial": int((frame.label == 1).sum()), "dataset_sha256": dataset_metadata["sha256"],
        "dataset_source_file": dataset_metadata["file"], "tfidf_parameters": tfidf_parameters,
        "logistic_regression_parameters": lr_parameters, "decision_threshold": THRESHOLD,
        "random_state": 42, "sklearn_version": sklearn.__version__,
        "python_version": platform.python_version(), "git_commit": commit,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    metadata_path = output_path.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    print(json.dumps(train_revision_detector(), indent=2))
