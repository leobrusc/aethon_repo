# SRC-02 storage architecture decision

Target: **C plus A/B**: pre-provisioned storage and isolated collector identity,
with complete Linux descriptor-relative / Windows handle-relative storage backends.
Current production writes remain disabled. No native confinement is certified here.

## Alternatives

| Option | Root / ancestors / links | ACL and privilege boundary | Atomicity / recovery | Operations, portability and residuals |
| --- | --- | --- | --- | --- |
| A Linux descriptors | Hold approved root; constrain all child lookup; forbid symlink/magic-link/mount escape | Non-writable trusted ancestors and exclusive principal; open FDs do not imply instant rights revocation | Native no-clobber transactions, file+directory synchronization, durable intent | Linux-specific; local supported filesystem/kernel only; no rollback freshness by itself |
| B Windows handles | Volume/file IDs, held parents/children, reparse rejection; no pathname reopen fallback | Inspect handle-bound security descriptors and protected DACL; explicit share policy | Native same-volume no-clobber publication, flush and tested commit protocol | Windows/NTFS-specific; durability/revocation must be evidenced per build |
| C isolated collector **with A/B** | Approved root acquired before untrusted work, immutable code/assets | Separate non-admin identity, controlled storage ownership and no egress | Still requires A/B for every I/O and recovery operation | Smaller TCB than a new RPC service; isolation alone does not close TOCTOU |
| D authenticated storage service | Service owns approved roots; opaque run/object IDs only | Distinct service principal and bounded client capabilities | Transaction/idempotency API plus independent freshness witness | Additional protocol, service, keys and availability; still needs A/B internally |

## Required API redesign

The PR #18 `confinement.check(root, identity)` seam is explicitly for trusted test
injection. Implementing only that method and enabling the current store would
leave mkdir/open/link/read/unlink/recovery as pathname operations. It is not the
required native backend. Replace the full persistence boundary, preserving canonical
scientific bytes and run fingerprints, rather than toggling this hook.

```text
open_run(issued_authorization, root_capability, immutable_manifest) -> run_capability
put_if_absent(run_capability, sha256, canonical_bytes, operation_id) -> durable_receipt
get_verified(run_capability, sha256) -> canonical_bytes
append_event(run_capability, expected_sequence, previous_hash, event, operation_id)
    -> committed_sequence, head_hash, durable_receipt
read_head(run_capability) -> sequence, head_hash, recovery_disposition
close(run_capability)
```

Object/run identifiers follow narrow validated grammars; clients never supply
arbitrary paths, absolute child names, `..`, streams, devices or cross-run object
references. Bind capabilities and operation IDs to the complete authorized subject,
root identity, run fingerprint, resource budget and expiry. Same operation/same
bytes returns the same receipt; same operation/different bytes is a collision.
All reads, scans, locks, pointer writes, journal appends, cleanup and restart recovery
must use the same backend boundary. Keep an independent review authorization
design for post-collection human work; do not silently renew an immutable run.

## A — Linux requirements

