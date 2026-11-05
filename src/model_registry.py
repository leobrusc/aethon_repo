"""Lazy registry for local and API-backed model drivers."""

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, Dict
import os


@dataclass(frozen=True)
class LazyDriver:
    module: str
    class_name: str
    default_kwargs: Dict[str, Any] = field(default_factory=dict)

    def __call__(self, **kwargs):
        driver_class = getattr(import_module(self.module), self.class_name)
        parameters = dict(self.default_kwargs)
        parameters.update({key: value for key, value in kwargs.items() if value is not None})
        return driver_class(**parameters)


MODEL_REGISTRY = {
    "llama-2-7b-chat": LazyDriver("models.hf_causal_driver", "Llama2_7BChatDriver"),
    "llama-3.2-1b-instruct": LazyDriver("models.hf_causal_driver", "Llama32_1BInstructDriver"),
    "llama-3.2-3b-instruct": LazyDriver("models.hf_causal_driver", "Llama32_3BInstructDriver"),
    "qwen2.5-3b-instruct": LazyDriver("models.hf_causal_driver", "Qwen25_3BInstructDriver"),
    "qwen2.5-7b-instruct": LazyDriver("models.hf_causal_driver", "Qwen25_7BInstructDriver"),
    "phi-3-mini-4k-instruct": LazyDriver("models.hf_causal_driver", "Phi3Mini4KInstructDriver"),
    "phi-2": LazyDriver("models.phi2_driver", "Phi2Driver"),
    "mistral-7b": LazyDriver("models.mistral_driver", "Mistral7BDriver"),
    "llama3-8b": LazyDriver("models.llama3_8b_driver", "LLaMA3_8B_Driver"),
    "tinyllama-1.1b-chat": LazyDriver("models.hf_causal_driver", "TinyLlama_11BChatDriver"),
    "gpt-4o-mini": LazyDriver("models.openai_driver", "OpenAIDriver", {"model_name": "gpt-4o-mini"}),
    "gpt-5.4-nano": LazyDriver("models.openai_driver", "OpenAIDriver", {"model_name": "gpt-5.4-nano"}),
    "gpt-5.4-mini": LazyDriver("models.openai_driver", "OpenAIDriver", {"model_name": "gpt-5.4-mini"}),
    "deepseek-v4-flash": LazyDriver("models.deepseek_driver", "DeepSeekDriver", {"model_name": "deepseek-v4-flash"}),
}

MODEL_VERSIONS = {
    "llama-2-7b-chat": "meta-llama/Llama-2-7b-chat-hf",
    "llama-3.2-1b-instruct": "meta-llama/Llama-3.2-1B-Instruct",
    "llama-3.2-3b-instruct": "meta-llama/Llama-3.2-3B-Instruct",
    "qwen2.5-3b-instruct": "Qwen/Qwen2.5-3B-Instruct",
    "qwen2.5-7b-instruct": "Qwen/Qwen2.5-7B-Instruct",
    "phi-3-mini-4k-instruct": "microsoft/Phi-3-mini-4k-instruct",
    "phi-2": "microsoft/phi-2",
    "mistral-7b": "mistralai/mistral-7b-v0.3",
    "llama3-8b": "meta-llama/Llama-3-8B-Instruct",
    "tinyllama-1.1b-chat": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-5.4-nano": "gpt-5.4-nano",
    "gpt-5.4-mini": "gpt-5.4-mini",
    "deepseek-v4-flash": "deepseek-v4-flash",
}

MODEL_ALIASES = {
    "meta-llama/llama-2-7b-chat-hf": "llama-2-7b-chat",
    "meta-llama/llama-3.2-1b-instruct": "llama-3.2-1b-instruct",
    "meta-llama/llama-3.2-3b-instruct": "llama-3.2-3b-instruct",
    "microsoft/phi-3-mini-4k-instruct": "phi-3-mini-4k-instruct",
    "qwen/qwen2.5-3b-instruct": "qwen2.5-3b-instruct",
    "qwen/qwen2.5-7b-instruct": "qwen2.5-7b-instruct",
    "tinyllama/tinyllama-1.1b-chat-v1.0": "tinyllama-1.1b-chat",
}

LLAMA_BENCHMARK_MODELS = [
    "llama-2-7b-chat",
    "llama-3.2-1b-instruct",
    "llama-3.2-3b-instruct",
]

OPEN_BENCHMARK_MODELS = [
    *LLAMA_BENCHMARK_MODELS,
    "qwen2.5-3b-instruct",
    "qwen2.5-7b-instruct",
    "phi-3-mini-4k-instruct",
]

API_BENCHMARK_MODELS = [
    "gpt-5.4-nano",
    "gpt-5.4-mini",
    "deepseek-v4-flash",
]

MODEL_REQUIRED_ENV = {
    "gpt-4o-mini": "OPENAI_API_KEY",
    "gpt-5.4-nano": "OPENAI_API_KEY",
    "gpt-5.4-mini": "OPENAI_API_KEY",
    "deepseek-v4-flash": "DEEPSEEK_API_KEY",
}


def normalize_model_name(name: str) -> str:
    key = name.lower()
    return MODEL_ALIASES.get(key, key)


def get_model_driver(name: str, **kwargs):
    key = normalize_model_name(name)
    if key not in MODEL_REGISTRY:
        raise ValueError(f"[model_registry] Model '{name}' not registered. Available: {list(MODEL_REGISTRY.keys())}")
    contract = kwargs.pop("contract_version", "aethon.generation.v1")
    if contract not in {"aethon.generation.v1", "legacy-v1"}:
        raise ValueError("Unknown generation contract")
    if MODEL_REGISTRY[key].module not in {"models.openai_driver", "models.deepseek_driver"} and contract != "legacy-v1":
        from aethon.generation import ExplicitCausalLMDriver
        kwargs.setdefault("model_id", MODEL_VERSIONS[key])
        kwargs.setdefault("name", key)
        return ExplicitCausalLMDriver(**kwargs)
    return MODEL_REGISTRY[key](**kwargs)


def get_model_version(name: str) -> str:
    key = normalize_model_name(name)
    return MODEL_VERSIONS.get(key, name)


def get_model_availability_error(name: str, dry_run: bool = False) -> str:
    if dry_run:
        return ""
    key = normalize_model_name(name)
    required_env = MODEL_REQUIRED_ENV.get(key)
    if required_env and not os.getenv(required_env):
        return f"missing required credential environment variable: {required_env}"
    return ""
