# Platform feasibility review

This is a contract feasibility assessment, not native validation. Public API documentation does not prove race safety, filesystem behavior, durability or correct adapter implementation.

## Linux

The selected primitives form a plausible restricted local-filesystem design:

- `openat2` resolution flags can constrain lookups beneath a directory FD and reject symlinks/magic links; kernel support and exact `EAGAIN`/unsupported handling must be pinned. `RESOLVE_NO_XDEV` is a strong initial policy when no subordinate mount is approved.
- `renameat2(RENAME_NOREPLACE)` provides no-overwrite publication where supported by the kernel/filesystem; unsupported combinations must fail, not fall back.
- `fsync(file)` does not necessarily persist the containing directory entry; directory FD `fsync` is separately required for a namespace durability claim.
- `F_OFD_SETLK` is a candidate local interprocess lock tied to an open file description. It is advisory and is not an atomic commit fence by itself.

**Linux readiness: REFINEMENT_REQUIRED.** Pin exact kernel/filesystem/mount combinations and no-replace primitive, add enforceable fencing semantics, define root bootstrap and intent state machine, then plan isolated native failure-injection. NFS/FUSE/SMB/overlay/WSL remain unsupported absent specific evidence.

## Windows

The proposed strategy is plausible only with an audited native handle-relative adapter:

- Microsoft documents `NtCreateFile` `RootDirectory` as a directory handle and a relative `ObjectName`; `FILE_ID_INFO` combines volume serial and file ID for object identity. Neither alone proves authority, freshness or no-reparse traversal.
- `FILE_OPEN_REPARSE_POINT` opens a reparse point itself rather than following it; the contract must specify detection/rejection for every component and the supported exact flags/ABI. Do not assume full-path `CreateFile` flags confine ancestors.
- `LockFileEx` can provide an exclusive byte-range lock, but all processes must honor it; it is not an independent fencing epoch. Memory-mapped I/O bypasses byte-range lock enforcement.
- `FlushFileBuffers` flushes file buffers. The proposal correctly does not equate this with Linux directory `fsync`; namespace metadata and crash/power-loss semantics remain an evidence gate.

**Windows readiness: REFINEMENT_REQUIRED.** Function-specific docs do not fully settle the exact user-mode relative-open/reparse combination or a certified no-clobber + metadata durability contract. Require a reviewed native wrapper and a supported Windows/NTFS profile before any prototype.

## Primary references

- Linux [`openat2(2)`](https://man7.org/linux/man-pages/man2/openat2.2.html), [`renameat2(2)`](https://man7.org/linux/man-pages/man2/renameat2.2.html), [`fsync(2)`](https://man7.org/linux/man-pages/man2/fsync.2.html), [`fcntl` OFD locks](https://man7.org/linux/man-pages/man2/fcntl_locking.2.html).
- Microsoft [`NtCreateFile`](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile), [`FILE_ID_INFO`](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_info), [`LockFileEx` locking semantics](https://learn.microsoft.com/en-us/windows/win32/fileio/locking-and-unlocking-byte-ranges-in-files), [`FlushFileBuffers`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers), and [reparse point operations](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-point-operations).
