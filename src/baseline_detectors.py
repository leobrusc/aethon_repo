"""CPU adapters for the approved prompt-injection detector baselines."""
from __future__ import annotations
import time
from dataclasses import dataclass
import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

@dataclass
class Prediction:
    score: float
    prediction: int
    latency_ms: float
    truncated: bool
    token_count: int

class TransformerDetector:
    def __init__(self, model_id: str, malicious_labels=("malicious", "injection", "1"), max_length=512):
        self.model_id, self.max_length = model_id, max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_id).to("cpu").eval()
        self.malicious_labels = {str(x).lower() for x in malicious_labels}
        self.malicious_index = self._find_index()
        self.warmup_count = 0
    def _find_index(self):
        labels = getattr(self.model.config, "id2label", {}) or {}
        for i, label in labels.items():
            if str(label).lower() in self.malicious_labels or any(x in str(label).lower() for x in self.malicious_labels):
                return int(i)
        return 1 if getattr(self.model.config, "num_labels", 2) == 2 else 0
    def warmup(self, prompts):
        for p in prompts:
            self._infer(p, timed=False)
        self.warmup_count = len(prompts)
    def _infer(self, prompt, timed=True):
        raw = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=self.max_length)
        length = int(raw["input_ids"].shape[1])
        with torch.inference_mode():
            start = time.perf_counter(); out = self.model(**raw); elapsed = (time.perf_counter()-start)*1000 if timed else 0.0
        probs = torch.softmax(out.logits, dim=-1)[0].cpu().numpy()
        return Prediction(float(probs[self.malicious_index]), int(np.argmax(probs) == self.malicious_index), elapsed, length >= self.max_length, length)
    def predict(self, prompt): return self._infer(prompt, timed=True)

class PromptGuard22M(TransformerDetector):
    def __init__(self): super().__init__("meta-llama/Llama-Prompt-Guard-2-22M", ("malicious",))

class ProtectAIV2(TransformerDetector):
    def __init__(self): super().__init__("protectai/deberta-v3-base-prompt-injection-v2", ("1", "injection"))
