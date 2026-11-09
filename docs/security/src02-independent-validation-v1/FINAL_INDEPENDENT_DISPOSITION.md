# Final Independent Disposition

## Findings and classifications

- SRC2-REV-01: `OPEN`
- SRC2-REV-02: `PARTIAL`
- SRC2-REV-03: `OPEN`
- SRC2-REV-04: `OPEN`
- SRC2-REV-05: `PARTIAL`
- SRC2-REV-06: `PARTIAL`

## Independent classifications

- SRC-02 contract: `SRC02_CONTRACT_REMEDIATION_REQUIRED`
- Scientific asset byte integrity: `SCIENTIFIC_ASSETS_INTACT`
- Linux readiness: `LINUX_CONTRACT_REFINEMENT_REQUIRED`

“Assets intact” means that the bytes match the protected hashes and LFS objects verify. It does not assert that every asset parses: `hf_red_team_attempts.jsonl` fails JSONL parsing in its protected canonical bytes. No repair is authorized or recommended as part of this review.

## Basis

The finite explorer's history deduplication had no frontier mismatch among 15,941 reachable aliases at depth 12. That bounded result is favorable but not a proof for arbitrary states. Two independent counterexamples remain: a response-less, pre-dispatch operation can reach `COMMITTED`; and an unavailable witness query can clear `recovery_blocked` and report `RECONCILED` without reading the witness. Thus the six-finding remediation is not independently closed.

CI runs `42412776565` and `42413419166` passed all three jobs; the latter included the requested PR #35 HEAD. Local full pytest had one environment-blocked OpenSSL subprocess test (`437 passed, 1 failed`); the failure is recorded, not masked. Four JSONL assets parse; the fifth has invalid canonical syntax despite matching its expected hash.

## Required next action

Correct SRC2-REV-01/03 so a committed object requires proof of actual dispatch, observed response, and durable response provenance. Correct SRC2-REV-04 so witness unavailability cannot reconcile or clear the block. Add negative tests for both counterexamples and rerun bounded alias-congruence checks. Add lease identity/authoritative serialization state to the model for SRC2-REV-02. Separately, open a governed dataset-quality issue for the invalid JSONL bytes; preserve the historical file and hash while any corrected derivative receives a new identity and provenance.

No classification authorizes a native backend. Preserve `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED`, and all eight gates `PENDING`.
