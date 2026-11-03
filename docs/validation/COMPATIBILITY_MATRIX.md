# Compatibility matrix — explicit contracts update

Current code: `5b44560`. Contracts: `aethon.precision.v1` and
`aethon.generation.v1`. New evidence: [contracts-v1/](contracts-v1/).

| Control | Status | Evidence / scope |
| --- | --- | --- |
| Llama explicit FP32, historical and maintained libraries | PASS | Same reviewed weights; three real chats and two raw calls per environment |
| Llama bounded contract comparison | PASS | All three input/generated-ID sequences, continuations and stop reasons match; no statistical equivalence claim |
| Qwen 3B explicit BF16 CPU | PASS | Real load, three chats and two raw calls; parameters/buffers/forward observations recorded |
| FP32 default, supported BF16, incompatible precision, parameter drift | PASS | 18 synthetic regression tests in both environments; BF16 also exercised by real Qwen |
| Templates, token boundaries, prompt echo, EOS-only empty generation | PASS | Structured result and safe evaluation routing; ambiguous legacy text rejected |
| Legacy string interface and structured serialization | PASS | Full text retained separately; generation.v1 round-trip |
| Full maintained suite / Ruff / pip check | PASS | 141 tests; no dependency conflicts |
| Scientific integrity and historical dependency manifests | PASS | 127 files, 31 evidence files, six manifests; all original locks unchanged |
| B0–B4 replay, both environments | PASS | 9,139 prompts, 25 condition/dataset comparisons each, zero mismatches |
| Installation and CLI | PASS | Code-only target install, wheel, seven help commands, two-row dry-run |
| Seven locked upstream security queries | PASS | Zero matched advisories; no suppressions |
| Exact PyTorch binary catalog / universal model trust | NOT_AUDITED | Scanner skips retained; receipt/hash is not a safety audit |
| Historical stack for unrestricted untrusted use | FAIL | Existing vulnerable stack retained only for controlled reproduction |
| Actual CUDA FP16/BF16 execution | NOT_RUN | No NVIDIA GPU accessible; policy unit tests are synthetic |
| Qwen historical comparison / prospective ASR / statistical equivalence | NOT_RUN | No expanded scientific campaign |

Engineering decision: **PASS for scoped CPU integration of the explicit
contracts**, subject to review of dependent PRs. Scientific readiness for final
campaigns: **NOT_RUN**. The legacy default discrepancy remains a historical
fact; new registry executions no longer use it. See
[GENERATION_CONTRACT.md](GENERATION_CONTRACT.md) and the validation manifest.

## Initial PR #4 matrix — preserved assessment of legacy defaults

The following rows describe the earlier implementation before the explicit
contracts. Its FAIL/NOT_AUDITED evidence is retained, not relabeled retrospectively.

PASS is scoped to the executed check. FAIL, NOT_RUN and NOT_AUDITED are retained;
passing hash checks does not certify safety or scientific equivalence.

| Component / contract | Historical | Maintained | Decision / limit |
| --- | --- | --- | --- |
| Canonical scientific inputs/results | Frozen reference | 127 hashes + 31 evidence hashes PASS | PASS, no historical changes |
| Dependency snapshots | Six original manifests | Byte hashes PASS | PASS; historical vulnerabilities retained |
| L1/L2/B0–B4 reference decisions | 9,139 prompts | Same 9,139 prompts, all five conditions | PASS; compound identities, no retuning |
| Scores, threshold, F1/FPR/AUROC/AUPRC | Frozen source | Atol 1e-12 comparisons | PASS; undefined metrics remain undefined |
| L3 decision invariance | B3/B4 equal | B3/B4 equal | PASS; noise is not text privacy |
| L3 fixed-seed replay | Recorded seed 42 | Same seed/config | PASS; not required for independent stochastic releases |
| L3 distribution | Theoretical Laplace | Frozen 15,000-draw checks | PASS, synthetic/statistical only |
| Llama cached load / raw registry inference | FP32, real | BF16 automatic, real | Functional PASS; default precision equivalence FAIL |
| Llama native chat / explicit FP32 | Real controlled run PASS | Real controlled run PASS | Tokenization and observed outputs matched; no general scientific equivalence claim |
| Chat tokenizer return format | List default | BatchEncoding default | Explicit return_dict=False PASS in harness; initial failure retained |
| Raw driver output | Full prompt + generation | Same contract | PASS contract; continuation-only/ASR interface NOT_AUDITED for a new campaign |
| Qwen 3B native and registry | NOT_RUN | BF16 CPU, real native + registry PASS | Three cases each plus registry chat control; historical FP32 comparison NOT_RUN |
| ProtectAI pinned smoke | Curated 18-row evidence | Real 18-row smoke | PASS after provenance correction; no efficacy estimate |
| ProtectAI config revision field | Present in former loading route | May be None | Verified snapshot proof PASS; conflicting metadata FAIL closed |
| Maintained dependency advisory queries | Historical findings FAIL | Seven locked upstream queries PASS | Does not audit exact binary payloads |
| CPU wheel source/hash receipt | Old evidence preserved | Official receipt PASS | Identity/provenance only |
| CPU/CUDA exact build catalog | NOT_AUDITED | NOT_AUDITED | Native skips preserved, not safety approval |
| NVIDIA operators/model inference | NOT_RUN | NOT_RUN | Only Intel GPU accessible; deferred protocol provided |
| Prompt Guard / other large cached targets | NOT_RUN | NOT_RUN | No gated download or unnecessary broad campaign |
| Independent final dataset / semantic review | Previously inspected pool unsuitable | New pool NOT_RUN | Final scientific evaluation blocked |
| Response ASR / human evaluation | Historical limitations retained | NOT_RUN | Benign smoke is not ASR evidence |

Engineering verdict: **FAIL for unrestricted/default-equivalent integration**;
CPU controls and explicit inference paths are proven within their scope.
Scientific verdict: **NOT_RUN for final campaigns**, pending prospective launch
gates. See the manifest for exact models, versions, files, attempts and comparisons.
