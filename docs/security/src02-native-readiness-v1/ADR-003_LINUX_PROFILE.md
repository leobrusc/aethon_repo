# ADR-003 — narrowly scoped Linux local filesystem qualification

Status: **PROPOSED_NOT_APPROVED**, not a selected or qualified platform. No native source code, device mounts, root directory or process permissions are changed.

## Candidate allowlist for a future isolated laboratory
- Linux x86_64, **single host**, dedicated non-admin collector identity.
- Locally mounted ext4 filesystem as *candidate*, with exact kernel build, distro, mount and journal options, block device, storage cache/flush capabilities, namespace topology and test image fingerprint recorded before approval.
- No NFS, SMB, FUSE, overlayfs, WSL/DrvFs, unknown bind mounts or shared/network storage; no silently substituted filesystem. Actual Linux kernel versions and ext4 mount options are **NOT_SELECTED/NOT_VALIDATED**, not wildcards for approval.
- Kernel/system calls `openat2`, `renameat2`, `fsync`, descriptor-relative operations and OFD locks are *candidates*, not proof of semantics for the certified stack.

## Path and identity confinement
A trusted bootstrap retains root and policy-relevant ancestor directory FDs after confirming approved identities/permissions, namespace and mount topology. Child lookups must be strictly relative to owned descriptors with `RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_XDEV` when all crossing is forbidden; refuse absolute paths, dot-dot escape, symlink/magic links, unexpected mounts, inode identity drift and mutable ancestry. Validate open results by descriptor, never trust caller-supplied path reconstruction. Unsupported syscall/flag/FS returns an error; no `Path` or shell fallback.

## Publication and durability
Durable intent BEFORE external inference dispatch; response bytes/digest and operation identity immutable. Stage on same filesystem, write bounded bytes and `fsync`; publish with experimentally qualified no-replace semantics; `fsync` parent directory; append exact journal record and synchronize; publish head via serialized, epoch-aware authoritative compare-and-swap; synchronize head and containing namespace; update required external witness; return `COMMITTED` **only** after all certified barriers and checks. Unknown crash or I/O outcomes become `COMMIT_UNKNOWN`, and possible model side effects must not be retried.

**Critical implementation issue:** a pair of POSIX operations (check epoch; then rename) is not an atomic fencing authority. The engineering review must pick and test a single serializer for epoch transfer and head publication. `F_OFD_SETLK` is only a local cooperative exclusion candidate and does not itself provide durable monotonic fencing. If the serializer cannot be demonstrated, do not prototype writer takeover.

## Fault-injection qualification required
Cover T01–T19 as applicable, especially T01–T07, T09–T14, T16/T17 and T19. Test power loss/crash at every barrier with real stack evidence, symlink/rename/mount races, stale process handles after lease transfer, inode reuse, owner/mode drift, disk-full/short write/`EIO`/`EDQUOT`, idempotent recovery and no inference replay.

## Authorization prerequisites
Record exact OS/kernel/FS/mount/storage profile; approve owner and budget for an **isolated fixture-only** implementation; approve dependency and root/witness components separately; obtain independent review of fencing/witness/commit atomicity. Until then `LINUX_PROFILE_NOT_VALIDATED` and `SRC-02 NOT_AUTHORIZED`.

Reference source contracts: `LINUX_CONFINEMENT_CONTRACT.md`, `INTERPROCESS_LEASE_CONTRACT.md`, `DURABLE_COMMIT_STATE_MACHINE.md` and `NATIVE_ADVERSARIAL_TEST_MATRIX.md`.