Bootstrap the pre-provisioned root from a trusted capability, verify fstat identity,
ownership, filesystem and signed root binding, and keep it open. Use openat2 with
RESOLVE_BENEATH, RESOLVE_NO_SYMLINKS/NO_MAGICLINKS and an approved mount policy.
O_NOFOLLOW alone applies to the final component, not every ancestor. Unsupported
kernel/flags or uncertain race errors must fail closed, not downgrade to path checks.
[openat2](https://man7.org/linux/man-pages/man2/openat2.2.html)

Retain directory descriptors for all mutation targets and use descriptor-relative
operations. Bind new objects to the held root even if an external pathname is
renamed; reject a different root during recovery. A rename does not invalidate an
already-open descriptor, but cannot prove current custody or confidentiality.
Never reacquire a missing capability by trusting the old path.
[open/openat](https://man7.org/linux/man-pages/man2/open.2.html),
[rename](https://man7.org/linux/man-pages/man2/rename.2.html)

Publish same-filesystem immutable objects using exclusive creation and a tested
no-replace primitive. Sync file data and then the containing directory before
acknowledging durable publication; a file fsync alone does not establish durability
of its directory entry. Stage object publication before the referencing event.
Exact filesystem, mount options and storage error behavior belong in the evidence.
[fsync](https://man7.org/linux/man-pages/man2/fsync.2.html)

Do not generalize ext4/XFS evidence to NFS, FUSE, SMB, overlay or WSL DrvFS. Owner,
mount/namespace administration and existing writable handles remain trust concerns.
If a malicious principal can change permissions or contents within the trusted
root, secure traversal alone cannot establish confidentiality or immutability.

## B — Windows requirements

Acquire and retain real directory handles, compare VolumeSerialNumber/FileId
against the approved root observation, and inspect each relevant component before
allowing writes. File IDs identify objects on a volume, not freshness after restore
or deletion/reuse. Do not use pathname hashes as substitutes.
[FILE_ID_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_info)

Documented CreateFile flags permit opening directories and reparse objects; they
are not an all-ancestor confinement guarantee. Use an audited handle-relative
open implementation, such as a reviewed NtCreateFile wrapper rooted at a trusted
directory handle, with strict reparse/relative-name policy and supported ABI.
Evaluate share modes and existing conflicting handles explicitly. Reject junctions,
mount points, UNC/device namespaces, alternate streams and unsupported filesystems
under the initial policy, rather than normalizing them silently.
[CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew),
[NtCreateFile](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile)

Inspect owner/DACL using the same object handle. A copied descriptor is an
observation, not a lock preventing its mutation; GetSecurityInfo itself does not
handle concurrent descriptor changes. Native rights and control-plane revocation
must be tested instead of inferred from Python st_mode.
[GetSecurityInfo](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo)

Define a same-volume, no-clobber, handle-bound publication protocol with explicit
file-buffer flushing and tested metadata/journal commit behavior. FlushFileBuffers
documents a file flush; this review does not equate it with Linux directory fsync
or certify survival of every power loss. Unsupported durable-commit semantics are
a blocking condition. No automatic fallback to shutil/Path writes is acceptable.
[FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)

## Shared operational guarantees and limits

| Property | Required evidence / residual trust |
| --- | --- |
| Identity and permissions | Root object and custody attestation, trusted ancestors, exclusive principal; monitor/control revocation and stop safely; privileged administrator remains trusted |
| Atomicity | Failure injection at every publication/event boundary; no partial accepted target or overwriting collision |
| Idempotence | Durable inference/evaluation intent before side effects; same transaction returns prior result; uncertain inference is never automatically retried |
| Rollback | Hash chain is insufficient. Compare head with an independent authenticated monotonic witness before resume; absent witness/freshness proof means blocked resume under a rollback adversary |
| Isolation and egress | Native OS identity/filesystem/egress policy, not Python socket patches; provision only under separate approval |
| Keys | Collector needs public approval keys; keep signing/private witness keys outside it; authenticate any broker channel/run capability without logging secrets |
| Retention | Custodian, concrete deletion policy, private backup inventory and separately evidenced erasure; no claim that deleting a filename erases SSD snapshots/backups |
| Whole-host compromise | Neither object handles, crypto libraries nor a same-host service defeat a hostile kernel/admin or rollback of the entire trust base |

If an attacker can roll back both store and purported witness, that witness is not
independent. A separately administered append-only head ledger or reviewed offline
custodian checkpoint can be designed without assuming a paid/cloud service; none
is provisioned here. If this is not available, explicitly restrict the deployment
threat model and prohibit automatic resume where freshness cannot be established.

D remains an escalation path if process compromise must be contained: authenticate
peer/run/operation, hash and sequence; bind acknowledgments to exact data and
durability state; reject replay/conflicts and impose quotas. C and D still depend on
native OS isolation and A/B I/O correctness; no new service is created in this phase.
