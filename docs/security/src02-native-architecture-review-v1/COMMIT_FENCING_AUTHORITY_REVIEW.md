# Blocking review — atomic head publication and fencing

Disposition: **`BLOCKING_CONCRETE_PROTOCOL_REQUIRED`** (ARCH-REV-03).

The previous model atomically couples expected head, holder/lease, epoch and revocation in one *abstract* publish transition. That does not establish a matching native primitive. Using a separate `check_epoch()` and `renameat2()` creates a TOCTOU interval:

1. Writer A holds epoch 7 and verifies lease/head.
2. Writer A is descheduled.
3. Authority transfers to writer B with epoch 8.
4. Writer A executes its earlier prepared no-replace rename or updates a versioned head.
5. The head is incorrectly published under a stale lease unless the publication operation itself is serialized with the transfer.

A no-replace destination name is insufficient for compare-and-swap of the **existing current head**. An OFD lock protects only processes that follow the protocol, and a live inherited/duplicated FD may outlive the logical identity of a lease owner. Enforce one authority binding `(root_id, run_id, expected_sequence, expected_hash, lease_id, holder, current_epoch, revocation_epoch)` and the head mutation **within the same serialization boundary**.

## Candidate protocol to evaluate (NOT selected)

For a strictly single-host, same-root/identity, no-untrusted-writer future fixture, an exclusively held OS-backed serialization object *may* serialize head transitions and epoch transfer; no other process may publish outside that boundary. Maintain durable epoch history in a journal synchronized before allowing handoff; require fresh head validation and handle/FD identity under the lock. A retained stale writer must never be allowed to publish after transfer. If authority cannot prove this, do not permit takeover; use an independently serialized commit authority or block the prototype.

The existence of an advisory lock is not sufficient evidence of this protocol. Durable epoch history, authority crash-restart, lock-object replacement/aliasing, fork/exec and inherited FDs, stale cached head, ambiguous crash cut and post-crash witness disagreement must be explicitly tested.

## Minimum negative test

An attempted A/epoch-7 commit after B/epoch-8 transfer must be rejected **without changing head**. Separate simulated check-then-publish should be demonstrated vulnerable or marked unimplemented; an atomic transition must preserve the invariant. This is only a model-level test for now.

No endorsement of a specific Linux lock/CAS wrapper or deployed authority is given.
