# Independent final review — SRC2-REV-04

## Baseline and scope

- Reviewed PR #40 HEAD: `41f513696383c4a1b553cba40865f8fe8e93eaa6`.
- Source unchanged in this review; independent test-only diff.
- PR #39 negative counterexample (unchanged model) failed in both Linux and Windows, `496 passed, 1 failed` — the expected safety rejection did not occur.
- PR #40 fix run `42551027708`: 3/3 jobs SUCCESS. Linux 497 passed, Windows 497 passed, one expected warning per job.
- Historical response-proof mutation tests from PR #38 are preserved.
- This review's new tests independently challenge both policy downgrades and individual witness evidence changes at VERIFIED, RECONCILED and COMMITTED checkpoints, plus valid policy profiles and bounded alias-frontier consistency.

## Invariants under evaluation

1. `witness_required == bound_witness_required` for every accepted synthetic State, independent of acknowledgment.
2. A frozen verifier claim tuple matches the current request/response fields whenever `witness_response_valid` is asserted.
3. Witness authentication, signer identity, freshness, revocation, run/op/policy/epoch and sequence/head are checked by `validate()` and `classify()`.
4. A valid acknowledged commit is a historical fact that does not require the remote witness service to remain online continuously.
5. Legitimate no-witness histories remain valid only when their initial policy explicitly permits it.

## Trust boundary and residual risk

The witness policy binding is initialized by `State.__post_init__` from a Python constructor argument. This is an **abstract fixture invariant**, not a signed independent grant. An adversary able to forge the full state, both policy fields, or the verification snapshot is outside the modeled API-level adversary. Native root/bootstrap, authenticated policy issuance, secure persistent verification receipts, OS-backed fencing and real witness service remain NOT_IMPLEMENTED/NOT_VALIDATED.

Full formal verification, cross-process guarantees and backend authorization are not inferred from finite tests. Historical Windows worktree artifacts remain inaccessible; no identical-byte preservation is claimed. Scientific dataset bytes were not modified. The existing canonical `hf_red_team_attempts.jsonl` format issue is independent.

## Preliminary disposition (before review CI)

`SRC2-REV-04 PENDING_FINAL_INDEPENDENT_TEST_RESULTS`. Do not interpret this report as a PASS until the review branch CI shows all new adversarial tests passing on Linux and Windows. If CI succeeds, classify `SRC02_ABSTRACT_SAFETY_CLOSURE_VALIDATED` **only** within the declared synthetic API/State model and list the limitations above. If it fails, record `SRC02_ABSTRACT_SAFETY_REMEDIATION_REQUIRED` with the failing trace.

SRC2-REV-01/02/03: CLOSED_SPEC_MODEL, subject to the new regression run.
SRC2-REV-05/06: PARTIAL, no native claims.

Permanent states: `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED`, eight gates `PENDING`.
