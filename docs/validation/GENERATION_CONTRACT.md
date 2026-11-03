# Explicit inference contracts v1

New registry-created local HF drivers use `aethon.precision.v1` and
`aethon.generation.v1`. Reference configuration: `configs/generation_v1.json`.
CPU/FP32 is the fixed default; neither device availability nor checkpoint dtype
selects a different precision. No lock or historical driver was changed.

## Precision

The preserved `models.hf_causal_driver` CPU loader omits `torch_dtype`.
In installed Transformers 5.22.1, `modeling_utils.py:4075–4107` resolves an
omitted dtype to `auto`; the checkpoint/config dtype is then consulted by
`_get_dtype` (around line 817). The local Llama config declares BF16. The earlier
4.46.3 stack loaded FP32 instead. This is a real default difference, not a
change to weights. The initial FAIL evidence remains unchanged.

The new loader passes `torch_dtype` explicitly in both HF versions. This
backwards-compatible keyword is deprecated in HF5; the warning is retained.
There is no error-to-fallback conversion.

| Requested device / storage dtype | precision.v1 policy |
| --- | --- |
| CPU / FP32 | Supported, explicit |
| CPU / BF16 | Requires a real BF16 matrix-operator probe; does not establish native acceleration |
| CPU / FP16 | Rejected; partial CPU operator support is outside this version's policy |
| CUDA / FP32 or FP16 | Requires accessible CUDA; real GPU execution remains NOT_RUN here |
| CUDA / BF16 | Requires CUDA BF16 capability and a successful BF16 operator probe |
| auto / other dtype / other device / unknown version | Rejected |

All floating parameter elements and devices are checked before and after
generation. A mismatch raises an error. Floating buffers are inventoried by
name/dtype/device separately: e.g. FP32 rotary buffers can coexist with BF16
parameters. Forward hooks observe exposed logits/cache floating dtypes;
unexposed internal arithmetic is not audited. Inference runs with gradients and
device autocast disabled. Parameter storage dtype is not a claim that all
accumulation, buffers, kernels or execution states use one dtype.

## Output and evaluation boundary

`GenerationResult` carries a version, original user prompt, effective input IDs,
actual generated IDs (including EOS), decoded continuation, legacy full text,
stop reason and model/tokenizer/precision/generation metadata. It supports
`to_dict()`, `to_json()` and `from_json()`; unknown versions/invalid IDs are
rejected. Metadata includes the rendered chat input, template hash, special
tokens, revision observation status, effective generation configuration, actual
torch seed and library versions. Review public exports for sensitive content.

v1 supports single-request decoder-only models. It verifies the exact generated
sequence input prefix and slices IDs at its token length. Encoder-decoder models
are rejected explicitly; their decoder boundary requires a separate contract.
Chat rendering is opt-in through `messages`; its final user content must equal
the original prompt. Tokenized rendering must equal template tokenization;
special tokens are not added twice. Decoding disables token cleanup explicitly.

Stop reasons are `eos`, `length`, `empty` or `unknown`. EOS takes precedence at
the token limit. An EOS-only sequence has generated IDs but empty visible
continuation; no returned new IDs is also represented explicitly. An unknown
stop is not relabeled as EOS. Greedy requests omit inactive temperature;
beam/return counts are fixed to one. The remaining model generation defaults
are recorded in full and must be frozen separately for a scientific protocol.

`.infer()` keeps the full-text string interface for legacy consumers.
`evaluation_response()` uses `generate_result().continuation` for benchmark,
paired-response and LLM-judge paths. Ambiguous legacy/full-text drivers fail
closed; their text is never heuristically stripped. Existing API drivers have
continuation semantics; injected adapters must explicitly declare
`response_contract = "continuation-v1"`. This declaration is an adapter contract,
not a security certification. Direct judge string arguments must already be
responses, not raw pipeline results. Empty responses are not evaluated as ASR.
Benchmark manifests also record loaded and last-executed precision observations.

## Usage and reproduction

```python
from model_registry import get_model_driver
driver = get_model_driver("llama-3.2-1b-instruct",
    model_id="/reviewed/cache/snapshots/9213176726f574b556790deb65791e0c5aa438b6",
    revision="9213176726f574b556790deb65791e0c5aa438b6",
    device="cpu", precision="float32")
result = driver.generate_result("Reply with READY.", max_tokens=16,
    temperature=0, messages=[{"role": "user", "content": "Reply with READY."}])
response_for_evaluation = result.continuation
legacy_full_text = result.legacy_full_text

# Explicit historical opt-in; immutable original module remains importable.
legacy = get_model_driver("llama-3.2-1b-instruct", contract_version="legacy-v1")
```

New local loading is offline, native-code only, `trust_remote_code=False`,
`use_safetensors=True`; it never downloads missing weights. Review exact
artifacts beforehand. Hashes establish identity, not universal model safety.
Remote cached references without observable exact revision are marked
NOT_AUDITED, not silently treated as pinned. The bounded validation runner
requires the reviewed exact local revisions and hashes every artifact.

Re-run `scripts/validate_generation_contract.py --help` using the unchanged PR3
environment, then select a new output path, local snapshot, dtype and environment
label. Run the same script with the historical interpreter for the controlled
FP32 comparison. It performs three frozen chat cases plus two real raw-interface
calls, max 16 tokens each. The legacy-inspection runner explicitly selects
`legacy-v1`; it cannot be mistaken for the new default.

Observed identical IDs on three Llama cases demonstrate this bounded contract
comparison. They do not establish statistical equivalence or general scientific
performance. See the machine-readable manifest for actual runs and hashes.
