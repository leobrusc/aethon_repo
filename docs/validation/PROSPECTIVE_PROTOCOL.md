# Independent prospective protocol — frozen v1

Status: PREPARED, final evaluations NOT_RUN. This protocol must be committed and
hashed before recruiting/sealing any final evaluation pool. No historical/smoke
result is promoted into prospective performance evidence.

## Threat model and populations

Evaluate an attacker who controls a user message or untrusted retrieved/tool
content, attempting to override application instructions, extract synthetic
protected canaries, or misuse explicitly sandboxed tools. Separate direct user
jailbreaks from indirect injection. No real secrets, credentials or unsafe tools.
Retain independent legitimate-task controls with matched languages/domains.
Document what AETHON does not protect: model/host compromise, arbitrary trusted
code execution, and confidentiality of text merely because L3 adds count noise.

## Independent dataset and sealing gates

Acquire a licensed, prospectively collected pool not used for training, threshold
selection, prompt engineering or previous inspection. Existing 9,139-row data and
the tiny readiness inputs are reference/smoke only and are excluded as final data.
No new independent pool is claimed to exist in this delivery.

Before sealing, assign source/position-based IDs, raw/normalized hashes, license,
collection time, threat family, provenance and label-review status. Compare every
candidate against all training, historical reference and readiness inputs using
exact normalized matches, lexical near duplicates and pinned semantic embeddings.
Two reviewers adjudicate suspicious semantic/family overlaps and conflicting
labels; report disagreements and excluded IDs. Embedding similarity alone does
not establish independence. Keep attack-family groups together. Reserve separate
development data; keep final labels hidden from model/threshold selection.

Seal the manifest, data hashes, reviewer decisions, inclusion probabilities and
sample-size/power justification before final runs. Numerical sample size and
power depend on predeclared precision/effect goals and pilot variance from the
development pool; these remain launch gates, not post-hoc choices on final data.
No final campaign is authorized until these fields are concrete and reviewed.

## Frozen baselines and execution

Preserve B0–B4 and L1/L2/L3. Use the historical detector as a frozen reference;
evaluate the independent research variant under its own name. Include the pinned
ProtectAI and Prompt Guard baselines only with verified class meanings, revisions
and comparable threat scope. Contemporary baseline selection must be reviewed
and frozen before sealing; injection detectors are not assumed to cover every
jailbreak family. Freeze target LLM/tokenizer revisions, templates, decoding,
seeds, dtype, hardware, contributions and DP epsilon/composition rules.

Use paired prompt identities across systems. Retain technical failures, missing
judgments, truncations and eligibility information. Log implementation/lock/data
hashes, run IDs, start/end time, hardware, manifests and safe resume state. Store
raw text/responses privately with custodian, ACL and deletion date; export only
reviewed aggregates and non-sensitive evidence. Never rerun/select outcomes merely
to improve metrics. Extensive GPU/paid/download campaigns require separate approval.

## Endpoints and inference

Prompt detection: per-source/family F1, FPR, AUROC, AUPRC, confusion counts and
coverage, with threshold policy frozen on development/training only. Mark metrics
undefined for single-class populations; report micro and macro separately.
Response ASR requires actual LLM inference, objective-specific rubrics, eligibility
denominators, missing-judgment bounds, two blinded human reviewers and agreement.
Report legitimate-task preservation separately. Smoke outputs receive no ASR score.

Predeclare paired correctness/McNemar tests, effect sizes and stratified/grouped
paired bootstrap confidence intervals (95%, seed 2026, 10,000 replicates), with
attack-family/source clustering and limitations. Freeze a primary comparison and
multiple-comparison policy before final execution. Retain stochastic generation
replicates only under a predeclared design; do not demand cross-stack token equality.

Launch checklist: dataset/semantic review SEALED, power/sample size SEALED,
baselines/target weights FROZEN, rubrics/reviewers READY, infrastructure/auth
VERIFIED, privacy/cost controls APPROVED. Until then scientific campaign readiness
is NOT_RUN/conditional, regardless of successful engineering smoke tests.
