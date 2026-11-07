# Witness and local-head reconciliation

This refines `FRESHNESS_WITNESS_DESIGN.md`. The protocol uses authenticated,
per-run compare-and-advance with `(operation_id, expected_sequence,
expected_head_hash, next_sequence, next_head_hash)` and idempotent query by the
same Operation ID. A new request is never created after a timeout until the
prior request's disposition is queried.

| Local vs witness | Required result |
|---|---|
| same sequence and hash | Revalidate authorization/revocation, then resume read/append under a fresh lease |
| local exactly one ahead; same Operation ID receipt proves intended next head | Query or repeat the exact compare-and-advance; accept only the same operation result |
| local ahead without matching intent/receipt | Block; independent recovery decision required |
| witness ahead | Rollback/conflict: block; never lower local or witness sequence |
| same sequence, different hash | Integrity conflict: block |
| witness unavailable before request | Block resume and new inference |
| timeout before remote commit | Query same Operation ID; if confirmed absent at exact predecessor, retry same request only |
| timeout after remote commit | Query same Operation ID and verify exact next tuple; do not advance under a new ID |
| duplicate same request | Return the same authenticated result |
| replayed older checkpoint | Reject by monotonic sequence and authenticated current query/proof |
| epoch or policy epoch differs | Block until separately governed reauthorization/recovery |

No sequence can be reset or downgraded. An ambiguous query remains
`COMMIT_UNKNOWN`; no automatic resume occurs. A local hash chain cannot detect a
coherent full-store rollback. The two infrastructure choices remain open: an
independent linearizable witness service or an authenticated append-only ledger
with client-verifiable freshness/consistency proofs. Selection requires a
separate operator, key lifecycle, backup/recovery and availability decision.

The abstract model verifies the idempotent same-operation path and blocks
unavailable, ahead, behind and same-sequence-conflicting states. It does not
validate a deployed witness, PKI, network protocol or administrative
independence.
