# Durable inference intent and uncertain effects

This refines Phase 7A's `DURABLE_COMMIT_STATE_MACHINE.md` and
`JOURNAL_RECOVERY_CONTRACT.md`; it does not change B0–B4 or authorize execution.

## Per-slot states

| State | Durable evidence | Recovery / retry rule |
|---|---|---|
| `INTENT_PREPARED` | bounded, canonical intent constructed | no dispatch; commit not started |
| `INTENT_DURABLE` | intent receipt and journal barrier verified | dispatch may be attempted only after this point |
| `DISPATCH_MAY_HAVE_STARTED` | conservative marker durably committed before calling model/provider | after restart, never infer non-dispatch from missing response |
| `RESPONSE_OBSERVED` | exact returned continuation in memory, digest bound to operation | not reportable; crash means unknown |
| `RESPONSE_DURABLE` | immutable response object and response receipt durably published | persistence may resume with same operation/digest |
| `RESPONSE_COMMITTED` | response referenced by journal/head transaction | still await all barriers and required witness |
| `INTERRUPTED_UNKNOWN` | dispatch marker exists but no durable exact response disposition | no new inference; preserve slot and require governed reconciliation |

The durable dispatch marker is deliberately conservative: it is recorded before
the external call. A crash after marker publication but before the actual call
still yields `INTERRUPTED_UNKNOWN`; avoiding duplicate external effects takes
priority over automatic completion. Only `INTENT_DURABLE` with no dispatch marker
proves that a retry is safe. The backend must establish that this proof survives
restart and is bound to the same run, slot, input, configuration and Operation ID.

## Crash cuts

The abstract tests inject crash at each state in a complete synthetic history.
Before the dispatch marker, recovery may establish no external effect and permit
continuation. At or after the marker, recovery leaves `INTERRUPTED_UNKNOWN` unless
the exact response bytes are recovered and verified. Object/journal/head writes
may be retried only for the same Operation ID, canonical intent, exact bytes and
expected predecessor; conflicting content is rejected. This persistence retry
is distinct from re-running inference.

Any crash, timeout, I/O failure, quota exhaustion or uncertain response after
dispatch blocks scientific completion. No automatic inference retry or ASR
denominator exclusion is permitted. This is a specification-level rule; native
crash and durability tests remain `NOT_RUN`.
