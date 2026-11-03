# Compatibility matrix

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
