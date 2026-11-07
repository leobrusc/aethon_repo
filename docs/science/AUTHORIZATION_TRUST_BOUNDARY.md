# Authorization trust boundary

`authorize()` remains the only supported issuer. It verifies all eight gate receipts, technical observations, reviewer/operator independence and launch intent before constructing and registering the exact base `Authorization`. Registration binds object identity and a snapshot digest of all dataclass fields.

`require_issued_authorization(value, subject)` rejects any type except the exact base class and invokes `Authorization.check(value, subject)` directly. The base check requires the registry entry to resolve to the same object, an unchanged field snapshot, matching subject digest and unexpired authorization.

The facade checks before deriving provenance or opening a backend. `StorageBackend.open_run` validates before manifest validation/capability minting. The synthetic backend repeats checks before run creation and for capability operations. `ReviewLedger` uses the same helper. Closing an issued backend capability remains owned-resource cleanup and does not create or extend authority.

This is an in-process application boundary. Arbitrary code executing in the interpreter can inspect or mutate module state and monkeypatch classes; this change does not claim to resist that attacker. MemoryBackend remains test-only. No native backend or production authorization is enabled.
