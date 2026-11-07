# Durable commit state machine

## Result type and binding

Replace the current free-form `WriteReceipt.durability` string with a versioned, closed result type: `NOT_COMMITTED`, `COMMIT_UNKNOWN`, or `COMMITTED`. A receipt binds root-capability ID, run ID, manifest digest, run fingerprint, complete grant/budget/retention binding, operation ID, exact object digest/length, journal sequence and head hash, backend/platform profile, durability policy version, and witness checkpoint where required. It must not imply physical durability on the synthetic backend.

`COMMITTED` means the backend has satisfied every data, namespace, journal and head persistence barrier for the specifically certified platform profile and the resulting journal/head agree. It is not an absolute promise against malicious hardware, administrator/kernel compromise, or storage-stack guarantees beyond evidence.

## Transaction stages

For an object plus event transaction, persist a durable operation intent before any external side effect (including inference). Then:

1. Validate active RootCapability, live Authorization, manifest, budget, witness freshness, lease/fencing token and expected journal head.
2. Create a unique staging object without following links; write bounded bytes; flush object; verify bytes and digest.
3. Publish the immutable object with no-replace semantics; synchronize required namespace metadata. A collision is accepted only if existing bytes and operation binding are identical; otherwise reject.
4. Append one journal record via compare-and-append containing prior head, next sequence, operation ID, object references and exact state. Flush the journal record and required metadata.
5. Publish/update head with compare-and-swap and no-replace/versioned semantics; flush it and containing metadata according to the platform profile.
6. Update the authenticated external witness (if required) to this exact sequence/head. The failure ordering must be specified: witness ahead of local state blocks resume pending reconciliation; local ahead of witness is not acknowledged committed.
7. Re-read/verify all bindings and issue a durable receipt only when local and witness state satisfy policy.

The transaction's logical linearization point is the successful head CAS, but its durable acknowledgment point is later: after all required local flushes and external witness acknowledgment. No caller may infer commit from object existence alone.

## Three-valued outcomes

| Result | Meaning | Caller behavior |
|---|---|---|
| `NOT_COMMITTED` | Evidence proves the transaction did not cross the durable commit point; no accepted state references its effects | May retry only idempotent persistence with the same operation ID/intent; inference may be retried only if a durable pre-inference intent proves it never started |
| `COMMIT_UNKNOWN` | Crash, timeout, I/O error or witness disagreement prevents proof either way | Do not repeat inference or external side effect; stop run, preserve evidence, reconcile under exclusive lease and witness; no scientific completion report |
| `COMMITTED` | All certified local barriers, journal/head consistency and required witness update succeeded | Return exact receipt; retry with same operation ID and same bytes yields same receipt |

Failure before durable intent can be `NOT_COMMITTED` only after proving no side effect began. Any failure after inference intent or possible model invocation is `COMMIT_UNKNOWN` unless a durable record proves its final disposition. Failure after head update but before acknowledgment is reconciled by exact operation ID and witness; it is never blindly repeated.

## Platform qualification

Linux profile must document object-file flush, no-replace publication, containing-directory synchronization, head ordering, mount options and tested filesystem/kernel. Windows profile must document handle-bound no-clobber creation, `FlushFileBuffers`, metadata ordering and tested NTFS/storage stack. If the profile cannot prove directory/namespace persistence or maps an error ambiguously, it cannot return `COMMITTED`.
