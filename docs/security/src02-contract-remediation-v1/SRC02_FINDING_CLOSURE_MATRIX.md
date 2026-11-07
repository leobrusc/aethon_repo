# SRC-02 finding closure matrix

All statuses below are specification/model status only. Nothing here authorizes
storage, witness, dependency, pilot or native implementation.

| Finding | Prior defect | Phase 7C refinement | Evidence | Disposition |
|---|---|---|---|---|
| SRC2-REV-01 HIGH | Independent boolean classifier accepted COMMITTED without durable object/journal or legal history | Closed action relation, exact bindings, legal history validation, three-valued outcome plus `REJECTED` | 24 synthetic tests; explorer 16,642 states | `REMEDIATED_SPEC_MODEL` |
| SRC2-REV-02 HIGH | Token check separate from head CAS | Epoch/holder/expected-head checked in one abstract publish transition; stale writer counterexample rejected; unsupported lock-only takeover prohibited | A epoch 7 → B epoch 8 → A rejected with unchanged head | `REMEDIATED_SPEC_NATIVE_GATE_REQUIRED` |
| SRC2-REV-03 HIGH | Intent did not distinguish may-dispatch from durable response/unknown | Explicit lifecycle; durable marker precedes effect; uncertain state never retries; persistence retry is exact/idempotent only | crash-cut and retry rejection tests | `REMEDIATED_SPEC_NATIVE_GATE_REQUIRED` |
| SRC2-REV-04 MEDIUM | Witness timeout/divergence had no safe reconciliation table | Operation-ID compare-and-advance/query, before/after timeout cases, epoch binding, explicit conflicts, no downgrade/automatic conflict recovery | idempotent same-operation tests and conflict rejection | `REMEDIATED_SPEC_WITNESS_UNSELECTED` |
| SRC2-REV-05 MEDIUM | Bootstrap issuer, principal, revocation trust details underspecified | Versioned canonical signed receipt, independent trust anchor, OS-principal/root binding, monotonic revocation epoch and race outcomes specified | contract document; no issuer/receipt implementation | `REMEDIATED_SPEC_ISSUER_UNIMPLEMENTED` |
| SRC2-REV-06 MEDIUM | Windows reparse, no-clobber and durability profile unpinned | Candidate serviced Windows 11 26H2 x64/local NTFS scope and fail-closed requirements documented | official docs referenced; native guarantee `NOT_VALIDATED` | `REMEDIATED_SPEC_NATIVE_NOT_VALIDATED` |

## Overall

`SRC02_CONTRACT_REMEDIATED` within the specification/model scope, subject to
independent review. All six reported gaps now have explicit invariants,
transitions, fail-closed outcomes and acceptance criteria. This is not native
implementation evidence: lease enforcement, witness service, issuer/revocation
infrastructure, Windows ABI/durability, and Linux profile remain unselected or
`NOT_VALIDATED`. It does not permit an operational backend, pilot or production
prototype. Those require their own review and authorization gates.
