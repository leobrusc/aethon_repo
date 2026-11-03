# Residual risks and operational limits

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
