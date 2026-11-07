# Interprocess writer lease contract

## Lease properties

The native backend, not the caller, acquires an OS-enforced exclusive lease scoped to `(root_capability_id, run_id)`. The lease records owner process identity (platform process ID plus start identity to avoid PID reuse), boot/session identity, grant ID, expiry/renewal policy, current journal head, monotonically increasing fencing token, and backend instance nonce. The lock object is opened only through the root capability and cannot be named by an inventory pathname.

Every mutating operation carries the lease/fencing token and revalidates current ownership immediately before compare-and-append/head publication. A stale token cannot commit after a successor obtains a higher token. Lease acquisition also revalidates authorization, revocation, root identity and witness freshness.

## Owner death and contention

Contenders fail with `WriterBusy` or wait only under a bounded, configured policy. They do not break a lease based on elapsed wall time alone. On confirmed process death/OS lock release, the next writer obtains a higher fencing token, then performs full recovery before any mutation. If owner death occurred during an operation, that operation is `COMMIT_UNKNOWN` until journal/witness reconciliation.

The OS primitive and its owner-death semantics must be documented for each supported platform/filesystem. A Python mutex, in-memory flag, lockfile pathname, stale timestamp, or advisory lock not honored by the filesystem is insufficient. Multi-host operation is unsupported unless the selected filesystem/lease service provides and passes explicit distributed-fencing tests.

## Lifecycle and non-goals

Lease release is tied to the backend-owned handle and is idempotent; cleanup never removes another process's lock. Closing a capability cannot grant access or create a run. Threads tests establish only in-process behavior; multiprocess, crash, PID reuse, machine reboot and simultaneous-host tests are separately required. The lease does not defend against an administrator or kernel that can forge process/lock state.
