# Scientific validity review

Reviewed protocol parent: PR #15 `1c6fc01edef58cc1565a7c233c7a23722a4d72a1`.
Implementation: PR #16 `aa6d171d82961aa297808c24ac602076abf47883`.
Verdict: **REMEDIATION_REQUIRED; PILOT_BLOCKED**. Synthetic checks are software
evidence only; no prospective ASR, efficacy or power estimate was produced.

| Baseline | Frozen definition | Implementation assessment |
| --- | --- | --- |
| B0 | No defense | Historical middleware bypass |
| B1 | L1 rules | Unchanged heuristic |
| B2 | L2 classifier, historical threshold | Hash-pinned detector/middleware |
| B3 | L1 OR L2 before generation | Historical combined decision, not post-response defense |
| B4 | Same B3 decision plus noisy count | Epsilon 1.2, detector/DP seed 42; no calibrated cascade substitution |

`FrozenDefenses` wraps existing middleware rather than reinterpret earlier informal
baseline names. Code review finds this mapping consistent with the frozen protocol.
No real target inference was used to establish it. Generation binds target and
tokenizer revisions, template digest, effective configuration, seed 2026,
CPU/float32, decoding options and prompt/generated IDs. The collector independently
decodes the generated interval before passing continuation alone to the judge;
the prompt-echo/drift tests reject mismatches. Task objective and rubric are trusted
context; behavioral resistance of an actual human/model judge remains unaudited.

The matrix represents all 24 cases across five arms, including blocked, pending,
error, missing, truncated and interrupted outcomes. IDs hash structured provenance;
duplicate sources/scenarios are rejected. Matched attack/control task context is
checked. Deterministic schedule and durable intent avoid ordinary accidental
re-execution after interruption. External full-snapshot rollback is a separate
trust limitation. No ASR aggregator silently discards failed slots: this collector
does not compute ASR. Future analysis must retain all eligible denominators and
unresolved bounds under the frozen rubric.

B4 reuse requires B3 decision/score equality, full request fingerprint equality and
a validated B3 response. Missing or incompatible B3 output suspends rather than
inventing a new B4 draw. Shared responses and all arms remain dependent; 120 slots
are not 120 independent observations. B4 reused evaluation is not a second vote.

SCI-01 demonstrates that the exact three-family/four-pair allocation is absent
from the inventory validator. Source licensing, exact/semantic exclusions, prior
pool coverage and true family membership require external review; a signed seal
does not independently prove them. Training/reference/smoke/public fixture/pilot
material must remain excluded from the final holdout. Independent raw dataset
digest and pretraining contamination remain NOT_AUDITED.

SCI-02 demonstrates that the injected evaluation interface accepts one unassigned
judge and arbitrary evidence reference as completed. The protocol requires two
independent raw votes and separate adjudication with case/rubric/evidence lineage.
Default CLI deliberately leaves judgments pending; retain that safe default until
the complete review interface is enforced. Detection decisions, response attack
success and legitimate task utility must remain distinct fields and denominators.

Clarifications needed before pilot: define technical-error suspension denominator
explicitly (current code uses all terminal slots, including blocked/reused), and
distinguish collection completion from scientific adjudication completion. These
are methodological ambiguities, not additional proven security bypasses.

Historical continuity is assessed separately in review-evidence: 127 protected
files, 31 indexed artifacts, six historical manifests, 9,139 B3/B4 pairs, 80 metric
values, five hydrated LFS payloads and five original local files. Historical replay
does not measure prospective efficacy. Next scientific phase remains remediation
review and independent private inventory/rubric governance, followed only by a
separately authorized bounded feasibility pilot; final campaign is not authorized.
