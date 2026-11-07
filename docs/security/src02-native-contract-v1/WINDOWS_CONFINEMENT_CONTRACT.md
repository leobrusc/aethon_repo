# Windows confinement contract

## Supported profile

Publish an explicit allowlist for Windows build, architecture, NTFS version/volume configuration, storage stack and security policy. Initial scope excludes UNC paths, device namespaces, alternate data streams, junctions, mount points and any unsupported reparse tag unless a separately reviewed profile permits one. No claim extends from NTFS to ReFS, SMB, removable media, cloud-synced folders or filter-driver stacks without tests.

## Bootstrap and handle-relative operations

Trusted bootstrap acquires and retains real directory handles for root and relevant ancestors. It binds `FILE_ID_INFO` (VolumeSerialNumber and FileId), volume/filesystem identity, owner and DACL/security descriptor policy to the independent receipt. File IDs identify an object on a volume; they are not an access grant, proof of freshness, or protection against deletion/reuse.

Every child operation must be relative to a retained directory handle using an audited native handle-relative open implementation (for example a reviewed `NtCreateFile` wrapper with a documented ABI). The implementation must define `OBJECT_ATTRIBUTES.RootDirectory`, relative-name grammar, desired access, create disposition, share modes, object type, and reparse handling. It must reject absolute names, `..`, DOS/NT device namespaces, UNC, ADS, unexpected reparse points, volume changes and any path-resolution ambiguity. `CreateFile` flags on a full pathname alone do not establish all-ancestor confinement. No fallback to pathname-based Python I/O is allowed.

After open/create, query identity and security information through the same handle and compare to policy. Retain parent handles across publication. Share modes must deny incompatible replacement/deletion where required, while recognizing that administrator/kernel actions and existing handles are separate trust concerns. DACL/owner changes invalidate the grant; a prior ACL snapshot does not freeze permissions or guarantee revocation of already-open handles.

## Publication and flush

Staging and final objects must be on the same approved volume. Create final names with a tested no-clobber disposition, verify exact bytes and file identity, and flush file contents with `FlushFileBuffers` before publishing references. Define and test the metadata/directory-entry durability protocol for the exact Windows/NTFS/storage stack; do not claim equivalence to Linux directory `fsync`, and do not equate a successful file flush with guaranteed survival of every power loss. If required metadata durability cannot be demonstrated, return `COMMIT_UNKNOWN` or refuse the profile; never emit a durable receipt.

Cleanup must be handle-bound, identity-checked and restricted to records owned by this run/backend. It cannot delete a path discovered by scanning an attacker-controlled namespace.

## Required native fault tests

Test junction/reparse swaps, parent rename/replacement, volume changes, ADS/device/UNC rejection, concurrent opens/share-mode behavior, DACL changes, no-clobber races, cross-volume moves, `FlushFileBuffers` failures, disk full, process crash at every stage, reboot/power-loss evidence on the exact stack, handle closure/reopen, lock owner death, and recovery against a stale witness. Tests on Linux or memory backends do not validate Windows guarantees; native validation is `NOT_RUN`.
