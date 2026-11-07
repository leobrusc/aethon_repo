# Journal and recovery contract

## Record model

Every journal record is canonical, bounded, versioned and bound to root ID, run ID, immutable manifest digest, original run fingerprint, grant/budget/retention, sequence, previous record hash, operation ID, event type and object digests. Sequence begins at the protocol-defined initial value and advances by exactly one. Hash is over the exact canonical record bytes and previous hash. `append_event` is compare-and-append on `(expected_sequence, expected_head)`; duplicates are accepted only when operation ID and all intent bytes match an already committed receipt.

The scientific manifest remains v2 and its fingerprint formula is unchanged. Storage transaction envelopes may evolve under a separate versioned storage schema; no automatic migration of historical manifests or receipts is allowed.

## Recovery algorithm

1. Reacquire RootCapability through trusted bootstrap; revalidate OS identity/policy, authorization/revocation, current witness checkpoint and run grant. Do not reopen the old pathname as authority.
2. Acquire exclusive OS writer lease/fencing token.
3. Read bounded head, journal and operation receipts through held handles. Verify canonical encoding, sequence continuity, hash chain, manifest/grant binding, object digests, no-replace identity and exact receipt linkage.
4. Compare local sequence/head with independent witness. A local lower head, witness lower head, same-sequence disagreement, missing witness, or unavailable witness blocks automatic resume. Invoke separately governed disaster recovery only with a new auditable decision.
5. Classify staged/unreferenced objects as orphans, not committed data. Retain them for forensic reconciliation; cleanup only under explicit backend-owned retention policy after proving no journal/head reference and no live writer.
6. Reconcile intents by operation ID. If intent indicates inference may have started but response commit is absent/uncertain, set slot to frozen `interrupted_unknown`; never rerun inference automatically. Missing referenced object, malformed record, duplicate sequence, gap, foreign checkpoint or inconsistent receipt poisons the run and blocks scientific reporting.
7. Recovery emits a signed/verified disposition receipt with old/new head, witness state, decisions and tool/runtime identity. It does not silently repair or truncate.

## Failure handling

- Partial final record: do not truncate in place; preserve bytes, classify unknown, and require an explicit recovery transaction after independent review.
- Corrupt checkpoint/head: reject run; checkpoint cannot override the journal or witness.
- Journal truncation or media error: block; no inferred completion from object scans.
- Head older than witness: rollback detected; block.
- Missing object referenced by committed event: integrity failure; block.
- Object without reference: orphan; no scientific meaning until separately reconciled.
- Recovery resource exhaustion/time limit: leave state unchanged, record incomplete recovery, retry only recovery (not inference) after resources restored.
- Failure during recovery: retain lease only while process is known healthy; otherwise OS releases it and new owner obtains a higher fencing token after reconciliation.

No operation may report collection or scientific review complete from a partial, poisoned, or unresolved run. A hash chain detects internal edits but not a coherent restore of the entire store; freshness depends on the independent witness.

## Phase 7C amendment — external-effect state

Each inference slot uses the explicit lifecycle `INTENT_PREPARED`,
`INTENT_DURABLE`, `DISPATCH_MAY_HAVE_STARTED`, `RESPONSE_OBSERVED`,
`RESPONSE_DURABLE`, `RESPONSE_COMMITTED`, or `INTERRUPTED_UNKNOWN`, described in
`docs/security/src02-contract-remediation-v1/DURABLE_INFERENCE_INTENT.md`.
The conservative dispatch marker is durable before the provider/model call. If
recovery sees that marker without the exact durable response, it must preserve
`INTERRUPTED_UNKNOWN`; missing output does not prove non-dispatch. Inference is
never automatically repeated from that state. Only an intent with no durable
dispatch marker can prove non-dispatch, and only persistence for the same
Operation ID, exact bytes and predecessor is retryable.

Object-only or journal-only artifacts remain uncommitted evidence; no scan-based
completion inference or silent truncation/repair is permitted.
