"""Versioned, explicit inference contracts. Historical drivers remain immutable."""
from dataclasses import asdict, dataclass
import hashlib
import json
import importlib.metadata
from pathlib import Path
import re


@dataclass(frozen=True)
class PrecisionConfig:
    dtype: str = "float32"
    device: str = "cpu"
    version: str = "aethon.precision.v1"

    def resolve(self):
        import torch
        if self.version != "aethon.precision.v1" or self.dtype not in {"float32", "float16", "bfloat16"}:
            raise ValueError("Unsupported precision contract")
        if self.device not in {"cpu", "cuda"}:
            raise ValueError("Explicit cpu or cuda device required")
        if self.device == "cuda":
            if not torch.cuda.is_available():
                raise ValueError("CUDA unavailable; no fallback permitted")
            if self.dtype == "bfloat16" and not torch.cuda.is_bf16_supported():
                raise ValueError("CUDA BF16 unsupported")
        elif self.dtype == "float16":
            raise ValueError("CPU FP16 is outside precision.v1 supported policy")
        dtype = getattr(torch, self.dtype)
        # A kernel capability probe, not a claim of native hardware acceleration.
        if self.dtype == "bfloat16":
            try:
                value = torch.ones((2, 2), dtype=dtype, device=self.device)
                if (value @ value).dtype != dtype:
                    raise ValueError("BF16 kernel changed dtype")
            except Exception as exc:
                raise ValueError("BF16 operator unavailable") from exc
        return dtype


@dataclass(frozen=True)
class GenerationResult:
    original_prompt: str
    input_ids: list
    generated_ids: list
    continuation: str
    legacy_full_text: str
    stop_reason: str
    metadata: dict
    version: str = "aethon.generation.v1"

    def __post_init__(self):
        if self.version != "aethon.generation.v1":
            raise ValueError("Unsupported generation contract")
        if self.stop_reason not in {"eos", "length", "empty", "unknown"}:
            raise ValueError("Invalid stop reason")
        for ids in (self.input_ids, self.generated_ids):
            if not isinstance(ids, list) or any(type(i) is not int or i < 0 for i in ids):
                raise ValueError("Invalid token IDs")
        if not all(isinstance(s, str) for s in (self.original_prompt, self.continuation, self.legacy_full_text)):
            raise ValueError("Invalid text fields")
        if not self.generated_ids and self.continuation:
            raise ValueError("Text without generated tokens")

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, allow_nan=False)

    @classmethod
    def from_json(cls, value):
        return cls(**json.loads(value))


def split_decoder_output(input_ids, output_ids):
    """Decoder-only sequences must retain their exact input token prefix."""
    if output_ids[:len(input_ids)] != input_ids:
        raise ValueError("Generated sequence does not preserve input token prefix")
    return output_ids[len(input_ids):]


def precision_observation(model, precision):
    """Check every floating parameter; inventory buffers separately (e.g. RoPE FP32)."""
    import torch
    parameters, buffers = {}, {}
    for name, tensor in model.named_parameters():
        if tensor.is_floating_point():
            parameters[str(tensor.dtype)] = parameters.get(str(tensor.dtype), 0) + tensor.numel()
            if str(tensor.dtype) != "torch." + precision.dtype or tensor.device.type != precision.device:
                raise ValueError(f"Requested/observed parameter precision or device mismatch: {name}")
    if not parameters:
        raise ValueError("No floating parameters available for precision verification")
    for name, tensor in model.named_buffers():
        if tensor.is_floating_point():
            buffers[name] = {"dtype": str(tensor.dtype), "device": str(tensor.device), "numel": tensor.numel()}
    return {"contract": asdict(precision), "floating_parameter_elements_by_dtype": parameters,
            "floating_buffers": buffers, "autocast_enabled": torch.is_autocast_enabled(),
            "scope": "Parameter storage validated; buffers and observed forward outputs reported separately. Not a claim of uniform arithmetic precision."}


