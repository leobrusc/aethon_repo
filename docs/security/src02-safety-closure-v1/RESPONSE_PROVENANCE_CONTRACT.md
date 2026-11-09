# Response Provenance Contract (Phase 7E)

## Required inference response chain

The abstract operation type is explicit: `INFERENCE`, `PERSISTENCE`, or `ADMINISTRATIVE`. Only an `INFERENCE` operation may enter the response state machine. `PERSISTENCE` can idempotently store an already durable response receipt. `ADMINISTRATIVE` can append a typed administrative record, but cannot create an inference response, response object, or acknowledged result.

For an inference slot, legal progress is:

`INTENT_PREPARED → INTENT_DURABLE → DISPATCH_AUTHORIZED → DISPATCH_MAY_HAVE_STARTED → RESPONSE_OBSERVED → RESPONSE_VERIFIED → RESPONSE_DURABLE → OBJECT_DURABLE → JOURNAL_DURABLE → HEAD_PUBLISHED → HEAD_DURABLE → WITNESS_CONFIRMED (when required) → RESPONSE_CONFIRMED`.

The intent and every observed response are bound to `(run_id, slot_id, operation_id, manifest_digest, config_digest)`. Dispatch authorization checks all five bindings and is only accepted after the intent is durable. The dispatch marker is at most once and deliberately means the external effect may have started. Empty continuations are rejected. The model computes SHA-256 over the exact synthetic response bytes and carries that digest through immutable persistence and the head. A changed digest, run/slot, manifest, configuration, or Operation ID is rejected.

`persist_object` is unavailable until a nonempty response was observed after the dispatch marker, verified against its bytes, and durably recorded. There is no empty response, placeholder, or administrative-to-inference conversion. `COMMITTED` requires response confirmation after object, journal, head and fencing barriers, plus authenticated witness evidence when that profile is required. Without witness, the local-barrier profile is explicitly weaker against complete store rollback.

## Persistence retry versus inference retry

`persist_retry` accepts only the same Operation ID and exact digest for an already durable response. It does not change response bytes, dispatch count, or external effects. Inference retry is a separate transition and is permitted only while the durable marker proves dispatch never began; it retains the original run/slot/op/config identity. Once a marker exists, a crash with no recoverable durable response sets `INTERRUPTED_UNKNOWN`; neither `recover` nor retry can clear that state automatically.

## Limits

The model stores a synthetic byte string to make digest equality executable. It does not retain or process AETHON private prompts/responses. SHA-256 here checks model-level byte identity; it does not authenticate an external model/provider. A real receipt/signature verifier, durable storage, and host isolation are outside this abstract model and remain NOT_VALIDATED.
