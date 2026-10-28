"""CPU adapters for the approved prompt-injection detector baselines."""
from __future__ import annotations
import time
from dataclasses import dataclass
import numpy as np
from scipy.special import softmax
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
    def __init__(self, model_id: str, malicious_labels=("malicious", "injection", "1"), max_length=512, device="auto", dtype="float32", revision=None, local_files_only=False):
        self.model_id, self.max_length = model_id, max_length
        if device == "auto": device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda" and not torch.cuda.is_available(): raise RuntimeError("CUDA requested but unavailable")
        if device not in {"cpu", "cuda"}: raise ValueError("device must be auto, cpu, or cuda")
        self.device, self.dtype = torch.device(device), dtype
        options = {"revision": revision, "local_files_only": local_files_only}
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, **options)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_id, **options).to(self.device).eval()
        self.revision = revision
        self.malicious_labels = {str(x).lower() for x in malicious_labels}
        self.malicious_index = self._find_index()
        self.warmup_count = 0
    def _find_index(self):
        labels = getattr(self.model.config, "id2label", {}) or {}
        matches = [int(i) for i, label in labels.items() if str(label).lower() in self.malicious_labels]
        if len(matches) != 1:
            raise ValueError(f"Unknown or ambiguous malicious label mapping: {labels}")
        return matches[0]
    def warmup(self, prompts):
        for p in prompts:
            self._infer(p, timed=False)
        self.warmup_count = len(prompts)
    def _infer(self, prompt, timed=True):
        raw = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=self.max_length)
        length = int(raw["input_ids"].shape[1])
        raw = {k:v.to(self.device) for k,v in raw.items()}
        if self.device.type == "cuda": torch.cuda.synchronize()
        with torch.inference_mode():
            start = time.perf_counter(); out = self.model(**raw)
            if self.device.type == "cuda": torch.cuda.synchronize()
            elapsed = (time.perf_counter()-start)*1000 if timed else 0.0
        probs = softmax(out.logits.detach().cpu().numpy(), axis=-1)[0]
        return Prediction(float(probs[self.malicious_index]), int(np.argmax(probs) == self.malicious_index), elapsed, length >= self.max_length, length)
    def predict(self, prompt): return self._infer(prompt, timed=True)
    def predict_batch(self, prompts):
        raw = self.tokenizer(list(prompts), return_tensors="pt", truncation=True, max_length=self.max_length, padding=True)
        lengths = raw["attention_mask"].sum(dim=1).tolist()
        raw = {k:v.to(self.device) for k,v in raw.items()}
        with torch.inference_mode(): out = self.model(**raw)
        probs = softmax(out.logits.detach().cpu().numpy(), axis=-1)
        return [(float(p[self.malicious_index]), int(np.argmax(p)==self.malicious_index), int(l>=self.max_length), int(l)) for p,l in zip(probs,lengths)]

class PromptGuard22M(TransformerDetector):
    def __init__(self, device="auto"): super().__init__("meta-llama/Llama-Prompt-Guard-2-22M", ("malicious",), device=device)

class ProtectAIV2(TransformerDetector):
    def __init__(self, device="auto"): super().__init__("protectai/deberta-v3-base-prompt-injection-v2", ("1", "injection"), device=device)
