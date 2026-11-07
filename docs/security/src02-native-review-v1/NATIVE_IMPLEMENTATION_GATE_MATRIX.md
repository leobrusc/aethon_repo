# Native implementation gate matrix

No gate below is satisfied by the Phase 7A design review alone. `BLOCKED` means the design needs refinement before a safe prototype; `NOT_RUN` means native proof is not expected at this design stage.

| Gate | Current | Required closure evidence / acceptance criterion |
|---|---|---|
| G1 — Root bootstrap | BLOCKED | Signed/versioned provisioner receipt; independent trust anchor and revocation; measurable OS principal, root/ancestor/volume/filesystem/mount identity; fail-closed reopen and race tests |
| G2 — Commit model | BLOCKED | Correct model rejects missing object/journal/witness barriers; all legal crash-cut transitions checked; no inferred state repair |
| G3 — Inference intent | BLOCKED | Durable per-slot write-ahead state; crash before/after dispatch; any ambiguous dispatch becomes `interrupted_unknown`, never retried |
| G4 — Fencing | BLOCKED | Atomic commit-time epoch check; stale writer paused after precheck cannot publish; monotonic epoch survives restart/rollback via trusted authority |
| G5 — Witness | BLOCKED | Versioned authenticated CAS/ledger protocol; replay/equivocation handling; local/witness state table; idempotent timeout reconciliation and disaster recovery policy |
| G6 — Linux profile | BLOCKED | Exact kernel/filesystem/mount allowlist; `openat2` behavior; no-replace + file/directory `fsync` tests; OFD lease + fencing tests; crash/power-loss evidence |
| G7 — Windows profile | BLOCKED | Exact build/NTFS allowlist; audited handle-relative/reparse policy; no-clobber and metadata durability protocol; lock/fencing and restart fault tests |
| G8 — Post-collection review | REFINE | Separate grant issuer, reviewer keys/revocation, assignment/rubric validation, immutable vote/adjudication journal and quorum replay tests |
| G9 — Quotas/recovery | NOT_RUN | Native enforcement for bytes, inodes, journal/staging and bounded recovery on supported filesystems |
| G10 — Native adversarial matrix | NOT_RUN | Full matrix executed with pinned build/runtime/filesystem, raw logs and independent review |
| G11 — Scientific contract | PASS at design evidence scope | Preserve manifest v2/fingerprint, 24 cases/12 pairs/4-4-4, 120 slots and frozen B0–B4 semantics; separately test in any adapter |
| G12 — Operational gates | PENDING | All eight actual gates plus explicit run-specific authorization; no inference before this |

## Prototype entry criterion

Do not begin Linux prototype until G1–G5 are specified and independently accepted, supported local filesystem/kernel profile is selected, and the model’s false-commit path is removed. A later Linux-only synthetic/native prototype would still need a separate authorization and must not create production storage or run inference. Windows work remains a separate profile.
