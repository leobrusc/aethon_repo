# Atomic fencing protocol

This refines `INTERPROCESS_LEASE_CONTRACT.md`. The model names an abstract
serialized commit authority; it does not claim a local lock alone provides
fencing.

## Required transition

Lease transfer and head publication are serialized by one authoritative epoch
source. Publication has a single compare-and-swap condition over:

```text
(run_id, expected_head_sequence, expected_head_hash,
 current_lease_id, current_epoch, holder, revocation_epoch)
```

The check and logical head publication are one indivisible operation. The
successful operation stores the fencing epoch and lease ID in the immutable
journal/head record. A separate “check token, then write” sequence is forbidden.
The next durable barrier confirms the publication; if it fails, the result is
`COMMIT_UNKNOWN` and recovery reconciles the exact Operation ID.

## Required stale-writer counterexample

1. A holds epoch 7 and reads head `n/h`.
2. A pauses before publication.
3. The lease authority transfers to B at epoch 8.
4. A attempts the old expected-head publication with epoch 7.
5. The atomic transition rejects A and leaves `n/h` unchanged.
6. Only B may publish with epoch 8 after revalidating the expected head.

The synthetic test proves this behavior in the abstract relation. The explorer
accepts no state in which a publication's stored writer/epoch differs from the
current holder/epoch at its linearization transition.

## Platform gate

Linux `F_OFD_SETLK` and Windows `LockFileEx` are candidate process-lifetime
exclusion primitives, not a complete distributed fencing authority. Their
native adapter must prove that a successor cannot transfer authority while a
stale process can still publish through retained descriptors/handles. If every
mutation cannot be forced through one OS-backed serialized authority, use an
independent transaction/commit service or do not implement multi-writer takeover.
PID plus process-start identity is audit metadata, not a fence. Wall-clock lease
expiry alone never transfers authority. Multi-host operation is unsupported.

Native race, crash, PID reuse, process restart, stale descriptor/handle and
lock-object replacement tests remain required before an implementation can
claim this contract.

## Phase 7E model state

The abstract model now retains lease IDs, holder, epoch, authority identity and
state, transfer serial/ID, prepared publication snapshots, expected head, and
revocation epoch. Transfer and publication are represented as transitions of
the same abstract serializer; publication atomically compares the saved token
with current lease/head/authority state. A prepared A/epoch-7 token is rejected
after B receives epoch 8. This is model behavior only and does not validate an
OS primitive or native backend. See `docs/security/src02-safety-closure-v1/ATOMIC_LEASE_AUTHORITY.md`.
