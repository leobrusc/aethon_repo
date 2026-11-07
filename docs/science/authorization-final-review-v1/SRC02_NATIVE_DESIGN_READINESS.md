# SRC-02 native design readiness

## Disposition

**`NATIVE_CONTRACT_REFINEMENT_REQUIRED`.** AUTH-REV-01 closure does not authorize
or validate a production storage backend. The current in-memory backend is a
synthetic test implementation and provides no filesystem durability, ACL,
encryption, interprocess isolation, or anti-rollback guarantee.

## Requirements still needed before native implementation

1. **Independent root bootstrap:** identify the provisioner and independent
   trust anchor; define accepted filesystem/device identity, mount policy,
   ancestor checks, and permissions before opening the root.
2. **Root and directory identity:** define held-handle semantics, symlink/
   junction/reparse policy, stable object IDs, ancestor replacement defense,
   and ACL-change behavior for Linux and Windows separately.
3. **Durable commit contract:** specify no-replace publication, data/journal/head
   flush ordering, directory durability, and `COMMITTED`, `NOT_COMMITTED`, and
   `COMMIT_UNKNOWN` outcomes after crashes.
4. **Journal and recovery:** define partial write, truncation, corruption,
   orphan object, checkpoint, and replay rules. An uncertain inference must
   never be silently repeated.
5. **Cross-process writer leases:** define OS-backed lock/lease semantics,
   owner-death handling, stale lease recovery, expiry, contention, and process
   identity. Thread tests are insufficient.
6. **Freshness/rollback witness:** a local hash chain cannot detect replacement
   of the complete store with an older valid copy. Specify an independent
   monotonic witness or transparency service and failure behavior.
7. **Expiry and revocation across restart:** define how revocation is observed
   while a run is open and after collector restart; process-local authorization
   bookkeeping is not enough.
8. **Real resource limits:** bind disk, inode, journal, event, object, and
   checkpoint quotas to the private root/run; define fail-closed exhaustion and
   retention cleanup.
9. **Post-collection scientific review:** define reviewer access, durable
   votes/adjudication, key revocation, retention, and audit after the collector
   exits.
10. **Native fault validation:** plan replacement races, symlink/reparse tests,
    permission changes, crash injection, flush failures, restart recovery,
    rollback detection, and proof that uncertain inference is not repeated on
    each supported filesystem.

No Linux or Windows backend was implemented or exercised in this review.
`SRC-02 NOT_AUTHORIZED` remains in force.