class ExplicitCausalLMDriver:
    """Offline native decoder-only models, explicit parameter dtype, no remote code.

    infer() retains the legacy full-text string interface. Evaluators must use
    generate_result(), which never removes prompts by manipulating text.
    """
    def __init__(self, model_id, name=None, device="cpu", precision="float32", revision=None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.NAME, self.HF_MODEL = name or model_id, model_id
        local = Path(model_id)
        snapshot_revision = local.name if local.parent.name == "snapshots" and re.fullmatch("[a-f0-9]{40}", local.name) else None
        if snapshot_revision and revision and snapshot_revision != revision:
            raise ValueError("Local snapshot and requested revision disagree")
        self.precision = PrecisionConfig(precision, device)
        dtype = self.precision.resolve()
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision,
                            local_files_only=True, trust_remote_code=False)
        # torch_dtype is explicit in both historical HF4 and maintained HF5.
        self.model = AutoModelForCausalLM.from_pretrained(model_id, revision=revision,
                            local_files_only=True, trust_remote_code=False,
                            use_safetensors=True, torch_dtype=dtype).to(device).eval()
        if self.model.config.is_encoder_decoder:
            raise ValueError("generation.v1 supports decoder-only architectures; use a separate contract for encoder-decoder")
        self.observation = precision_observation(self.model, self.precision)
        self.revision = snapshot_revision or getattr(self.model.config, "_commit_hash", None)
        self.requested_revision = revision
        self.available = True
        self.device = device
        self.torch = torch

    def generate_result(self, prompt, max_tokens=256, temperature=0.2, *, messages=None):
        torch = self.torch
        if self.model.config.is_encoder_decoder:
            raise ValueError("generation.v1 requires decoder-only architecture")
        if not isinstance(prompt, str) or type(max_tokens) is not int or max_tokens < 1 or not 0 <= temperature <= 100:
            raise ValueError("Invalid generation request")
        rendered = prompt
        if messages is not None:
            if not self.tokenizer.chat_template:
                raise ValueError("Chat template required")
            if not messages or messages[-1] != {"role": "user", "content": prompt}:
                raise ValueError("Original prompt must match final user message")
            rendered = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(rendered, return_tensors="pt", add_special_tokens=messages is None).to(self.device)
        input_ids = inputs["input_ids"][0].tolist()
        if messages is not None:
            template_ids = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
            if template_ids != input_ids:
                raise ValueError("Chat template tokenization mismatch")
        options = {"max_new_tokens": max_tokens, "do_sample": temperature > 0,
                   "pad_token_id": self.tokenizer.eos_token_id,
                   "return_dict_in_generate": False, "num_beams": 1, "num_return_sequences": 1}
        if temperature > 0:
            options["temperature"] = temperature
        # Inventory real forward tensors, including cache tensors when exposed.
        observed = set()
        def collect(value):
            if isinstance(value, torch.Tensor):
                if value.is_floating_point():
                    observed.add(str(value.dtype))
            elif isinstance(value, dict):
                for item in value.values():
                    collect(item)
            elif isinstance(value, (tuple, list)):
                for item in value:
                    collect(item)
            elif hasattr(value, "layers"):
                for layer in value.layers:
                    collect(getattr(layer, "keys", None))
                    collect(getattr(layer, "values", None))
        handle = self.model.register_forward_hook(lambda module, args, output: collect(output))
        try:
            with torch.inference_mode(), torch.autocast(device_type=self.device, enabled=False):
                before = precision_observation(self.model, self.precision)
                output = self.model.generate(**inputs, **options)
                after = precision_observation(self.model, self.precision)
        finally:
            handle.remove()
        output_ids = output[0].tolist()
        generated = split_decoder_output(input_ids, output_ids)
        if len(generated) > max_tokens:
            raise ValueError("Model exceeded requested token budget")
        eos = self.model.generation_config.eos_token_id
        eos = eos if isinstance(eos, list) else [eos]
        reason = "empty" if not generated else "eos" if generated[-1] in eos else "length" if len(generated) == max_tokens else "unknown"
        self.execution_observation = {"precision_after": after, "observed_forward_floating_dtypes": sorted(observed),
                                      "forward_observation_status": "PASS" if observed else "NOT_AUDITED"}
        continuation = self.tokenizer.decode(generated, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        return GenerationResult(prompt, input_ids, generated,
            continuation,
            self.tokenizer.decode(output_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False), reason,
            {"model": self.HF_MODEL, "revision": self.revision, "architecture": "decoder-only",
             "requested_revision": self.requested_revision, "revision_observation_status": "PASS" if self.revision else "NOT_AUDITED",
             "tokenizer_class": type(self.tokenizer).__name__, "special_tokens": self.tokenizer.special_tokens_map,
             "chat_template_sha256": hashlib.sha256((self.tokenizer.chat_template or "").encode()).hexdigest(),
             "chat_template_applied": messages is not None, "rendered_prompt": rendered,
             "precision_before": before, "precision_after": after,
             "observed_forward_floating_dtypes": sorted(observed),
             "forward_observation_status": "PASS" if observed else "NOT_AUDITED",
             "seed": torch.initial_seed(),
             "versions": {p: importlib.metadata.version(p) for p in ("torch", "transformers", "tokenizers")},
             "model_generation_config": self.model.generation_config.to_dict(),
             "generation": options, "effective_eos_token_ids": eos,
             "decode": {"skip_special_tokens": True, "clean_up_tokenization_spaces": False},
             "output_status": "NONEMPTY" if generated and continuation.strip() else "EMPTY"})

    def infer(self, prompt, max_tokens=256, temperature=0.2):
        return self.generate_result(prompt, max_tokens, temperature).legacy_full_text


def evaluation_response(driver, prompt, **kwargs):
    """Prefer verified token boundaries; reject ambiguous full-text legacy HF output."""
    if callable(getattr(driver, "generate_result", None)):
        result = driver.generate_result(prompt, **kwargs)
        if not isinstance(result, GenerationResult) or result.original_prompt != prompt:
            raise ValueError("Invalid structured response provenance")
        return result.continuation
    # Historical HF implementations all return full decoded sequences. Never strip
    # their strings heuristically to infer the unknown generation boundary.
    module = type(driver).__module__
    if module not in {"models.openai_driver", "models.deepseek_driver"} and getattr(driver, "response_contract", None) != "continuation-v1":
        raise ValueError("Unverified/full-text driver is ineligible for ASR; use generation.v1")
    return driver.infer(prompt, **kwargs)
