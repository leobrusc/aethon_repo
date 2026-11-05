"""Synthetic contract tests; these do not count as real pretrained inference."""
import json
from types import SimpleNamespace

import pytest
import torch
import transformers

from aethon.generation import (ExplicitCausalLMDriver, GenerationResult, PrecisionConfig,
                               evaluation_response, precision_observation, split_decoder_output)
from benchmark.asr import RuleBasedASRJudge


class Batch(dict):
    def to(self, device):
        return Batch({k: v.to(device) for k, v in self.items()})


class Tokenizer:
    chat_template = "reviewed template"
    eos_token_id = 9
    special_tokens_map = {"eos_token": "<eos>"}

    def __call__(self, value, **kwargs):
        return Batch(input_ids=torch.tensor([[1, 2]]), attention_mask=torch.ones((1, 2), dtype=torch.long))

    def apply_chat_template(self, messages, tokenize, **kwargs):
        return [1, 2] if tokenize else "rendered template"

    def decode(self, ids, **kwargs):
        return "".join({1: "Here is how: ", 2: "prompt", 3: "I cannot assist", 9: ""}.get(i, "x") for i in ids)


class Model(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.ones(2))
        self.register_buffer("rotary", torch.ones(2))
        self.config = SimpleNamespace(is_encoder_decoder=False)
        self.generation_config = SimpleNamespace(eos_token_id=[9], to_dict=lambda: {"eos_token_id": [9]})
        self.tokens = [3, 9]

    def forward(self, inputs):
        return {"logits": self.weight * 2}

    def generate(self, input_ids, **kwargs):
        self(input_ids)
        return torch.cat((input_ids, torch.tensor([self.tokens], device=input_ids.device, dtype=torch.long)), dim=1)


@pytest.fixture
def factory(monkeypatch):
    calls = []
    def load(*a, **kw):
        calls.append(kw)
        return Model().to(dtype=kw["torch_dtype"])
    monkeypatch.setattr(transformers.AutoModelForCausalLM, "from_pretrained", load)
    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", lambda *a, **kw: Tokenizer())
    return lambda **kw: ExplicitCausalLMDriver("test-reviewed", **kw), calls


def test_explicit_fp32_loader_and_forward(factory):
    create, calls = factory
    driver = create()
    result = driver.generate_result("prompt", temperature=0)
    assert calls[0]["torch_dtype"] is torch.float32
    assert calls[0]["trust_remote_code"] is False and calls[0]["use_safetensors"] is True
    assert result.metadata["precision_after"]["floating_parameter_elements_by_dtype"] == {"torch.float32": 2}
    assert result.metadata["observed_forward_floating_dtypes"] == ["torch.float32"]


def test_bf16_supported_with_separate_fp32_buffer(factory):
    create, _ = factory
    driver = create(precision="bfloat16")
    driver.model.rotary = driver.model.rotary.float()
    result = driver.generate_result("prompt", temperature=0)
    assert result.metadata["precision_after"]["floating_buffers"]["rotary"]["dtype"] == "torch.float32"
    assert result.metadata["observed_forward_floating_dtypes"] == ["torch.bfloat16"]


@pytest.mark.parametrize("dtype,device,version", [("auto", "cpu", "aethon.precision.v1"), ("float16", "cpu", "aethon.precision.v1"),
    ("float32", "mps", "aethon.precision.v1"), ("float32", "cpu", "unknown")])
def test_reject_unsupported(dtype, device, version):
    with pytest.raises(ValueError):
        PrecisionConfig(dtype, device, version).resolve()


def test_cuda_policy_without_hardware(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(ValueError, match="CUDA unavailable"):
        PrecisionConfig("float16", "cuda").resolve()
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "is_bf16_supported", lambda: False)
    with pytest.raises(ValueError, match="BF16 unsupported"):
        PrecisionConfig("bfloat16", "cuda").resolve()
    assert PrecisionConfig("float16", "cuda").resolve() == torch.float16


