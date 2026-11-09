# Inference Dispatch and Crash Recovery

## State distinctions

| State | Meaning | Recovery rule |
|---|---|---|
| `INTENT_PREPARED` | Bound operation exists in memory | No dispatch is permitted yet |
| `INTENT_DURABLE` | Bound intent barrier completed | Dispatch may be authorized; no dispatch is yet known |
| `DISPATCH_MAY_HAVE_STARTED` | Durable single dispatch marker precedes provider call | Never infer non-dispatch from a missing response |
| `RESPONSE_OBSERVED` | Exact nonempty continuation returned and bound to run/slot/op/config | Not yet recoverable after crash |
| `RESPONSE_VERIFIED` | SHA-256 recomputation matches the observed bytes | May proceed to durable response publication |
| `RESPONSE_DURABLE` | Exact response digest is durably represented | Persistence may retry idempotently with same op/digest |
| `INTERRUPTED_UNKNOWN` | Dispatch may have happened, but no verifiable durable response is available | Block; no new inference call |

## Crash cuts

- Before `INTENT_DURABLE`: no dispatch.
- After `INTENT_DURABLE` and before marker: durable absence of marker is the only modeled basis for a safe same-operation retry.
- After marker and before durable response: recovery moves to `INTERRUPTED_UNKNOWN`, including a crash before the provider call actually began. This conservative false uncertainty avoids duplicate external effects.
- After durable response: resume only persistence/publication for the same operation and exact response digest; do not call inference again.
- After object, journal, publish, head barrier, or witness request: preserve `COMMIT_UNKNOWN` until the corresponding local barriers and, when configured, fresh witness evidence reconcile the same operation.

The abstract crash action does not model power-loss ordering, provider-side idempotency, or actual syscall durability. Native fault-injection remains NOT_RUN.
