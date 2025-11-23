"""
phi2_driver.py
Driver para Phi-2 (HF). Uso como 'drop-in' para o model_registry.
Notas:
- Modelo: microsoft/phi-2 (referência: Microsoft, 2024)
- Requer transformers >= 4.40
- Execute em GPU (device_map="auto") no cluster; em CPU local fallback.
"""
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import warnings

class Phi2Driver:
    NAME = "phi-2"
    HF_MODEL = "microsoft/phi-2"

    def __init__(self, device=None):
        # Device resolution
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.HF_MODEL, use_fast=True)
            # load with device_map if cuda available to reduce memory footprint
            if self.device == "cuda":
                self.model = AutoModelForCausalLM.from_pretrained(self.HF_MODEL, device_map="auto", torch_dtype=torch.float16)
            else:
                self.model = AutoModelForCausalLM.from_pretrained(self.HF_MODEL)
            self.gen = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer, device=0 if self.device=="cuda" else -1)
        except Exception as e:
            warnings.warn(f"Phi2Driver: problema ao carregar pesos: {e}")
            self.tokenizer = None
            self.model = None
            self.gen = None

    def infer(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2):
        """Generate text for given prompt. Returns string."""
        if self.gen is None:
            return "[MODEL_NOT_LOADED]"
        out = self.gen(prompt, max_new_tokens=max_tokens, do_sample=(temperature>0.0), temperature=temperature, pad_token_id=self.tokenizer.eos_token_id)
        if isinstance(out, list) and len(out) > 0:
            return out[0].get("generated_text", "")
        return ""
