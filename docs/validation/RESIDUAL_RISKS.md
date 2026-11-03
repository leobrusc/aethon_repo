# Residual risks and operational limits

## Current disposition after generation.v1

| Finding | Status | Disposition |
| --- | --- | --- |
| Implicit Llama BF16 in new executions | PASS remediation | Registry now uses explicit precision.v1 CPU/FP32; both-stack real comparison passed. Legacy default behavior remains only behind explicit opt-in |
| Prompt-prefix contamination in ASR paths | PASS remediation | Continuation extracted by token boundary; full text kept separately; ambiguous legacy outputs rejected. Direct judge strings must already be response-only |
| Parameter precision drift | PASS control | Every floating parameter checked before/after generation; buffers and exposed forward/cache dtypes inventoried separately |
| Uniform internal arithmetic precision | NOT_AUDITED | No claim about every accumulation/kernel/hidden execution state; forward hooks observe exposed tensors only |
| Generation configuration beyond precision | PASS recorded, protocol-dependent | Greedy/sampling choice and token budget explicit; complete model generation config recorded. Future scientific campaigns must freeze remaining parameters and seed policy |
| Model/adapter trust and license | NOT_AUDITED universally | Local reviewed safetensors, no remote code; hashes and adapter continuation declarations do not certify safety or legal compliance |
| Exact torch CPU/CUDA catalog | NOT_AUDITED | Official receipts and seven upstream advisory queries PASS; native skips retained |
| Historical environment vulnerabilities | FAIL for unrestricted use | Retained for reproduction; existing offline benign controlled smoke only, no in-place upgrade |
| CUDA FP16/BF16 and other architectures | NOT_RUN | No accessible NVIDIA GPU; encoder-decoder explicitly rejected by generation.v1; no multi-device/quantized guarantee |
| Qwen historical/FP32 compatibility | NOT_RUN | Only current BF16 CPU tested within available resources |
| Independent dataset, semantic overlap review, response ASR and statistical equivalence | NOT_RUN | Existing prospective launch gates unchanged; tiny benign smoke cannot establish effectiveness |
| Legacy full-text reproduction | PASS preservation | Original drivers and raw evidence unchanged. `.infer()` remains a string/full-text interface; decoder cleanup is explicitly versioned in new runs, not claimed identical to every old default |

Recommended integration: approve the scoped engineering changes after reviewing
the dependent PR chain and CI; keep scientific campaign gates open. No universal
security approval, risk waiver, automatic merge or production authorization is
implied. The prior manifest is preserved at
[evidence/validation-pre-contract-v1.json](evidence/validation-pre-contract-v1.json).

## Initial PR #4 risks — preserved pre-remediation assessment

Rows below describe the earlier legacy-driver assessment. Current remediation
and residual status are above; historical failures are not retroactively PASS.

| Finding | Status | Disposition |
| --- | --- | --- |
| Llama registry default precision changed FP32 -> BF16 | FAIL for default parity | Retained as a real compatibility difference; use a reviewed explicit precision contract before unconditional integration/campaigns |
| Native FP32 model functionality | Executed separately | Does not repair or hide the unchanged registry default |
| Legacy driver echoes input in generated_text | Existing contract; new response-study suitability NOT_AUDITED | Freeze chat rendering and continuation extraction before ASR; no silent historical behavior change |
| Transformer 5 tokenizer return API | Initial harness FAIL, corrected | Explicit return_dict=False; failed attempt retained |
| ProtectAI revision metadata absent | Initial real-run FAIL, corrected | Exact repo/snapshot verification and hashed local loading; conflicting reported hashes still rejected |
| Historical vulnerable packages | FAIL for general untrusted use | Only reviewed offline artifacts and tiny fixed tests used; no upgrade in place or security certification |
| Exact torch CPU/CUDA binary catalogs | NOT_AUDITED | Official URL/hash checks and public-version queries remain separate evidence |
| Model/serialization trust | NOT_AUDITED as a universal guarantee | Native architectures, no remote code, reviewed safetensors and trusted maintainer-trained detector only; hashes prove identity, not safety |
| Model legal/license review | NOT_AUDITED | Gated access check verifies repository access, not a legal audit |
| CUDA execution and GPU inference | NOT_RUN | No NVIDIA adapter/driver interface accessible locally; no CUDA environment installed here |
| Qwen historical FP32 route | NOT_RUN | Bounded memory/scope; maintained BF16 native/registry success is not proof of historical FP32 parity |
| Full nested/retraining/prospective studies | NOT_RUN | Only immutable artifacts/replay are verified; no new generalization claim |
| Semantic duplicate review / independent sealed dataset | NOT_RUN | Exact/lexical checks alone do not establish independence |
| Response ASR, human rubrics, legitimate-task preservation | NOT_RUN | No objective-specific response judgment or effectiveness claim from smoke outputs |
| Cross-stack latency comparison | NOT_AUDITED as an experiment | Cache state, loading, dtype and execution order differ; recorded seconds are descriptive diagnostics |

No blanket risk acceptance is implied. Engineering tests and real model execution
support a scoped CPU assessment; they do not authorize production deployment or
final scientific conclusions. The recommended merge decision is conditional:
review the dependency chain and source provenance fix, then resolve/version the
precision and response-output contracts before unrestricted generative integration.
There is no automatic merge and no attempt to modify protected historical drivers,
labels, scores, thresholds or scientific outputs merely to make all rows PASS.
