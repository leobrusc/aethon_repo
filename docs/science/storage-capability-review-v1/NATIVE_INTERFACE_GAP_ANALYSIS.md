# Native interface gap analysis

The current protocol can express immutable object publication, verified reads, journal CAS, a head snapshot, writer scope and handle close. It is sufficient as a conceptual seam, not yet a complete Linux/Windows native-storage contract.

## Linux prerequisites

- Trusted bootstrap holds approved root and ancestor directory descriptors before untrusted inventory; bind `fstat` identity, owner, filesystem/mount policy and grant to every run.
- All object, checkpoint, event, head, lease, recovery and cleanup operations remain descriptor-relative; use reviewed `openat2` resolution constraints and no unsafe pathname fallback.
- Define no-replace publication, file and containing-directory synchronization order, durable receipt schema, disk-full/partial-write behavior and object-before-journal ordering.
- Test process death, kernel crash/power-loss and supported filesystems/mount options. Keep ambiguous inference outcomes `interrupted_unknown` and never retry automatically.
- Add independent authenticated monotonic freshness witness checked before resume if coherent rollback is in threat scope.
- Enforce the complete frozen scientific manifest (SCI-REV-01) before minting a capability.

## Windows prerequisites

- Trusted bootstrap retains real directory/ancestor handles and binds approved volume/file identities; no pathname reopen to recover authority.
- Reviewed handle-relative opens, share modes, DACL/owner verification, revocation assumptions, reparse/junction/mount/ADS/device/UNC policy.
- Same-volume no-clobber publication and a tested `FlushFileBuffers` journal protocol; state what metadata durability is and is not established.
- Adversarial replacement/rename, concurrent handle, crash/power-loss and supported NTFS build tests. No Python `Path`/`st_mode` substitute.
- Same independent freshness and manifest requirements as Linux.

## Cross-platform contract changes before implementation

1. Make root capability and trusted bootstrap explicit in backend construction; current `open_run(authorization, manifest, budget)` has no root identity parameter and cannot prove root custody.
2. Return a typed commit result that distinguishes durable commit, not committed, and uncertain; current `WriteReceipt.durability` is an unvalidated string with a synthetic default and no required commit state.
3. Define backend restart/reopen semantics for a new process, capability renewal/revocation, and external freshness witness protocol.
4. Separate collection authorization lifetime from a separately approved post-collection review grant. Current facade checks the original authorization expiry on all operations, so human review after collection expiry cannot safely persist votes without an explicit new scoped authorization design.
5. Specify atomic object+event or recoverable intent semantics, durable operation receipt retention, object orphan handling, close/lease abandonment and bounded scan behavior.
6. Define actual byte/metadata/CPU quota accounting; Python object overhead and native metadata are not currently represented by logical byte budgets.
7. Require all full frozen case/pair/family/schedule validation before capability issuance (SCI-REV-01).

No adapter, OS primitive, ACL, root directory, egress policy or durability guarantee was implemented or tested in this review.
