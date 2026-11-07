# Freshness witness review

## Comparison

| Criterion | Independent witness service | Authenticated monotonic ledger |
|---|---|---|
| Administrative independence | Must have distinct administrators, credentials, backup and recovery domain from store custodian | Ledger operator and signing/logging keys must be outside store and collector control |
| Authenticity | Mutually authenticated API; signed responses bind run/root/sequence/head/manifest/policy and nonce | Signed checkpoint plus verifiable inclusion/consistency proofs; pin roots and verify proofs locally |
| Atomicity/concurrency | Per-run compare-and-advance with expected prior sequence/hash; idempotent request ID | Append-only transaction with unique operation ID and a defined total order per run |
| Availability | Online at commit/resume; outage blocks resume and leaves commit unknown | Proof/ledger retrieval required; outage blocks resume; no stale cache-only success |
| Recovery | Read-after-timeout lookup of same request; reconcile local/witness head cases | Retrieve signed inclusion and consistency proofs; do not reset after divergent history |
| Key lifecycle | Rotation overlap, revocation, audit, service identity and disaster recovery | Root/key rotation, witnessed transition, proof retention and independent verifier versioning |
| Replay | Nonce + idempotency key + strict monotonic expected state | Checkpoint sequence and proof freshness; reject old signed checkpoints |
| Compromise | Service/admin compromise can forge or roll back its state | Ledger operator/root compromise can equivocate or rewrite unless externally witnessed |

## Decision criteria (no infrastructure selected)

Select only after security owner approves a concrete independent operator, trust roots, API/ledger consistency model, backup/recovery design, service availability target and key rotation/revocation. Prefer the service only if it offers linearizable per-run compare-and-advance and independently auditable monotonic storage. Prefer a ledger only if client-side proof verification and append-only history are independently reviewable. If neither can prove independent monotonicity, restrict the threat model and prohibit automatic resume under rollback risk.

## Finding SRC2-REV-04

The draft says monotonicity, authentication and fail-closed behavior, but does not yet specify idempotent advance response recovery, equivocation detection or how to reconcile local-ahead/witness-ahead states. Required transition table is in `COMMIT_AND_RECOVERY_REVIEW.md`. Keep `Freshness witness readiness: REFINEMENT_REQUIRED` until those protocol details are versioned and reviewed.
