# Commit and recovery review

## Required invariants

- A response is reportable only when its immutable object, journal entry, head, operation receipt and required witness checkpoint agree on run, manifest, operation, digest and sequence.
- `COMMITTED` is emitted only after all certified local durability barriers and required witness acknowledgment. `NOT_COMMITTED` requires proof no relevant external effect began. Otherwise `COMMIT_UNKNOWN`.
- Inference intent is durable before invocation. If recovery cannot prove dispatch did not occur or recover the exact response, the slot becomes `interrupted_unknown`; inference is never retried automatically.
- A retry is idempotent only for the same run binding, operation ID, exact input bytes and expected predecessor state.

## Findings and counterexamples

### SRC2-REV-01 — abstract model accepts impossible commit (HIGH)

The model passes its self-check, but `classify()` tests only `acknowledged`, `head_durable` and optional `witness_advanced` to return `COMMITTED`. It does not require `object_durable` or `journal_durable`, nor verify a legal state order. Reproduction:

```python
Snapshot(intent=True, acknowledged=True, head_durable=True,
         object_durable=False, journal_durable=False)
```

`classify(..., witness_required=False)` returns `COMMITTED`; adding `witness_advanced=True` also returns `COMMITTED` with witness required. This is an abstract-model false acceptance, not a native storage exploit. The model must be corrected before it is used to claim safety evidence.

### SRC2-REV-03 — inference dispatch state is underspecified (HIGH)

The contract says to persist intent before an external effect but does not define an authenticated/durable state transition that unambiguously distinguishes queued intent, dispatch possibly begun, model result received, response object durable and response committed. If restart sees only an intent and no response, retry is safe only when there is durable evidence that dispatch never occurred. Without that evidence the only safe disposition is `interrupted_unknown`. Make that rule normative and encode it in the state model.

### SRC2-REV-04 — witness/local ordering needs a recovery table (MEDIUM)

The proposal chooses local head before witness update. It correctly blocks auto-resume on disagreement, but must define:

| Local state | Witness state | Required outcome |
|---|---|---|
| n/h | n/h | Resume after auth/revocation checks |
| n/h | n-1/previous | Authenticate operation receipt and idempotently advance witness, or remain blocked; never infer commit from local alone |
| n/h | n+1/h' | Rollback/conflict; block and require independent disaster-recovery decision |
| n/h | unavailable/unknown | `COMMIT_UNKNOWN`; no resume/inference |
| n/h | n/h' where h' differs | integrity conflict; block |

This table is proposed acceptance behavior, not a claim that the current contract already defines a complete reconciliation procedure.

## Linearization and durability points

Head CAS may be the logical linearization point only if the writer epoch/fencing token is checked atomically as part of that publication. Durable acknowledgment follows data, namespace, journal/head barriers and witness response. The current text names this distinction but does not prove that the token check and CAS are one indivisible operation. Linux `fsync` includes file metadata; the containing directory needs its own `fsync` for the namespace entry. Windows requires separate evidence for namespace metadata; `FlushFileBuffers` alone is not stated as a directory durability guarantee.

## Model correction acceptance criteria

Reject any snapshot with a missing prerequisite, sequence gap, reordered stage, stale lease epoch, object/journal digest mismatch, witness conflict, or acknowledgment before durable barriers. Add crash cuts after intent, inference dispatch, response, object publication, journal, head CAS, witness advance and acknowledgment. Add two-writer/stale-writer interleavings. Verify that every accepted terminal state is reachable through legal transitions and every unknown effect stays unknown. This model remains abstract and cannot establish OS durability.
