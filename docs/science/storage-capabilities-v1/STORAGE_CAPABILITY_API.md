# SRC-02 opaque storage capability API

Technical disposition: **STORAGE_INTERFACE_READY**. Production storage is disabled; SRC-02 has no operational authorization. This is the API refactor required by [SRC02_STORAGE_DECISION.md](../../../SRC02_STORAGE_DECISION.md), not native confinement validation.

## Inventory and replacement boundary

The source at PR #24 `2dc16eb53d93336318a8e23c428cc0542656d25d` used a `confinement.check(root, identity)` hook around pathname operations. That left mkdir/open/link/read/unlink, journal scans, pointer files, writer.lock and recovery outside an object-bound backend. The old implementation and three affected test modules are preserved byte-for-byte under historical/, with parent SHA and hashes in index.json. Previous PR #17 reproduction archives are unchanged.

| Component | Responsibility after refactor |
|---|---|
| pilot_storage_backend.py | Protocol, opaque identity handles, structured keys/operation IDs, receipts/head snapshots, quotas and explicit error types |
| pilot_storage_facade.py | Collector state machine/accounting, canonical run-scoped objects/checkpoints and domain replay; no filesystem operations |
| pilot_storage.py | Compatibility imports only; no legacy writer or immutable_write fallback |
| pilot_storage_probe.py | Existing read-only root/ACL/encryption diagnostics; never a root capability or persistence authorization |
| tests/pilot_memory_backend.py | Sole implementation: volatile in-memory synthetic contract backend; excluded from installed aethon packages |
| pilot_runtime.collect_runtime | Unconditionally rejects production collection before storage/model bootstrap; no backend CLI selector |

All **run persistence** reads/writes, journal scans, leases/locks, recovery and owned cleanup cross the backend. Read-only configuration/model/receipt/rubric/evidence input loaders remain separate inputs under their existing governance contracts, not a second run-store I/O path. They cannot issue a native storage capability. B0–B4 algorithms, generation contracts, signed receipt formats and review quorum logic are unchanged.

## Operations

| Operation | Contract |
|---|---|
| open_run(authorization, canonical_manifest_bytes, budget) | Verify issued live authorization, narrow run ID, complete manifest/config/120-slot schedule and immutable full binding; mint an identity-only capability in backend registry |
| put_if_absent(cap, StorageKey, bytes, OperationId) | Immutable publication; same operation/same intent returns its receipt, different intent collides; exact bytes preserved, never silently repaired |
| get_verified(cap, StorageKey) | Verify digest/envelope and complete run/manifest/checkpoint binding before returning bytes; missing checkpoint is None, missing referenced object is an explicit failure |
| append_event(cap, expected_sequence, previous_hash, canonical_event, OperationId) | Compare-and-append, hash chain and correlated committed-event receipt; idempotent retry lookup before CAS |
| read_head(cap) | Bounded consistent verified journal snapshot and recovery disposition; reject gaps, foreign binding, corruption and partial commit/resource accounting |
| writer(cap) | Additional backend-owned exclusive writer lease covering collector initialization/collection/review transaction; no client pathname lock or cleanup |
| close(cap) | Idempotent owned handle/lease cleanup; never removes another handle's lease; permitted even after authorization expiry |

Future native backend instances must receive an independently issued **root object capability** and approved resource/freshness policy through a trusted bootstrap constructor. open_run must not resolve a root pathname supplied by inventory. This phase supplies no such constructor or native root capability. The synthetic backend's per-instance registry is an API model, not proof of physical root identity or an independently approved resource grant.

RunCapability carries no public run/path/token fields. A constructed, copied, foreign-backend or closed handle is not in the issuing registry and is rejected. This does not resist hostile Python reflection or process/host compromise; it prevents data/flags/pathnames from acting as capabilities in the supported API.

StorageKey has only object/content SHA-256 or checkpoint/(sample-or-slot SHA-256, request|response|evaluation). Checkpoints must belong to the immutable 120-slot matrix; request keys use sample IDs, response/evaluation keys use slot IDs. No absolute/relative filenames, streams, devices, separators or arbitrary inventory paths are lookup arguments. Run IDs have a bounded ASCII grammar. Operation IDs are narrow SHA-256 identities scoped by the backend's run binding and complete intent.

## Binding and scientific bytes

All object/checkpoint envelopes bind the full immutable manifest digest, existing run_fingerprint and complete backend grant binding (including the immutable budget). Native grant bindings must additionally include actual approved root identity; the synthetic backend has no physical root authority. The manifest includes subject, config, inventory digest, retention, deterministic schedule, all slots and authorization provenance. Resource budget is also bound at open. Changes collide on reopen even when an attacker retains the old run_fingerprint. Receipt operation IDs, binding, bytes/hash, sequence and committed event are checked by the facade. No existing filesystem store is automatically migrated or repaired.

Canonical finite JSON, depth/node/string/byte bounds, typed keys and byte-for-byte idempotence are enforced. Inventory strings remain scientific data; they never select storage filenames. The 120 slots and original transitions remain represented, including no_response, truncation, errors, interrupted_unknown and pending human review. A callback cannot complete scientific review. B3/B4 reuse/effective-input checks stay in the unchanged collector.

The facade is a transaction-local materialized view. writer() refreshes it from read_head; explicit load() refreshes it between transactions. Independent users of a store must not treat an old view as a fresh concurrent snapshot. Journal mutations use CAS and foreign writer leases reject mutation. Failed recovery poisons that facade until it is closed/independently inspected; no partial accounting report is accepted from it.

## Limits and recovery

Default per-run limits: object/manifest 2 MiB each, event 64 KiB, total canonical bytes 32 MiB, 2,048 stored objects/checkpoints, 4,096 events, 8,192 operations. Hard maxima and JSON depth48/node100,000 limits are explicit in ResourceBudget/bounded_json. The synthetic backend additionally limits runs16, active handles64 and lifetime handles1,024. These are bounded logical records/bytes, not a precise Python heap/CPU quota or an operationally signed budget.

Before-commit interruption leaves no accepted mutation; after-commit lost acknowledgment retains exactly one committed result and retry returns the same receipt. Unreferenced accepted objects are retained conservatively, not swept outside the backend. A started inference without durable response remains interrupted_unknown and is not retried automatically. No facade code opens, scans, deletes or recovers a path. Complete coherent rollback of the entire synthetic state remains undetectable without an independent witness.

**PILOT_BLOCKED**, eight real gates PENDING, **DEPENDENCY_APPROVAL_REQUIRED** unchanged. No synthetic receipt/capability selects a production backend or bypasses SRC-01.

Existing collector reason labels containing durable are protocol intent markers only in synthetic tests; their presence does not establish persistence. The synthetic receipt explicitly reports SYNTHETIC_VOLATILE_NOT_PRODUCTION. A native backend must demonstrate actual durable acknowledgments before any separately approved operational integration.
