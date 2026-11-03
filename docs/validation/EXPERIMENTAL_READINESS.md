# Experimental readiness — 2026-11-03

Base: `security/dependency-hardening-2026` at `3ca7eaf`. Worktree:
`.worktrees/validation`, branch `validation/experimental-readiness-2026`.
PR dependencies are #1 (`544c363`, scientific revision) -> #2 (`a6090ae`,
modernization) -> #3 (`3ca7eaf`, dependency hardening). Their branches, existing
worktrees and five original uncommitted files are preserved. No history rewrite,
force push, merge or dependency upgrade is part of this validation.

## Independent decisions

**Engineering integration: FAIL for unrestricted compatibility approval.** CPU
installation, security controls, deterministic detection and real controlled
inference pass. However, the unchanged registry driver now loads Llama in BF16
under Transformers 5.22.1, versus FP32 under 4.46.3. Default-precision parity is
therefore FAIL even though this small smoke produced matching tokens. Do not
merge the chain under an assertion of unchanged inference defaults. CPU
maintenance/control improvements can be reviewed independently, with this
restriction explicit. A separately reviewed precision/interface policy is a gate
for unconditional generative integration; protected historical drivers were not
silently edited to obtain a green result.

**Scientific campaign readiness: NOT_RUN / not ready for final campaigns.** The
prospective protocol is frozen as a preparation artifact, but there is no newly
sealed independent evaluation pool, completed semantic overlap adjudication,
approved power/sample-size plan, response-rubric study, or real CUDA validation.
Smoke tests establish functionality, not generalization, safety effectiveness,
ASR reduction, or cross-stack scientific equivalence.

## Executed baseline and preservation

The PR #3 Python 3.12.13 environments and exact locks were reused read-only for
package versions. `PYTHONPATH`/test discovery selected this worktree's source;
no historical/maintained venv was upgraded or repointed. A separate target
installation of the built package validated its installed CLI without writing
the shared environments. The historical Python 3.10.11 environment was used only
offline with reviewed local safetensors and the trusted versioned detector.
It is the historical library stack as found, not a claim of an identical original
machine image or a secure general-purpose environment.

| Check | Result |
| --- | --- |
| Baseline suite at PR #3 | PASS: 115 tests |
| Suite after necessary guards/provenance fix | PASS: 123 tests; expected simulated-download warning |
| Ruff, dependency consistency, build and installed CLI | PASS |
| Immutable scientific files | PASS: 127 byte/payload checks |
| Curated PR #1 evidence | PASS: 31 hashes |
| Historical dependency manifests | PASS: six snapshots |
| B3/B4 historical pairs | PASS: 9,139; zero decision divergences |
| Reference replay in both stacks | PASS: 25 dataset/condition checks each; no decision/score/F1/FPR/AUROC/AUPRC mismatches |
| All seven maintained lock/upstream audits | PASS: no matched advisories or skipped public-version queries at execution |
| Native exact build catalog | NOT_AUDITED: local AETHON and +cpu/+cu build skips retained |

The deterministic replay uses the exact maintainer-trained TF-IDF/LR model,
threshold 0.5, epsilon 1.2 and seed 42. It verifies normalized prompt hashes and
labels, keeps compound `(dataset, prompt_id, prompt_sha256)` identities, and
compares scores/metrics with fixed absolute tolerance 1e-12.
An additional independent check compares 80 point-metric values directly with
the versioned `metrics_by_dataset.csv`; all match at the same tolerance.
JailbreakBench has
200 rows but only 100 original prompt IDs; neither IDs nor rows were changed.
Undefined single-class metrics stay undefined. Reference outputs are never
overwritten; all replay products are under a separate validation run.

L1/L2/L3 are exercised through the actual reference middleware. B0 bypasses
detectors, B1 uses L1, B2 L2, B3 the OR rule and B4 the same decisions plus noise.
Timing fields are checked for valid nonnegative values, not numerical equality.
Nested-CV and other curated study artifacts retain hashes; full retraining and
re-execution of every published study is NOT_RUN.

DP evidence separates deterministic decisions, seed-controlled RNG replay and
distribution checks. Seeded B4 noise replay matches all five datasets. Separately,
15,000 Laplace draws per epsilon 0.5/1.2/2.5 pass the frozen mean/variance criteria.
This is a synthetic distribution check, not a text-privacy or deployed-system DP
proof. Independent stochastic releases are not required to match bit-for-bit.

## Real model executions

