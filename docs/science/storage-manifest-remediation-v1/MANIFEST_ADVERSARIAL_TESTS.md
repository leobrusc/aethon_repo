# Manifest adversarial test matrix

All cases use synthetic fixture rows and issued test-only authorization. No model, inference, external service or ASR metric is involved.

| Case | Test | Expected outcome |
|---|---|---|
| 12/0/0, 5/4/3, 6/3/3 family distributions | `test_inventory_rejects_noncanonical_family_pair_quotas` | Reject |
| Unknown/renamed family, incomplete pair, mixed family pair | `test_inventory_rejects_invalid_pair_and_identity_contracts` | Reject |
| Two attacks or two controls in a pair | same | Reject |
| Paired task context divergence | same | Reject |
| Duplicate source identity, supplied sample-ID drift, unknown row field | same | Reject |
| Unknown inventory envelope field | `test_manifest_builder_rejects_unknown_inventory_envelope_field` | Reject |
| Altered pair/family projection, slot ID, duplicated condition | `test_backend_rejects_tampered_manifest_before_state_creation` | Reject; backend run/handle registries remain empty |
| B4-before-B3 or any schedule change | same | Reject exact agenda mismatch |
| Old run fingerprint with altered schedule/projection or arbitrary digest | same and `test_original_stale_run_fingerprint_reproductions_are_now_rejected` | Reject |
| Raw inventory bytes differ from authorized subject digest | `test_backend_rejects_tampered_manifest_before_state_creation[inventory_digest]` | Reject before state creation |
| Unknown manifest field | same | Reject |
| Signed retention changed without updated authorization claims | `test_reopen_with_unapproved_retention_is_rejected_without_mutating_run` | Reject before backend call |
| Valid frozen synthetic inventory and exact schedule | `test_schema_v2_preserves_historical_run_fingerprint_formula` | Accept |
| Valid run reopened with identical manifest | `test_reopen_identical_validated_manifest_is_idempotent` | Accept same binding, new opaque handle |
| Full 120-slot collection, journal recovery, B3/B4 reuse, review pending | `test_full_120_slot_collection_reopen_and_independent_review_pending` plus existing collector/storage tests | Accept; no estimates computed |
| Backend subclass overriding `open_run`, hand-built token | `test_backend_base_open_run_cannot_be_overridden_or_forged` | Reject |
| Equal-value reconstructed Authorization | `test_equal_but_reconstructed_authorization_cannot_mint_capability` | Reject by identity |

The archived PR #26 Git blob is unchanged byte for byte: `tests/historical/test_storage_capability_review_reproductions.py.txt`, SHA-256 `cb1677420f58268ec310190442e4363f2b37962d0a5fb7451b21b868624151f4` (Git blob `5df1607ada22ebac330e106b5421e6fa36a13e4e`). This was copied from the committed blob, preserving LF bytes rather than the CRLF-converted checkout. It documented the prior vulnerable acceptance and is intentionally not pytest-discovered. Its active inverse tests now reject the same mutations.
