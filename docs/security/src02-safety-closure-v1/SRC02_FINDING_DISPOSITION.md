# SRC-02 Finding Disposition — Phase 7E

## Proposed status pending independent review

| Finding | Proposed classification | Evidence | Residual limitation |
|---|---|---|---|
| SRC2-REV-01 | `REMEDIATED_SPEC_MODEL` | Response-less pre-dispatch trace rejects before object/head; response commit requires exact observed, verified and durable continuation bound to run/slot/op/manifest/config. | No provider or native persistence implementation. |
| SRC2-REV-02 | `REMEDIATED_SPEC_MODEL` | Lease IDs, holder, epoch, authority, transfer generation, expected head and revocation epoch are represented and compared atomically at abstract publish; stale A rejected after B transfer. | One in-memory abstract authority; no OS-backed enforcement proof. |
| SRC2-REV-03 | `REMEDIATED_SPEC_MODEL` | Marker is at-most-once; crash after possible dispatch without durable response becomes `INTERRUPTED_UNKNOWN`; no inference retry. Persistence retry is same operation/digest. | No real provider idempotency or durable crash testing. |
| SRC2-REV-04 | `REMEDIATED_SPEC_MODEL` | Recovery cannot clear on unavailable witness; only authenticated/fresh/bound/consistent evidence can reconcile. | Authentication and freshness are modeled trusted outcomes, not implemented crypto/service controls. |
| SRC2-REV-05 | `PARTIAL` | Existing root bootstrap specification retained. | No native signed root receipt, trust anchor, restart revocation or executable proof. |
| SRC2-REV-06 | `PARTIAL` | Existing candidate Windows profile retained. | No Windows native adapter or platform validation. |

## Overall proposed disposition

`SRC02_SAFETY_REMEDIATED_PENDING_REVIEW`: the three reproduced abstract defects are addressed by the transition relation and synthetic acceptance tests, subject to independent review. This does not mean all six findings are fully implemented, or that a native backend is ready. Findings 05/06 remain partial. Keep `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED`, and all eight gates PENDING.

## Review request focus

Independently challenge (1) whether response provenance and digest binding are sufficient in the abstract state machine, (2) whether witness validation can be reached without the trusted verification event, (3) whether all publish paths check the same serialized lease authority and revocation generation, and (4) whether bounded state deduplication remains congruent after the state schema change.

## Phase 7E local validation

| Check | Result |
|---|---|
| Focused SRC-02 model suite | PASS — 33 tests |
| Full pytest | 440 passed, 1 failed (441 total): legacy Git-for-Windows OpenSSL subprocess denied signal-pipe creation (`Win32 error 5`, return code 3221225794); no policy workaround or mock used |
| Ruff | PASS |
| `pip check` | PASS — no broken requirements |
| Protected scientific inventory | PASS — 127 files against baseline `544c363c19a08574d30e7e2c064a78ce1bdfb601` |
| Research evidence hashes | PASS — 31 |
| Historical dependency manifests | PASS — six preserved |
| B3/B4 read-only recalculation | PASS — 9,139 pairs, labels equal, zero decision mismatches; CSV SHA-256 `914901a1ed82836dfb42567cb376ec90f20459d1ad0f9b12d72568f4bfca202a` |
| Git LFS | PASS — `git lfs fsck` |
| Repository publication guard | PASS |
| `git diff --check` | PASS |
| Offline preflight | `PILOT_BLOCKED`, `executed=false`, all eight gates PENDING (expected fail-closed result) |
| GitHub Actions run `42542931617` on implementation commit `eb3544fed208d5ab9e6e92aeedcdc0fd64184fff` | PASS — Linux, Windows, and research/GPU audit jobs SUCCESS; GPU inference NOT_RUN |

The independent historical reproduction remains excluded from default test
collection and byte-preserved in the parent Git object. Its prior vulnerable
assertions are forensic evidence, not acceptance assertions.
