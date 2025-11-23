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

MODEL_REGISTRY = {
    "phi-2": Phi2Driver,
    "mistral-7b": Mistral7BDriver,
    "llama3-8b": LLaMA3_8B_Driver,
    "gpt-4o-mini": OpenAIDriver,
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
    if key.startswith("gpt") and "model_name" in kwargs:
        return Driver(model_name=kwargs.get("model_name"))
    return Driver()
