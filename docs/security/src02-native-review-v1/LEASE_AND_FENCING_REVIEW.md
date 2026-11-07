# Lease and fencing review

## Assessment

The PR #33 contract correctly rejects Python locks, timestamps and caller-named lockfiles as sufficient interprocess exclusion. It also recognizes PID reuse, owner death and the need for a monotonically increasing token. The missing property is atomic enforcement: a pre-publication “revalidate token” check is subject to a race with lease transfer.

### SRC2-REV-02 — stale writer can pass check before transfer (HIGH)

Counterexample sequence:

1. Writer A holds token 7 and validates it against the lease record.
2. A pauses before head publication.
3. Lease expires/transfers; writer B obtains token 8 and recovers.
4. A resumes and performs CAS against the expected old head, without atomically comparing token 7 to current token 8.

If the expected head is still compatible or A's publication path does not include the epoch, the stale writer may publish after B. An “immediately before” check narrows but does not remove the TOCTOU interval.

## Required contract

- The fencing epoch is monotonic across process restart and cannot roll back with the run store; if the filesystem is the only source, a separately trusted witness must fence it.
- Every mutating record/head includes `(lease_id, fencing_epoch)` and publication atomically rejects a stale epoch. It is not enough to store the token in process memory or validate it in a separate read.
- Lease transfer and head publication must share one serializable authority or prove an equivalent OS primitive. Define transfer linearization, crash behavior, token allocation and stale writer rejection.
- A lease cannot be declared expired solely from wall-clock timeout while the prior writer may continue running. Use an OS lock tied to retained handle/process lifetime, or a service that issues fences enforced by the commit authority.
- PID and process start identity are audit fields, not fencing by themselves.

## Platform candidates, not approvals

- **Linux, single-host local FS:** an advisory open-file-description byte-range lock (`F_OFD_SETLK`) on a root-relative, identity-checked lock object is a candidate. It is associated with the open file description, unlike traditional process-associated record locks. It releases when the relevant open description is finally closed. It does not itself provide a durable monotonic fencing token, prevent privileged bypass, or establish correct semantics on unsupported/network filesystems. A token still needs atomic commit enforcement.
- **Windows, single-host local FS:** a `LockFileEx` exclusive byte-range lock on an identity-checked handle-bound lock object is a candidate; process termination closes kernel handles. Define sharing modes and ensure every mutator honors the lock. Byte-range locks are not respected by memory-mapped accesses, so the implementation must prohibit that path. It also does not provide the monotonic durable fence by itself.
- Multi-host use remains unsupported absent a separately reviewed distributed lock/fencing service and filesystem profile.

## Acceptance tests

Pause A between validation and commit, transfer lease to B, then resume A: A's commit must fail atomically. Repeat with process kill, PID reuse, restart, expiry, lock-object replacement, witness outage, and concurrent witness/head CAS. Assert no dual successful writers and no automatic inference replay. Threads tests alone are insufficient.
