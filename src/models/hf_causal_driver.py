"""
Generic Hugging Face causal language model driver.

Used for model aliases that only differ by HF repository id.
"""

import warnings

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline


class HuggingFaceCausalLMDriver:
    NAME = "hf-causal-lm"
    HF_MODEL = None

    def __init__(self, model_id=None, name=None, device=None):
        self.HF_MODEL = model_id or self.HF_MODEL
        self.NAME = name or self.NAME
        if not self.HF_MODEL:
            raise ValueError("HF model id must be provided.")

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self._use_device_map = self.device == "cuda"

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.HF_MODEL, use_fast=True)
            if self._use_device_map:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.HF_MODEL,
                    device_map="auto",
                    torch_dtype=torch.float16,
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(self.HF_MODEL)

            pipe_kwargs = {
                "task": "text-generation",
                "model": self.model,
                "tokenizer": self.tokenizer,
            }
            if not self._use_device_map:
                pipe_kwargs["device"] = -1
            self.gen = pipeline(**pipe_kwargs)
        except Exception as e:
            warnings.warn(f"{self.NAME}: problema ao carregar pesos: {e}")
            self.tokenizer = None
            self.model = None
            self.gen = None

    @property
    def available(self):
        return self.gen is not None

    def infer(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2):
        if self.gen is None:
            return "[MODEL_NOT_LOADED]"
        out = self.gen(
            prompt,
            max_new_tokens=max_tokens,
            do_sample=(temperature > 0.0),
            temperature=temperature,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        if isinstance(out, list) and len(out) > 0:
            return out[0].get("generated_text", "")
        return ""


class Llama2_7BChatDriver(HuggingFaceCausalLMDriver):
    NAME = "llama-2-7b-chat"
    HF_MODEL = "meta-llama/Llama-2-7b-chat-hf"


class Phi3Mini4KInstructDriver(HuggingFaceCausalLMDriver):
    NAME = "phi-3-mini-4k-instruct"
    HF_MODEL = "microsoft/Phi-3-mini-4k-instruct"


class Qwen25_3BInstructDriver(HuggingFaceCausalLMDriver):
    NAME = "qwen2.5-3b-instruct"
    HF_MODEL = "Qwen/Qwen2.5-3B-Instruct"


class Qwen25_7BInstructDriver(HuggingFaceCausalLMDriver):
    NAME = "qwen2.5-7b-instruct"
    HF_MODEL = "Qwen/Qwen2.5-7B-Instruct"


class TinyLlama_11BChatDriver(HuggingFaceCausalLMDriver):
    NAME = "tinyllama-1.1b-chat"
    HF_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"


class Llama32_1BInstructDriver(HuggingFaceCausalLMDriver):
    NAME = "llama-3.2-1b-instruct"
    HF_MODEL = "meta-llama/Llama-3.2-1B-Instruct"


class Llama32_3BInstructDriver(HuggingFaceCausalLMDriver):
    NAME = "llama-3.2-3b-instruct"
    HF_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
