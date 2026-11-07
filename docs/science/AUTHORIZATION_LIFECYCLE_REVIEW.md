# Authorization lifecycle review

## Observed paths

`authorize()` verifies gate receipts and launch intent, constructs `Authorization`, then invokes `_record_issued_authorization`. `PrivateRunStore.__init__` and `StorageBackend.open_run` require the exact base type and call the shared base verifier. `MemoryBackend._open_validated_run` repeats verification before inserting run state; `_state` repeats it for reads, writes, journal, and writer leases. `PrivateRunStore.guard` revalidates before facade operations. `ReviewLedger.__init__` and vote verification revalidate. `close()` removes only a capability key found in that backend's own handle map and does not issue authority.

## Lifecycle observations

- Reopening identical manifest/budget is covered by synthetic storage tests.
- Foreign, copied, and closed capabilities are rejected; closing an expired owned handle is allowed for cleanup.
- The memory backend's `RLock` and lease cover logical in-process writers only. They do not establish process isolation or native filesystem durability.
- The registry snapshot covers every dataclass field and detects ordinary frozen-dataclass mutation. The weak reference must resolve to the identical object; a stale entry with a collected object cannot validate a new object solely through id reuse.
- A malformed entry fails by exception before state creation; the current code does not normalize every malformed registry exception into `PermissionError`, but the failure is closed.
- There is no explicit revocation service/state. Expiry is the available time-bound check; immediate revocation/freshness is a native-contract requirement.

## Blocking lifecycle gap

Registration is not actually confined to `authorize()`: a caller can import `_AUTHORIZATION_ISSUER` and `_record_issued_authorization`, register a fresh base instance with copied values, then pass all lifecycle checks. This demonstrated route must be removed or otherwise excluded from the ordinary caller surface before declaring issuance exclusive.

## Threat-model boundary

No Python-level result here resists arbitrary code in the same interpreter, class/module monkey-patching, memory inspection, or host compromise. The private-issuer reproduction is narrower: it uses existing Python-level module names and calls the registration helper; it does not patch the interpreter or storage backend.