def test_mismatch_rejected_before_and_after_generation(factory):
    create, _ = factory
    driver = create()
    driver.model.to(dtype=torch.float64)
    with pytest.raises(ValueError, match="mismatch"):
        driver.generate_result("prompt")
    with pytest.raises(ValueError):
        precision_observation(Model(), PrecisionConfig("bfloat16"))
    driver = create()
    original = driver.model.generate
    def mutate(**kw):
        result = original(**kw)
        driver.model.to(dtype=torch.float64)
        return result
    driver.model.generate = mutate
    with pytest.raises(ValueError, match="mismatch"):
        driver.generate_result("prompt")


def test_chat_template_and_token_boundary_echo(factory):
    create, _ = factory
    driver = create()
    result = driver.generate_result("prompt", messages=[{"role": "user", "content": "prompt"}])
    assert result.input_ids == [1, 2] and result.generated_ids == [3, 9]
    assert result.continuation == "I cannot assist"
    assert result.legacy_full_text == "Here is how: promptI cannot assist"
    assert result.original_prompt == "prompt" and result.metadata["chat_template_applied"]
    with pytest.raises(ValueError):
        driver.generate_result("different", messages=[{"role": "user", "content": "prompt"}])
    driver.tokenizer.chat_template = None
    with pytest.raises(ValueError, match="template"):
        driver.generate_result("prompt", messages=[{"role": "user", "content": "prompt"}])


@pytest.mark.parametrize("tokens,limit,stop,text", [([], 2, "empty", ""), ([9], 2, "eos", ""), ([3, 9], 2, "eos", "I cannot assist"),
                                                  ([3], 1, "length", "I cannot assist"), ([3], 2, "unknown", "I cannot assist")])
def test_empty_eos_length_unknown(factory, tokens, limit, stop, text):
    create, _ = factory
    driver = create()
    driver.model.tokens = tokens
    result = driver.generate_result("prompt", max_tokens=limit)
    assert result.stop_reason == stop and result.continuation == text
    assert evaluation_response(driver, "prompt", max_tokens=limit) == text


def test_serialization_and_legacy_interface(factory):
    create, _ = factory
    driver = create()
    result = driver.generate_result("prompt")
    assert GenerationResult.from_json(result.to_json()) == result
    assert driver.infer("prompt") == result.legacy_full_text
    data = result.to_dict()
    data["version"] = "unknown"
    with pytest.raises(ValueError):
        GenerationResult.from_json(json.dumps(data))
    with pytest.raises(ValueError):
        split_decoder_output([1, 2], [1, 3, 9])


def test_asr_never_uses_prompt_echo_or_eos_only(factory):
    create, _ = factory
    driver = create()
    judge = RuleBasedASRJudge()
    def assess():
        return judge.judge("prompt", evaluation_response(driver, "prompt"), False, "red_team_attempts", "red_team_attempts", 1)
    assert assess().asr_result == "failed"
    driver.model.tokens = [9]
    assert assess().asr_result == "not_evaluated"
    class Legacy:
        def infer(self, prompt, **kw):
            return prompt
    with pytest.raises(ValueError, match="ineligible"):
        evaluation_response(Legacy(), "Here is how: instructions")


def test_encoder_decoder_rejected(factory):
    create, _ = factory
    driver = create()
    driver.model.config.is_encoder_decoder = True
    # Generation must reject architecture drift too.
    with pytest.raises(ValueError, match="decoder-only"):
        driver.generate_result("prompt")


def test_registry_dispatch_and_explicit_historical_opt_in(monkeypatch):
    from model_registry import get_model_driver
    monkeypatch.setattr("aethon.generation.ExplicitCausalLMDriver", lambda **kw: kw)
    assert get_model_driver("llama-3.2-1b-instruct", precision="float32")["precision"] == "float32"
    class Legacy:
        def __init__(self, **kw):
            self.kw = kw
    import models.hf_causal_driver as historical
    monkeypatch.setattr(historical, "Llama32_1BInstructDriver", Legacy)
    assert isinstance(get_model_driver("llama-3.2-1b-instruct", contract_version="legacy-v1"), Legacy)
    with pytest.raises(ValueError):
        get_model_driver("llama-3.2-1b-instruct", contract_version="unknown")
