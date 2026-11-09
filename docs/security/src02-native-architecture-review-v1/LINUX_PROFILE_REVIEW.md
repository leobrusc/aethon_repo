# ADR-003 — Linux confinement and persistence review

Disposition: `REVISE_AND_QUALIFY_PLATFORM` (ARCH-REV-04).

Proposed x86_64, single-host, local ext4 is only a candidate; neither precise kernel nor mount/storage stack is fixed. The contract correctly forbids network, overlay, FUSE and WSL substitutes.

## Kernel and filesystem contract review

- `openat2` with `RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_XDEV` is a candidate descriptor-relative confinement primitive; reject unsupported flags, absolute/parent escapes and changed mount topology.
- `renameat2(RENAME_NOREPLACE)` is a candidate for no-clobber namespace publication, not a native atomic compare-and-swap combining lease epoch, expected journal head and a no-replace rename.
- `fsync` on each newly created file and enclosing directory is necessary to target metadata persistence. It does not alone demonstrate power-loss durability for the selected block device/controller/cache stack.
- `F_OFD_SETLK` is a candidate advisory exclusion mechanism; it does not prove monotonic durable fencing or enforce trust against an uncooperative writer already holding a descriptor.

## Required exact profile and test evidence

Owner must record exact distribution, kernel build, architecture, filesystem, mount options, block device, disk cache/flush settings, user/mount namespaces, collector UID/GID/capabilities, relevant security modules, quota, toolchain and binary SHA. Permit only tested combinations.

Run T01–T19 as applicable after separate fixture-only authorization, especially symlink and mount races, root replacement, stale-FD writer after lease transfer, journal/head flush ordering, EIO/ENOSPC/EDQUOT, power loss at every barrier, and unknown inference outcome. Current status for all native tests is `NOT_RUN`.

No native syscall, filesystem provisioning or hardware testing was performed in this review.
