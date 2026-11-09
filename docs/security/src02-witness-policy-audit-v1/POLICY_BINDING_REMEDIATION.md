# SRC2-REV-04 — immutable witness policy binding remediation

## Evidence and ancestry

- PR #38 reviewed HEAD: `7b8a0efac4840713b7f381ab6ef68f03ed7316f6`.
- Independent review PR #39: `abd7ea1db106c7b032d9dce5d378470cb0d1d97e`, with negative tests for policy downgrade.
- This branch is based on PR #39 and retains its independent tests unchanged.

## Defect and fix

The immutable `State` previously included an unbound `witness_required` field. At the synthetic snapshot boundary, `dataclasses.replace` could change that field after a witness-protected operation had already committed. `classify()` evaluated witness proof requirements conditionally on the altered field. An adversarial review test also clears witness bookkeeping to demonstrate policy weakening.

Added `bound_witness_required` as the initial launch-policy value. `State.__post_init__` initializes that binding for a fresh synthetic fixture; `dataclasses.replace` retains it. `validate()` always checks the effective policy against this frozen binding, regardless of operation state, including post-acknowledgment classification. Witness proof snapshots also bind both policy fields.

This is an abstract model-level authorized policy integrity guarantee, **not** a trusted OS or cryptographically signed launch grant. An attacker with arbitrary Python access who can rewrite both fields can forge a synthetic State. The native design must bind witness policy to a separately authenticated immutable launch grant, which remains unimplemented.

## Acceptance

- PR #39 negative tests must reject post-commit policy changes.
- Existing valid witness-required and witness-optional histories must remain `COMMITTED`.
- Other witness claim mutations must still be rejected.
- No weakening of prior independent tests or scientific guards.
- GitHub Actions must pass; do not claim acceptance before verifying actual logs.

This branch changes only abstract model source and documentation. The original Windows worktree and scientific artifacts are untouched. No native backend, external witness service, root bootstrap, deployment or inference is authorized.

Keep SRC2-REV-04 pending an independent final review; SRC-02 NOT_AUTHORIZED, DEPENDENCY_APPROVAL_REQUIRED, PILOT_BLOCKED and all eight gates PENDING.
