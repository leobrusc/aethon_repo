# Implementation readiness decision

## Disposition

**`NATIVE_CONTRACT_READY_FOR_INDEPENDENT_REVIEW`** as a contract proposal. This means the major trust boundaries, state transitions, platform confinement requirements, failure semantics, freshness, revocation, quotas and post-collection authority are specified for independent critique. It is not implementation approval, deployment approval, or evidence that Linux/Windows primitives work as required.

## Core invariants

1. No run capability without an independently bootstrapped root object capability, valid application authorization, exact immutable manifest v2, grant, budget, retention and fresh witness state.
2. No untrusted input becomes a pathname, native object name, root selector or authority.
3. Every persistence operation—read, write, scan, journal, head, lock, recovery, staging and cleanup—uses the same retained root capability and platform-native relative operations.
4. A durable receipt follows object, journal, head and required witness durability in a certified platform profile; otherwise result is `NOT_COMMITTED` or `COMMIT_UNKNOWN`.
5. Unknown external effects, especially inference, are never retried automatically.
6. A writer lease and fencing token are required for mutation; stale writers cannot commit.
7. Resume requires fresh authorization/revocation checks and external monotonic freshness when rollback is in scope.
8. Collection and post-collection review use separate scoped authorities; frozen quorum remains unchanged.
9. Structural validation preserves 24 cases, 12 pairs, 3 families 4/4/4 and 120 B0–B4 slots; B3/B4 reuse requires the frozen identical-input contract.
10. Corruption, unsupported OS primitive, policy drift, quota exhaustion, witness outage or ambiguous commit fails closed without scientific completion.

## Decisions before implementation

Independent reviewers must settle (a) supported Linux kernel/filesystem/mount profile and exact no-replace/flush primitives; (b) supported Windows build/NTFS profile, audited handle-relative wrapper and metadata durability evidence; (c) root provisioner and trust anchor; (d) witness alternative/operator and disaster recovery; (e) lease primitive and fencing semantics; (f) quota implementation; (g) post-collection review grant; and (h) error/result schema/versioning. No downgrade or default is acceptable for an unresolved item.

## Readiness gates and required evidence

Before a native prototype: independent contract review; approved platform profiles; threat-model sign-off; synthetic state model review; exact failure-injection plan; no dependencies/locks changes without dependency approval; separate implementation branch; no production root or external service; fixtures only.

Before operational use: native adversarial matrix passes on declared profiles; independent code review; verified root/ACL/retention/encryption and witness receipts; immutable approved runtime/SBOM; egress controls; recovery and rollback evidence; all eight operational gates completed; explicit run-specific authorization. Until then `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED`, eight gates `PENDING`.

## Phase 7C status

The finite abstract model is ready for independent review, but does not close
native implementation gates. Before a Linux prototype, reviewers must accept
the transition relation; the platform owner must select a local
filesystem/kernel profile and one serialized fencing authority that atomically
binds epoch to head publication. Issuer/trust-anchor/revocation and witness
operator/consistency decisions and a fault-injection plan covering every
barrier and uncertain inference boundary are prerequisites. Windows remains a
separate profile requiring ABI, reparse and metadata durability evidence. See
`docs/security/src02-contract-remediation-v1/SRC02_FINDING_CLOSURE_MATRIX.md`.

## Evidence index

SHA-256 index of prior decision/evidence files used for this specification is `EVIDENCE_SHA256SUMS.txt` beside this document. `ARTIFACT_SHA256SUMS.txt` indexes the new documents and abstract model (excluding the index itself). These hashes establish the exact reviewed text, not truth of every upstream assertion. The reference set is listed in `EVIDENCE_REFERENCES.md`; execution results are in `VALIDATION_RESULTS.md`.
