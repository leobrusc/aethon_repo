# SCI-REV-01 closure matrix

Reviewed code: PR #27 HEAD `2034aade9b56bf76ff13f4816a5ff9de73a879a6`.

| Check | Evidence | Result |
|---|---|---|
| Validate before `RunCapability` issuance | `StorageBackend.open_run` validates before `_open_validated_run`; invalid manifests leave synthetic backend state empty | PASS |
| `StorageBackend.open_run` subclass bypass | Ordinary and multiple-inheritance `open_run` overrides rejected; `ValidatedRunManifest` constructor is sealed | PASS for the reviewed backend subclass contract; hostile reflection/monkey-patching remains out of model |
| Authorization subclass bypass | Unissued `Authorization` subclass overrides `check()` with a no-op; `PrivateRunStore` and base backend dynamically dispatch it, then issue a synthetic capability for a valid manifest | FAIL — separate high-severity `AUTH-REV-01`; does not bypass scientific-manifest validation, but blocks operational authorization and native backend work |
| 12/0/0, 5/4/3, 6/3/3 family distributions | Parameterized synthetic rejection tests | PASS |
| Pair integrity and context | Incomplete pair, two attacks, two controls, mixed family, context drift, duplicate identity and unknown fields rejected | PASS |
| 24 cases / 12 pairs / five arms | Builder and validator reconstruct exact case projections | PASS |
| 120 slots, no extra/missing/duplicate conditions | Slot list must equal regenerated projection; count and unique IDs checked | PASS |
| Exact deterministic agenda and B3-before-B4 | Regenerated seeded order compared for equality; policy string must match | PASS |
| Historical fingerprint | Original formula recomputed from authorized subject/config/rows/retention/order; stale fingerprint with altered slots/schedule rejected | PASS |
| v1/unknown schema | Unsupported schema rejected by backend contract | PASS |
| Valid reopen and no partial state on rejection | Synthetic positive/reopen tests and state-empty assertions | PASS |
| Duplicate keys, canonical bytes, and bounded manifest | Source inventory duplicate hook; outer canonical-byte equality; byte/depth/node budgets | PASS; strict RSS bound is OS-level and not claimed |
| Private data in CLI/logs/artifact paths | CLI redacts to status fields; CI log string search absent; upload paths exclude inventory/manifests | PASS by code/path review; ZIP bodies not unpacked |

### Positive and negative test run

`python -m pytest -p no:cacheprovider -q tests/test_scientific_manifest_contract.py tests/test_storage_capabilities.py` — **76 passed** on the independent Windows worktree.

No effectiveness, ASR, or utility estimate was made. Fixtures were synthetic.

SCI-REV-01 is closed at the scientific manifest boundary. The overall security disposition is `REMEDIATION_REQUIRED` until AUTH-REV-01 is fixed and independently tested.
