"""AETHON ablation conditions and deterministic cascade evaluation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import time

import numpy as np

from aethon_heuristic import is_adversarial_heuristic
from aethon_ml_pipeline import load_model


class MissingClassifierError(RuntimeError):
    """Raised when an ML ablation condition has no trained classifier."""


@dataclass
class MiddlewareResult:
    heuristic_flag: Optional[bool]
    ml_prediction: Optional[int]
    ml_score: Optional[float]
    detection_score: Optional[float]
    final_decision: str
    blocked: bool
    noisy_audit_count: Optional[float]
    latency_ms: float


class BenchmarkMiddleware:
    def __init__(self, ml_model_path: Optional[str], epsilon: float, seed: int):
        self.epsilon = epsilon
        self.rng = np.random.default_rng(seed)
        self.ml_model = None
        if ml_model_path:
            path = Path(ml_model_path)
            if not path.exists():
                raise FileNotFoundError(f"ML model not found: {path}")
            self.ml_model = load_model(str(path))

    def _predict_ml(self, prompt: str) -> tuple[int, Optional[float]]:
        if self.ml_model is None:
            raise MissingClassifierError("B2, B3 and B4 require --ml-model-path.")
        prediction = int(self.ml_model.predict([prompt])[0])
        score = None
        if hasattr(self.ml_model, "predict_proba"):
            score = float(self.ml_model.predict_proba([prompt])[0][1])
        return prediction, score

    def evaluate(self, prompt: str, condition: str) -> MiddlewareResult:
        started = time.perf_counter()
        heuristic_flag: Optional[bool] = None
        ml_prediction: Optional[int] = None
        ml_score: Optional[float] = None
        detection_score: Optional[float] = None
        noisy_count: Optional[float] = None

        if condition == "B0":
            blocked = False
        elif condition == "B1":
            heuristic_flag = is_adversarial_heuristic(prompt)
            blocked = heuristic_flag
            detection_score = float(heuristic_flag)
        elif condition == "B2":
            ml_prediction, ml_score = self._predict_ml(prompt)
            detection_score = ml_score if ml_score is not None else float(ml_prediction)
            blocked = ml_prediction == 1
        elif condition in {"B3", "B4"}:
            heuristic_flag = is_adversarial_heuristic(prompt)
            ml_prediction, ml_score = self._predict_ml(prompt)
            blocked = heuristic_flag or ml_prediction == 1
            detection_score = max(float(heuristic_flag), ml_score if ml_score is not None else float(ml_prediction))
            if condition == "B4":
                noisy_count = float(1 + self.rng.laplace(0, 1 / self.epsilon))
        else:
            raise ValueError(f"Unknown condition: {condition}")

        return MiddlewareResult(
            heuristic_flag=heuristic_flag,
            ml_prediction=ml_prediction,
            ml_score=ml_score,
            detection_score=detection_score,
            final_decision="mitigate" if blocked else "allow",
            blocked=bool(blocked),
            noisy_audit_count=noisy_count,
            latency_ms=(time.perf_counter() - started) * 1000,
        )
