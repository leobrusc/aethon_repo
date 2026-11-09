# SRC2-REV-04 — witness verification-time claim binding

## Recovery and provenance

- Immutable remote source: PR #37 HEAD `1aec251ea6b8fa4d89a9aa278f4e0dd8dd4311aa`.
- The unpublished review worktree `.worktrees/src02-final-safety-review-v1` remains inaccessible due to `CreateProcessAsUserW failed: 5`. Its uncommitted files and hashes have **not** been retrieved or verified.
- New tests `tests/test_src02_witness_proof_integrity.py` are **RECONSTRUCTED** from the reported review findings; they are not claimed to be byte-identical to the unpublished tests.
- Work took place through the connected GitHub API, without invoking the blocked Windows runner, touching the original worktree, provisioning any service or changing any scientific dataset.

## Root cause and repair

The model's trusted `witness_verify` transition set `witness_response_valid=True` without persisting the exact set of claims it validated. `witness_reconcile` and `classify` subsequently relied on that flag and on incomplete validation of signer, signature, freshness, identities and epochs. A synthetic replacement of previously verified evidence could therefore leave `COMMITTED` accepted.

The remediation introduces `witness_verified_binding`, an immutable tuple of the verified response and request claims. `witness_verify` and the existing abstract trusted compare-and-advance result record this tuple. Every `validate()` call compares current claims against this snapshot and independently checks signature, signer identity, freshness, revocation, run/operation/policy/revocation binding, sequence/head and acknowledged operation. Since `apply()` calls `validate()` before transitions and `classify()` also calls `validate()`, proof mutation is rejected even after reconciliation or acknowledgment.

This is an **abstract modeling invariant**, not cryptographic authentication or protection against code with arbitrary interpreter-memory access. An adversary who can rewrite both the proof and its trusted snapshot lies outside the synthetic API-misuse model.

## Regressions and status

The new tests mutate signer, signature, freshness, revocation validity, witness identity, request identity, run/operation, epochs, sequence/head and committed operation. They check the VERIFIED, RECONCILED and acknowledged checkpoints and preserve successful legitimate commits with and without a witness. Witness service unavailability after a historically valid acknowledgment does not retroactively invalidate that result; fresh recovery operations remain subject to a current query.

Historical vulnerable test files are untouched; the tests here are independent reconstructions, not modifications of prior evidence.

**Remediation status:** `SRC02_WITNESS_REMEDIATED_PENDING_REVIEW` only when CI regression results support it. Until then, `SRC2-REV-04 OPEN`. SRC2-REV-01/02/03 remain subject to regression; SRC2-REV-05/06 are PARTIAL.

**Not authorized:** Linux/Windows native backend, witness service, root bootstrap, inference, deployment, release, dependencies or scientific-data changes.

Keep `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED`, all eight operational gates `PENDING`.

## Evidence classification

No new independent byte verification of historical 127 protected files, 31 evidence hashes, six manifests, 9,139 B3/B4 pairs, five LFS objects or 80 metric values is claimed by this GitHub-only code change. All these historical results remain unchanged; CI evidence must be checked separately and reported according to its actual scope.
