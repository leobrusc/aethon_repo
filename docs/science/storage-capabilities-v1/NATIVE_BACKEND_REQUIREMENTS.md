# Requirements before Linux/Windows native backends

Mandatory decision: [SRC02_STORAGE_DECISION.md](../../../SRC02_STORAGE_DECISION.md), PR #19 `7431d7b423bc6fc34d1db51c12794742481f8428`. Selected architecture remains isolated pre-provisioned collector plus complete descriptor/handle-relative backends (C + A/B). This phase implements neither native option and grants no storage/pilot authority.

## Common prerequisites

Bootstrap must acquire an independently approved root object capability before untrusted inventory work, bind actual root/custody/authorization identity, approved immutable manifest/config/resource budget/expiry and an independent freshness policy. The backend instance owns this capability; neither a pathname nor a `confinement.check` callback/receipt flag can substitute. A native implementation must cover **all** get/put, object creation, journal/head scans/commits, writer lease/locks, recovery, staging and owned cleanup with the same confinement. No fallback to Path, shutil, shell or pathname reopen is allowed.

Native conformance must satisfy the synthetic logical tests plus adversarial replacement/rename, ancestry, symlink/junction/reparse, mount/device, concurrent writers, lock abandonment, collision, partial write, corruption, disk-full/denied I/O, crash/power-loss and independent rollback-witness tests on each actually supported OS/kernel/filesystem. Unsupported primitives or uncertain commit disposition fail closed. Replaying an ambiguous inference is not recovery.

An independently administered authenticated monotonic head witness must be checked before resume under a rollback adversary. Hash chains/content hashes alone do not detect coherent whole-store restore; a same-host witness restored with it is not independent. Without such evidence restrict the threat model explicitly and prohibit automatic production resume. No witness/service/key or cloud dependency is provisioned here.

## Linux

- Hold trusted root/ancestor directory descriptors and verify fstat object identity, ownership, filesystem/mount policy and signed root binding. Never recover authority by reopening an old pathname after root rename/replacement.
- Use reviewed descriptor-relative lookup, including openat2 RESOLVE_BENEATH, RESOLVE_NO_SYMLINKS/NO_MAGICLINKS and an explicit approved mount policy; O_NOFOLLOW on the final component alone is insufficient. Reject unsupported kernel flags or unsafe namespaces instead of downgrading.
- Use a tested same-filesystem exclusive/no-replace publication protocol; synchronize data and required containing-directory metadata before durable acknowledgments. Objects must be durable before referencing journal commits. Test real filesystem/mount/options and disk failures.
- Implement writer exclusion and recovery/cleanup using held capabilities, never a caller-owned writer.lock pathname. Define lease-owner verification/abandonment conservatively; permissions revocation on an already held FD is not inferred.
- Validate only real supported local filesystems/kernel combinations. Do not transfer evidence to NFS/FUSE/SMB/overlay/WSL DrvFS. Untrusted mount/namespace administration and writable existing handles remain operational trust concerns.

References: [openat2](https://man7.org/linux/man-pages/man2/openat2.2.html), [openat](https://man7.org/linux/man-pages/man2/open.2.html), [fsync](https://man7.org/linux/man-pages/man2/fsync.2.html).

## Windows

- Hold real root/ancestor/child directory handles. Compare approved VolumeSerialNumber/FileId identities and verify each applicable component; path hashes, File IDs alone or an earlier copied ACL observation do not establish current custody/freshness.
- Review a true handle-relative open implementation (for example an audited NtCreateFile wrapper), relevant ABI, reparse behavior and share modes. Reject junctions/reparse/mount escapes, device/UNC namespaces, ADS and unsupported filesystem cases under the initial policy. CreateFile flags alone are not all-ancestor confinement.
- Inspect owner/protected DACL using the same object handles and test concurrent security-descriptor changes/revocation. Python st_mode or an ACL snapshot is not a revocation lock. Separate collector from administrator/custodian and approval-signing identities.
- Define a same-volume, no-clobber, handle-bound publication and journal/lock recovery protocol with FlushFileBuffers and tested metadata durability. Do not equate a file flush with directory-fsync or guarantee every power-loss outcome without evidence. Cleanup must retain ownership/identity constraints and not delete a foreign writer's records.
- Test explicitly on the supported Windows build/NTFS/storage stack and hostile reparse/handle-sharing cases. No Windows backend exists or is certified by these Python in-memory tests.

References: [FILE_ID_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_info), [NtCreateFile](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile), [GetSecurityInfo](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo), [FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers).

## Operational release criteria

Independent native review, verified root/custody/isolation/retention/erasure receipts, OS-enforced filesystem/egress controls, immutable approved runtime/dependencies and valid operational authorization are all outstanding. The resource budget must be independently approved and tied to native root/run capabilities; synthetic defaults are not a grant. Actual deletion/SSD snapshots/backups and whole-host compromise remain outside what a Python API can guarantee.

No real root/ACL, private production directory, native handle backend, environment/dependency update, inference, network enabling or deployment was performed. SRC-01 remains blocked independently; storage work cannot authorize it. **SRC-02 NOT_AUTHORIZED / PILOT_BLOCKED**, eight gates PENDING.

Post-collection review authority must be designed and approved independently without silently extending the immutable run grant. Current facade operations retain the original issued authorization expiry. Logical run IDs are not OS filenames; native implementations must not concatenate them into paths or accept device names through a filesystem mapping.
