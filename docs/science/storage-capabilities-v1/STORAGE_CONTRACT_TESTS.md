# Synthetic storage contract evidence

Final full suite: **370 PASS**, one expected mocked model-load warning. No actual model download/inference occurred. The new module expands to **48 contract cases**, in addition to the 322 existing suite cases. Existing collection/review tests use the shared test-only memory backend. No results from these fixtures estimate ASR, efficacy or power.

| Requirement | Tests in tests/test_storage_capabilities.py / existing tests |
|---|---|
| Full matrix, deterministic B0–B4 and resume | full_120_slot_collection_reopen_and_independent_review_pending; existing complete_120_slots_and_idempotence/order/partial_resume/native_security_review |
| No persistence pathname escape | backend_and_facade_never_use_filesystem patches builtins.open/os.open/Path methods while opening, writing, reading, journaling, closing and reopening; facade_ast_has_no_path_persistence_and_history_is_preserved |
| Structured/issued identities | unstructured_identifiers_rejected; unknown_well_formed_checkpoint_cannot_expand_inventory; capabilities_cannot_be_issued_by_flags; foreign_backend_and_copied_capabilities_rejected; fake_authorization_never_mints_backend_capability |
| Complete fingerprint binding | manifest_reads_are_defensive_and_complete_binding_enforced; object_cannot_be_replayed_under_different_capability_budget; malformed_120_slot_manifest_never_opens; backend_rejects_unsupported_manifest_version; existing foreign-run copied checkpoint/object tests |
| No clobber/idempotency | idempotent_bytes_and_checkpoint_overwrite_rejection; same_operation_different_bytes_and_stale_head |
| Logical concurrent access | logical_concurrency_and_owned_lease_cleanup uses another thread; existing concurrent_writer_lock_not_removed_automatically and factory lock test |
| Interruption/partial persistence | fault_boundaries_and_idempotent_retry at put/append before/after commit; existing inference/evaluation interruption and durable_response reconciliation |
| Corruption/conservative recovery | missing_object_and_checkpoint_corruption_are_explicit; conservative_recovery_rejects_inconsistent_journal; failed_recovery_cannot_export_partial_accounting |
| Bounded resources | invalid_resource_budgets_rejected; object_event_total_and_structure_quotas; total_bytes_and_operation_count_are_bounded |
| Cleanup and fail-closed production | expired_authorization_still_allows_owned_cleanup; cli_never_selects_memory_or_invokes_native_bootstrap; legacy_path_hook_cannot_activate_even_with_synthetic_backend |
| Scientific review/reuse | Unchanged ReviewLedger two-vote/adjudication tests, B3/B4 divergence/token-interval/judge isolation tests; all part of full suite |

The interface's memory backend performs no filesystem, ACL, encryption, network or subprocess operation. Threads exercise logical exclusion/CAS, not cross-process or native filesystem races. Memory fault injection is trusted test instrumentation (inspect/fail_next), not part of StorageBackend or the production CLI. No false production security assurance follows from these passes.

## Migration and historical evidence

The previous implementation and test modules are archived from exact parent Git blobs before editing (historical/index.json). Original PR #17 reproductions and their existing SHA index are unchanged. Current path-dependent atomic-write/corruption/lock/cross-run tests were migrated to backend-owned state/fault injection. Tests for stale native path observations now demonstrate that no legacy path/confinement hook can activate storage; they do **not** certify detection of native inode/ACL/junction races. No old failure was hidden by deleting its source.

The complete rollback limitation remains an explicit test: coherently clearing the synthetic journal, objects, operation receipts and used-byte accounting permits a pristine-looking replay. This is the documented need for an independent monotonic witness, not a PASS for rollback defense. Interrupted inferred output is never invented or counted as successful.

The first targeted run had 91 PASS and one seal mismatch after code changed; only engineering implementation seals were updated. A later targeted run passed129. An intermediate full suite passed365 and369; final hardening added the complete-grant replay case and the final complete suite passed370. Exact final logs/hashes are retained under evidence/. No need to replay historical unsafe pathname code to claim a native fix.

Offline Python audit records zero test network events. This audit is not an OS egress sandbox and does not establish arbitrary native/subprocess isolation. Existing SRC-01 rejection tests remain active; no dependency/crypto verifier implementation was enabled.
