# ADR-002 — independent monotonic freshness witness

Status: **PROPOSED_NOT_APPROVED**. No witness has been selected or provisioned.

## Proposed candidate and alternative
Candidate A: a separately administered **linearizable** compare-and-advance service with independent storage/backup, signing keys and policy control. Alternative B: an independently administered append-only ledger with authenticated inclusion, consistency and current-head freshness proofs. This ADR proposes A for a *future isolated proof of concept*, not operational adoption. If its administrative and storage independence cannot be demonstrated, leave SRC-02 blocked; never substitute a local checkpoint or same-host daemon.

## Precise contract
Checkpoint identity binds `witness_id, root_id, run_id, operation_id, manifest_digest, policy_epoch, revocation_epoch, sequence, previous_head, next_head, expiry`. Request binds an unpredictable nonce, request identity and exact predecessor. A linearizable compare-and-advance atomically accepts an expected predecessor and new head for **the same operation**; identical replay yields the same authenticated receipt. Reject sequence decreases, same-sequence forks, different-head duplicate operations, foreign-run receipts, stale timestamps/nonces and revoked policy. The remote signer's trust anchor and service identity are deployed independently of the collector, not supplied by receipts.

The client must verify cryptographic receipt bytes, canonical serialization, signature and signer rotation status, nonce, run/operation, policy/revocation epoch and exact sequence/head. A `witness_response_valid` boolean or the synthetic `witness_verified_binding` tuple does not constitute an externally authenticated receipt.

## Failure table
| Case | Policy |
|---|---|
| No response, network split, stale/invalid response | `COMMIT_UNKNOWN`; block resume, no new inference |
| Timeout before/after remote advancement | Query same Operation ID with fresh authenticated query; do not generate a new operation |
| Exact duplicate (operation, predecessor, next) | Return identical bound outcome |
| Local one ahead with exact durable intent and unchanged predecessor | Reconcile same operation only; ambiguous remains blocked |
| Remote ahead, same sequence/different hash, rollback, equivocation | Reject, preserve evidence, independent adjudication |
| Witness becomes unavailable after valid ACK | Historical ACK remains valid; **new** recovery/commit requires valid fresh evidence |
| Revocation or policy epoch mismatch | Block; no silent downgrade |

## Witness availability and trust boundaries
Select independently operated identity, key governance, revocation source, failover, audit log, recovery from corruption, disaster recovery, rate limits and retention **before implementation**. Local-only and no-witness profiles do not protect against coherent whole-store rollback and may not silently satisfy a policy requiring rollback resistance.

## Required tests/approval
Demonstrate request replay, fork/equivocation, stale proof, timeout on both sides of remote commit, operator/backup independence, key rotation/revocation and monotonic recovery. Do not run live witness or create credentials in this design PR. Native witness fault tests T12/T13 stay `NOT_RUN`.
