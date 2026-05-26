"""
model_registry.py
Registra drivers de modelo e fornece factory get_model_driver(name, **kwargs).
Adicione novos drivers ao dicionário MODEL_REGISTRY.
"""
from pathlib import Path

# Import drivers
from models.phi2_driver import Phi2Driver
from models.mistral_driver import Mistral7BDriver
from models.llama3_8b_driver import LLaMA3_8B_Driver
from models.openai_driver import OpenAIDriver
from models.deepseek_driver import DeepSeekDriver
from models.hf_causal_driver import (
    Llama2_7BChatDriver,
    Llama32_1BInstructDriver,
    Llama32_3BInstructDriver,
)


class GPT54NanoDriver(OpenAIDriver):
    NAME = "gpt-5.4-nano"

    def __init__(self, model_name=None):
        super().__init__(model_name=model_name or self.NAME)

MODEL_REGISTRY = {
    "phi-2": Phi2Driver,
    "mistral-7b": Mistral7BDriver,
    "llama3-8b": LLaMA3_8B_Driver,
    "gpt-4o-mini": OpenAIDriver,
    "gpt-5.4-nano": GPT54NanoDriver,
    "llama-2-7b-chat": Llama2_7BChatDriver,
    "llama-3.2-1b-instruct": Llama32_1BInstructDriver,
    "llama-3.2-3b-instruct": Llama32_3BInstructDriver,
    "deepseek-v4-flash": DeepSeekDriver,
    # add other names here as needed
}

def get_model_driver(name: str, **kwargs):
    """
    Returns an instance of the driver for 'name'.
    For OpenAI models, pass model_name='<model-id>' as kwarg to override (e.g., 'gpt-4o', 'gpt-4-turbo').
    """
    key = name.lower()
    if key not in MODEL_REGISTRY:
        raise ValueError(f"[model_registry] Model '{name}' not registered. Available: {list(MODEL_REGISTRY.keys())}")
    Driver = MODEL_REGISTRY[key]
    # OpenAIDriver accepts model_name param
    if key.startswith("gpt") and kwargs.get("model_name"):
        return Driver(model_name=kwargs.get("model_name"))
    return Driver()
