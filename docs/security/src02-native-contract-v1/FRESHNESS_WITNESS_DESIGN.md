# Independent freshness witness design

## Requirement

A local hash chain, signed local receipt, filesystem object ID or backup copy cannot detect restoration of the entire store to an older internally valid state. If whole-store rollback is in scope, resume requires a separately administered monotonic witness whose state is not restored together with the run store.

Witness checkpoint is `(witness_id, root_id, run_id, sequence, head_hash, manifest_digest, policy_epoch, expiry, previous_checkpoint_hash)`, authenticated for the backend and verified before every resume and before acknowledging a commit when policy requires. The collector receives only a narrowly scoped client identity; witness signing keys remain outside collector storage/runtime. Requests are mutually authenticated, idempotent and replay-protected; the witness rejects sequence decrease and conflicting hashes at one sequence.

## Alternatives

| Attribute | A. Independent witness service | B. Authenticated external monotonic ledger |
|---|---|---|
| Trust | Separately administered service, identity and key custody | Independent ledger operator/append-only system plus client verifier |
| Write | Authenticated compare-and-advance for one run/head | Append signed checkpoint and obtain inclusion/consistency proof or authenticated ledger receipt |
| Read | Fresh current checkpoint over authenticated channel | Fresh signed checkpoint plus verifiable monotonic sequence/consistency evidence |
| Availability | Online dependency at commit/resume; fail closed if unavailable | Depends on ledger availability and proof retrieval; fail closed without fresh proof |
| Rollback resistance | Strong only if service state and administration are independent | Strong only if ledger history cannot be rewritten by the storage custodian/collector |
| Operational complexity | Service lifecycle, access control, audit, disaster recovery | Ledger format, proof validation, retention, key rotation, independent operations |
| Residual | Compromised service/admin or stale client cache | Compromised ledger/administrator, invalid trust roots, proof implementation defects |

Neither option is provisioned or selected operationally. A local file, same-host daemon or witness backed up/restored with the store is not independent. If witness unavailable or trust chain invalid, do not resume automatically. Disaster recovery requires an explicit human-governed reconciliation that records the accepted checkpoint and why; it cannot silently reset the sequence.

## Key and policy lifecycle

Define pinned witness identity, key rotation overlap, revocation, clock policy, request nonce, TLS/channel authentication, signed response canonicalization, audit retention and backup independence before implementation. Receipt verification is not operational authorization; the eight gates and launch authorization remain separate.
