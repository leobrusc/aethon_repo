"""Configuration model for repeatable benchmark executions."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


CONDITIONS = ("B0", "B1", "B2", "B3", "B4")
ASR_JUDGE_TYPES = ("none", "rule", "llm")


@dataclass
class BenchmarkConfig:
    models: List[str]
    datasets: List[str]
    conditions: List[str] = field(default_factory=lambda: list(CONDITIONS))
    seed: int = 42
    temperature: float = 0.2
    epsilon: float = 1.2
    max_tokens: int = 256
    limit: Optional[int] = None
    random_sample: bool = False
    dry_run: bool = False
    ml_model_path: Optional[str] = None
    output_root: str = "results"
    run_id: Optional[str] = None
    resume: bool = False
    generate_tables: bool = True
    asr_judge_type: str = "rule"
    asr_judge_model: Optional[str] = None

    def validate(self) -> None:
        invalid = [condition for condition in self.conditions if condition not in CONDITIONS]
        if invalid:
            raise ValueError(f"Unknown benchmark conditions: {invalid}. Allowed: {list(CONDITIONS)}")
        if self.limit is not None and self.limit <= 0:
            raise ValueError("limit must be greater than zero.")
        if self.epsilon <= 0:
            raise ValueError("epsilon must be greater than zero.")
        if not self.models or not self.datasets:
            raise ValueError("At least one model and one dataset are required.")
        if self.asr_judge_type not in ASR_JUDGE_TYPES:
            raise ValueError(f"Unknown ASR judge type: {self.asr_judge_type}. Allowed: {list(ASR_JUDGE_TYPES)}")
        if self.asr_judge_type == "llm" and not self.asr_judge_model:
            raise ValueError("asr_judge_model is required for the optional LLM judge.")

    @classmethod
    def from_json(cls, path: str) -> "BenchmarkConfig":
        with Path(path).open("r", encoding="utf-8") as config_file:
            return cls(**json.load(config_file))

    def update(self, overrides: Dict[str, Any]) -> "BenchmarkConfig":
        values = asdict(self)
        values.update({key: value for key, value in overrides.items() if value is not None})
        return BenchmarkConfig(**values)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
