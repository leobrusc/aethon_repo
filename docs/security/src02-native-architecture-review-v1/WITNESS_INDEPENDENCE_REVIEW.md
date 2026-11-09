# ADR-002 — witness independence and recovery review

Disposition: `OPEN_DECISION` (ARCH-REV-02).

The proposed linearizable compare-and-advance service is an appropriate candidate for preventing coherent whole-store rollback **only if** the collector and local store cannot roll back or forge the witness's state, trust anchor, signing keys, backup snapshots or operator grants. Neither a co-located process nor another local file is sufficiently independent.

## Concrete unresolved issues

1. Choose service operator/key custodian and define separation of duties from the root custodian and collector identity.
2. Fix identity and authenticated request/response schema; bind root ID, run ID, immutable manifest, operation ID, expected and next sequence/head, policy and revocation epochs, nonce, expiry and signer ID.
3. Specify a linearization point for per-run state compare-and-advance, uniqueness of (run,operation), exact idempotent retries, key rotation and signed monotonic query freshness.
4. Define disallowed situations: witness-local recovery divergence, remote ahead, same-sequence different hash, replay, missing witness, witness administrator/backup sharing with local root.
5. Specify independently governed disaster-recovery quorum and audit log, without allowing automatic sequence reset.

A signed stale cached value is **not** a current checkpoint. If a timeout occurs before/after the remote operation, query the same operation and avoid a new inference. Live failure-injection and independent backup tests are `NOT_RUN`.

The fixture model's `witness_response_valid` and frozen claim tuple are trusted modeling primitives; they do not instantiate cryptographic verification.

No witness selection or operational readiness is approved by this report.
