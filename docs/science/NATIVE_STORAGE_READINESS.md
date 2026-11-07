# Native storage readiness

## Disposition

`NATIVE_CONTRACT_REFINEMENT_REQUIRED`. Do not start the Linux backend prototype. Closing AUTH-REV-01 would not authorize SRC-02 or supply the missing operating-system guarantees.

## Contract gaps before a Linux prototype

1. **Independent root bootstrap:** define who provisions the root, how its descriptor/capability is authenticated, the filesystem/device identity accepted, ancestor handling, mount replacement policy, and permissions before the collector opens it.
2. **Durable transaction outcomes:** specify atomic no-replace publication, file and directory `fsync` ordering, handling of crash between data/journal/head writes, and explicit states for committed, not committed, and commit-unknown.
3. **Journal recovery:** define truncation/corruption policy, orphan object handling, checkpoint recovery, and how a partially published event is reconciled without replaying uncertain inference.
4. **Cross-process writer lease:** use OS-backed locks/leases and define stale lease recovery, process identity, owner-death handling, timeout, and adversarial contention. Thread tests do not prove this.
5. **Freshness and rollback:** a locally hash-chained journal cannot detect rollback of the entire tree. Specify an independent monotonic witness or transparency service and its trust/availability model.
6. **Revocation/expiry:** define how authorization revocation is observed after process restart and while a run is open; current registry and expiry are process-local.
7. **Resource enforcement:** bind limits to root/run and enforce disk quota, inode/event limits, journal growth, and cleanup behavior under exhaustion.
8. **Post-collection review:** define access and durability for votes/adjudications after collector exit, reviewer identity revocation, retention, and audit of final decisions.
9. **Recovery test plan:** prove fd-relative/no-follow path resolution, permissions, replacement races, fsync/crash injection, restart, rollback witness, and no inference replay on the target Linux filesystem.

All eight pilot gates remain `PENDING`. No Linux/Windows adapter is implemented or authorized by this review.
