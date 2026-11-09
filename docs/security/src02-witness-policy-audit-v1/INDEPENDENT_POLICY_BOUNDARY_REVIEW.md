# SRC2-REV-04 — independent witness-policy downgrade audit

## Review identity

Reviewed PR #38 exact HEAD: `7b8a0efac4840713b7f381ab6ef68f03ed7316f6`.

The PR #38 CI `42549485141` concluded Linux/Windows/research audit SUCCESS. Both CPU jobs ran 494 tests each; this is evidence for the existing test suite, not proof of immutable witness policy.

## New hypothesis / required invariant

The abstract State contains a mutable field `witness_required`. The model binds verified witness response claims to `witness_verified_binding` but does **not** bind `witness_required` to a frozen policy receipt or immutable launch grant. The check of witness proof at acknowledgment is conditional on this mutable policy field.

Required: after creation of a run, witness policy is fixed by the independently authorized grant. Changing from required to optional must not transform a previously witness-protected committed response into an accepted no-witness response.

The independent `tests/test_src02_witness_policy_audit.py` asserts rejection of:
1. A completed no-witness operation reclassified under a stronger witness requirement.
2. A completed witness-protected operation with `witness_required=False` and its witness verification/ack metadata removed.
3. Positive, unmodified histories in both configurations still classify `COMMITTED`.

The second case is a synthetic state-substitution adversarial test. It does not show bypass by normal application code, and does not imply arbitrary interpreter-memory tampering resistance. It demonstrates absence of an abstract immutable policy-consistency invariant when snapshots are accepted as inputs.

## Status and evidence

This branch adds **only adversarial tests and this report** to the exact PR #38 HEAD. It does not fix the implementation. The new negative tests are expected to reveal whether this invariant is enforced; a CI failure on the known counterexample is to be recorded as a security review finding, **not** as a passed remediation. No backend, filesystem, witness service, real inference or protected scientific data was modified.

Possible dispositions:
- `SRC2_REV_04_REOPEN_REMEDIATION_REQUIRED` if the downgrade is accepted.
- `REVIEW_INCOMPLETE` if the test cannot execute or the invariant cannot be evaluated.
- `NO_NEW_FINDING` only if it is rejected and regression tests remain clean.

Retain `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED` and all eight gates `PENDING`.
