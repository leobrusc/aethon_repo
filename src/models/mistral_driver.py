"""
mistral_driver.py
Driver para Mistral-7B (HF). Ajustes para cluster (FP16 + device_map).
Referência: Mistral AI, 2024.
"""
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import warnings

class Mistral7BDriver:
    NAME = "mistral-7b"
    HF_MODEL = "mistralai/mistral-7b-v0.3"  # ajustar se necessário

    def __init__(self, device=None):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.HF_MODEL, use_fast=True)
            if self.device == "cuda":
                self.model = AutoModelForCausalLM.from_pretrained(self.HF_MODEL, device_map="auto", torch_dtype=torch.float16)
            else:
                self.model = AutoModelForCausalLM.from_pretrained(self.HF_MODEL)
            self.gen = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer, device=0 if self.device=="cuda" else -1)
        except Exception as e:
            warnings.warn(f"Mistral7BDriver: problema ao carregar pesos: {e}")
            self.tokenizer = None
            self.model = None
            self.gen = None

    def infer(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2):
        if self.gen is None:
            return "[MODEL_NOT_LOADED]"
        out = self.gen(prompt, max_new_tokens=max_tokens, do_sample=(temperature>0.0), temperature=temperature, pad_token_id=self.tokenizer.eos_token_id)
        if isinstance(out, list) and len(out) > 0:
            return out[0].get("generated_text", "")
        return ""
