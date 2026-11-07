# Linux native confinement contract

## Supported profile is explicit

An implementation must publish an allowlist of kernel versions, architecture, local filesystem type, mount options, namespace policy, and storage stack actually tested. Initial support is limited to a validated local filesystem profile. NFS, FUSE, SMB, overlay filesystems, WSL DrvFs, unknown bind mounts and network filesystems remain unsupported until separately tested. No fallback to `Path`, string concatenation, shell commands or reopening a root pathname is permitted.

## Root and lookup

Trusted bootstrap opens and retains descriptors for the approved root and every ancestor whose identity/permissions are part of the policy. It records `fstat` device/inode, owner, mode, filesystem/mount identity and mount-namespace evidence. The implementation must account for inode reuse and must not use `(st_dev, st_ino)` alone as a permanent freshness token. Ancestors must not be writable by untrusted principals. Mount namespace and mount topology are checked against the approved profile; unexpected changes fail closed.

All child lookups are relative to held directory descriptors through reviewed `openat2` calls using `RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS | RESOLVE_NO_MAGICLINKS`; `RESOLVE_NO_XDEV` is required unless a narrowly specified, independently approved subordinate mount policy says otherwise. The implementation must reject absolute paths and `..`, verify each opened object with `fstat`, type, owner, link count and expected identity. Mutations use descriptor-relative syscalls and retained parent descriptors. `O_NOFOLLOW` on one final component is not a substitute for the full resolver policy.

If `openat2` or required resolve flags are unavailable, unsupported or return an ambiguous race/error, the backend returns unavailable/rejected and creates no run. There is no silent downgrade. Retained descriptors prevent pathname substitution from redirecting later operations but do not guarantee confidentiality against a process that already has access or prove that the object remains at an expected name.

## Publication and durability prerequisites

Create staging objects exclusively in the same approved filesystem. Write bounded bytes, verify exact digest/length, synchronize the object, publish using a tested no-replace primitive, then synchronize the containing directory before a durable receipt can be considered. A journal event may reference only objects whose publication durability has been established. Head publication follows journal durability and is itself synchronized. Exact ordering and error mapping are specified in `DURABLE_COMMIT_STATE_MACHINE.md`.

No-replace behavior must be verified on every supported filesystem and kernel combination. Any cross-device result, collision, unexpected link count, write/flush error, or uncertain rename/link outcome fails closed. Cleanup is descriptor-relative, limited to backend-owned objects, and never runs a broad recursive pathname delete.

## ACL/permissions and limits

The dedicated collector identity has least privilege and no administrative rights. Root/ancestor owner and mode are checked at bootstrap and before security-sensitive transitions. Permission changes are treated as policy invalidation; existing open descriptors may continue to work, so the design requires an operational control preventing untrusted ACL/owner mutation and does not claim instantaneous revocation. OS quota/project quota plus logical per-run counters are both required; counters alone are not physical quotas.

## Required native fault tests

Test symlink/magic-link traversal, `..`, mount crossing, root rename/replacement, ancestor replacement, link-count tricks, no-replace collision, concurrent writers, disk-full, `ENOSPC`, `EDQUOT`, short writes, `EIO` during each sync, process crash after every commit step, reboot/power-loss behavior on exact stack, permission changes with held descriptors, and recovery with external witness disagreement. Any unclassified result is `COMMIT_UNKNOWN` and blocks resume. These are future native tests, currently `NOT_RUN`.