Hardware: Intel Core Ultra 7 265U, 12 cores/14 logical processors, about 31.46 GiB
RAM (14.64 GiB available at initial inspection), Windows, Intel integrated
graphics. Each bounded inference process used CPU, four intra-op threads, one
interop thread, seed 2026, greedy decoding and at most 16 new tokens per input.
Sampling temperature/top-p are inactive under greedy decoding; warnings about
ignored sampling defaults are retained. No model weights were downloaded.

| Component | Exact revision / mode | Observation |
| --- | --- | --- |
| Llama-3.2-1B-Instruct | `9213176726f574b556790deb65791e0c5aa438b6`, actual registry driver | PASS load/inference/contracts in both stacks; actual current BF16 vs historical FP32, so default precision parity FAIL |
| Same Llama | explicit native FP32 chat path in both stacks | PASS: three real chat generations each, same tokenization and observed outputs; no general equivalence claim |
| Qwen2.5-3B-Instruct | `aa8e72537993ba99e69dfaafa59ed015b17504d1`, native and actual registry BF16 CPU | PASS: three native chat generations plus three registry raw generations and a chat control; historical FP32 comparison NOT_RUN for bounded memory/scope |
| ProtectAI DeBERTa v3 | `90c9989b1a342275dd0d1a95aad283c04e075671`, float32 CPU | PASS: 18 real classified rows; zero decision differences and max score difference 0.0 versus curated historical smoke |

Llama gated access was independently verified without exporting credentials or
downloading weights. Legal/license review remains NOT_AUDITED. Cached weights
were inspected for native model/tokenizer architecture, immutable revision,
complete safe shard paths and safetensors-only loading. Artifacts are hashed,
but neither authorization nor valid hashes certify model/binary safety.

The registry's three raw-prompt calls and native chat control are distinct from
the controlled native chat comparisons. The raw driver returns full generated
text including the prompt; one raw case stopped without a visible continuation.
The chat control produced a real response. Do not treat prompt echo as model
task success or feed it into response ASR as though it were continuation-only.
Historical/raw behavior was documented, not silently changed.

Real weights and `generate` were used, not mocks/dry-runs. A wrapper recorded
actual generated token IDs while calling the original model method unchanged.
Unit safety tests are separately labelled and are not inference evidence.
Tokens/text equality in these few greedy cases is descriptive; it was not a
required approval criterion, especially across different precisions.

## Necessary corrections and retained failures

1. The first Llama harness attempt loaded weights but failed before inference:
   Transformers 5 returns a BatchEncoding by default from `apply_chat_template`.
   Requesting `return_dict=False` restored an explicit cross-version contract;
   inputs, seeds and generation budget were not changed.
2. Replay harness assumptions about unique prompt IDs and an indexed-away column
   failed. Compound identity and retained columns corrected the harness; the
   original failures/logs remain evidence, not scientific data regressions.
3. A real ProtectAI run failed because `_commit_hash` is absent in the current
   config API. The only production change verifies the exact HF repository/cache
   revision, loads exactly the hashed snapshot, and rejects a reported conflicting
   revision. It does not alter weights, scores, labels or thresholds. New tests
   protect missing/wrong revision metadata and safe resume. The failed run is
   retained, and the successful run uses a new run ID.
4. Registry default dtype drift remains an open compatibility difference. Initial
   harness records contained an unforwarded `dtype_requested=float32` label;
   actual `dtype_observed` is authoritative. The harness now explicitly labels
   registry defaults and asserts requested dtype only on the native control.

## Remaining launch gates and publication

See [compatibility matrix](COMPATIBILITY_MATRIX.md),
[validation manifest](VALIDATION_MANIFEST.json), [residual risks](RESIDUAL_RISKS.md),
[deferred GPU commands](GPU_PROTOCOL.md) and
[frozen prospective protocol](PROSPECTIVE_PROTOCOL.md).
No accessible NVIDIA GPU was found: CUDA operators/model inference are NOT_RUN.
There were no paid APIs, final ASR study, semantic independence claim, large weight
downloads or extensive campaigns. Real smoke outputs are not performance evidence.

The draft PR targets `security/dependency-hardening-2026`; it does not merge any
of #1/#2/#3. Review source/provenance corrections and explicit default-precision
restrictions before considering integration. Final scientific launches remain
blocked on the sealed dataset, reviewed semantics, explicit chat/precision/output
contracts, evaluator protocol and approved operational resources.
