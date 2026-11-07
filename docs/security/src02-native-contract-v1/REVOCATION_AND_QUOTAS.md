# Revocation, expiry and resource quotas

## Authorization after restart

Python object identity and process-local issuer registries do not survive restart and cannot authorize reopening. Reopen requires fresh bootstrap of RootCapability, full manifest/fingerprint and grant verification, independent signature/receipt verification, live authorization policy, revocation status, current expiry, lease, witness checkpoint and run state. The reissued process capability is new and scoped to the exact prior run/root/manifest/grant; it cannot expand scope or extend retention.

Revocation is checked at bootstrap, lease acquisition, before every mutating transaction, before sensitive reads, and at bounded intervals during long operations. If revocation occurs, stop scheduling, cancel at safe boundaries, prevent new commits, close owned handles and leases. In-flight writes become `COMMIT_UNKNOWN` until reconciled. Expiry does not erase evidence or imply commit; close remains limited to releasing resources already owned by that capability.

## Quota dimensions

Bind both logical limits and OS-enforced limits to the root/run grant:

| Dimension | Accounting / enforcement |
|---|---|
| Persisted bytes | Exact object + manifest + journal + checkpoint bytes; filesystem/project quota reserves metadata overhead |
| Object/checkpoint count | Backend index and hard count ceilings; reject before staging |
| Events/operations | Monotonic counters and bounded receipt retention; no reuse of IDs with changed intent |
| Journal growth | Maximum records/bytes; checkpoint compaction only as a versioned transaction preserving hash/witness continuity |
| Metadata/inodes | OS quota or dedicated filesystem allocation; logical object count alone is insufficient |
| Temporary space | Separate staging allowance; reserve before operation and reclaim only owned uncommitted staging after safe recovery |
| Pending operations | Bound concurrent in-flight work; stop new work at limit |
| Recovery | CPU, bytes scanned, wall-clock and retry budget; exhaustion leaves store blocked and unchanged |

Quota reservation is itself serialized under the writer lease and committed in the journal. Any quota or disk exhaustion fails closed before starting a new external effect. If exhaustion occurs after an effect may have started, mark that slot uncertain; never retry inference as a storage remedy. Logical counters are not physical quotas. OS quota behavior and metadata accounting must be tested on each supported filesystem.

## Retention

Retention deadline, custodian, backup scope and deletion evidence are part of the immutable grant. Deletion requires its own authorized, handle-bound transaction and audit receipt; it must not erase witness history or other runs. File unlink is not proof of erasure from snapshots, backups, SSD remapping or media. Those claims require separate custodian evidence and remain operational gates.
