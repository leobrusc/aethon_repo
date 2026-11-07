# Windows profile refinement

This is a candidate profile only; no Windows backend or native primitive was
implemented or tested. At review time Microsoft lists Windows 11 26H2 build
family 26300 as a supported General Availability release. Candidate target:
Windows 11 Enterprise 26H2 x64, fully serviced, OS build recorded per run, on a
local NTFS volume. Support must be rechecked at implementation and deployment;
other editions/builds, ReFS, SMB, removable media, WSL/DrvFs and filter-managed
or virtual filesystems are excluded until separately validated. See Microsoft's
[supported client versions](https://learn.microsoft.com/en-us/windows/release-health/supported-versions-windows-client)
and [release information](https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information).

## Candidate acceptance profile

- Bootstrap opens and retains root and ancestor handles; binds VolumeSerialNumber,
  128-bit FileId (`FILE_ID_INFO`), filesystem name, owner SID, DACL, effective
  token SID/groups/privileges/integrity level and exact volume identity.
- All child operations use a reviewed handle-relative native wrapper. The wrapper
  must reject each reparse point/junction at every component and detect replacement
  races; `FILE_FLAG_OPEN_REPARSE_POINT` and post-open attribute checks alone are
  not assumed to make a multi-component walk race-free.
- Use explicit share modes that prevent untrusted replacement/deletion while
  handles are held. No named streams, device namespace, alternate data streams,
  DOS-device aliases or arbitrary caller-supplied names are accepted.
- Create staging/final objects with no-clobber semantics bound to the same volume.
  Collision is idempotent only for the same Operation ID and exact digest/length.
- `FlushFileBuffers` must be called on each relevant file handle. The backend
  must separately demonstrate namespace/rename metadata durability on the exact
  supported NTFS/storage stack; no directory-flush equivalence is assumed.
- DACL/owner changes, reparse findings, volume identity drift, sharing violations,
  unsupported APIs, ambiguous rename/flush outcomes, disk full, short write, or
  unknown error map to reject/`COMMIT_UNKNOWN`; no pathname fallback is allowed.

The exact OS build, ABI wrapper, no-clobber primitive, DACL race semantics,
metadata durability, crash/power-loss recovery and retained-handle revocation
remain `NOT_VALIDATED`. Microsoft API documentation establishes API behavior,
not backend safety. The profile remains blocked pending ABI/security review and
fault-injection on the declared NTFS stack. `FlushFileBuffers` documentation:
[Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers).
