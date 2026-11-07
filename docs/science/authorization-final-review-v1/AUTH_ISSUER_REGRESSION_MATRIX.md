# Authorization issuer regression matrix

CI evidence is run `42398791189` on the implementation commit named in the
independent review. The local focused pytest run printed twelve passing test
markers but did not exit cleanly; its process was interrupted and is not counted
as a clean local PASS.

| Attempt | Expected / observed | Evidence |
|---|---|---|
| Subclass overrides `check()` with `None` | REJECT; no run or handle | `test_unissued_authorization_subclass_cannot_open_facade_or_backend`; CI |
| Subclass overrides `check()` with `True` | REJECT; no run or handle | Same parametrized test; CI |
| Dataclass clone with equal values | REJECT | `test_equal_dataclass_clone_and_manual_base_instance_cannot_open_run`; CI |
| Manually constructed exact base object | REJECT | Same test and direct API-route test; CI |
| Copied fields from legitimate authorization | REJECT unless the original object identity was issued | Original private-issuer proof now fails on removed import; active tests cover clones/manual base objects |
| Mutated frozen-object snapshot fields | REJECT | `test_mutated_issued_authorization_snapshot_is_rejected` for policy, receipts, launch, retention; CI |
| Changed subject | REJECT | `test_subject_change_and_unissued_copy_do_not_create_state`; CI |
| Expired authorization | REJECT for use; owned close remains permitted | Existing expiry/owned-close storage tests; CI |
| Foreign, copied, or closed storage capability | REJECT | Existing storage capability tests; CI |
| Unissued authorization used in `ReviewLedger` | REJECT before review access/write | `test_application_api_has_no_direct_issuer_registration_route`; CI |
| Old issuer token/helper/module registry/factory imported | UNAVAILABLE | `hasattr` assertions and unchanged original script `ImportError`; CI plus direct replay |
| Direct base authorization use through facade/backend | REJECT before run state | Direct API-route test asserts backend run/handle maps remain empty; CI |
| Legitimate authorization from `authorize()` | ACCEPT | `test_legitimately_issued_synthetic_authorization_preserves_full_storage_cycle`; CI |
| Full synthetic legitimate lifecycle | ACCEPT: 120 slots, idempotent write, journal, close/reopen, review pending | Same positive lifecycle test; CI |

All authorization fixtures are synthetic. No real gate approval, pilot,
inference, ASR, or scientific efficacy estimate was created by these tests.
