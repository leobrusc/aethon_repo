# Independent storage capability security review

## Disposition

**STORAGE_REMEDIATION_REQUIRED** for the scientific manifest contract before a native backend is implemented. The tested Python API is path-free and the production runtime remains fail-closed, but the backend boundary accepts manifests whose frozen pairing/family quotas and B3/B4 schedule have been changed. No native storage guarantee was tested or is claimed.

Reviewed PR #25 at `a46cc65d36c90e83a91504bd414e92b6f7ac0299`, based on PR #24 `2dc16eb53d93336318a8e23c428cc0542656d25d`; PR #24 is an ancestor. Reference architecture is PR #19 `7431d7b423bc6fc34d1db51c12794742481f8428`. Review reproductions use synthetic fixture authorization and do not run inference or estimate ASR.

## Threat model and boundaries

Assets: immutable run manifest/configuration, private requests/responses, slot accounting, journal, authorization and human review evidence. Inputs (inventory, checkpoints, events) are untrusted. The synthetic backend is trusted test code but mutable test instrumentation can model corruption. The production Python process, kernel, administrator, future native backend, root-capability bootstrap and any independent freshness witness are outside this synthetic test boundary.

The facade delegates run-store object/checkpoint reads and writes, journal/head, writer leases, recovery and close to `StorageBackend`; source inspection found no persistence pathname operation in the facade. Configuration/model/evidence input loading and read-only storage probes remain distinct from run persistence. This is an architectural separation, not OS confinement. `collect_runtime` rejects collection before model or storage bootstrap.

| Area | Review result |
|---|---|
| Capability identity, foreign/closed handle rejection | Existing synthetic tests pass; no hostile-interpreter guarantee |
| Object/checkpoint binding and immutable publication | Logical binding tested; native durable integrity remains unimplemented |
| Journal chain/CAS/recovery | Synthetic corruption cases covered; coherent full rollback has no independent witness |
| Slots and generation side effects | Existing collector records started intent and refuses automatic retry when response is uncertain |
| Frozen case/pair/family/schedule contract | **Finding SCI-REV-01:** backend accepts altered quotas and B4-before-B3 schedule |
| Linux/Windows path confinement, durability, ACL/reparse behavior | NOT_RUN; future native review required |

## Finding SCI-REV-01 — scientific manifest constraints not enforced at capability boundary

**Severity: High (scientific integrity; pre-native implementation blocker).** `tests/pilot_memory_backend.py::MemoryBackend.open_run` validates 24 sample IDs, 120 unique slots and a B0–B4 set per sample, but does not independently validate 12 attack/control pairs, 4 pairs in each of the three frozen families, pair label/context correspondence, or the frozen B3-before-B4 dependency. It accepts arbitrary `pair_id`/`family_id`, and only checks that `schedule` is a permutation of slot IDs. It accepts the caller's 64-hex `run_fingerprint` without recomputing/validating it against the effective manifest; the reproductions retain the original run fingerprint while changing those design fields. `validate_inventory` and `make_manifest` in `pilot_collector.py` normally validate/generate these fields, but `open_run` is the boundary minting the run capability and receives an immutable manifest that may originate from untrusted inventory/caller code. A caller that bypasses or misuses the upstream helper can therefore bind a syntactically complete 120-slot run to a materially different design while retaining a stale run identity.

Reproduction: `tests/test_storage_capability_review_reproductions.py::test_review_repro_accepts_invalid_pair_and_family_quotas` changes all slots to one pair and an unknown family; `test_review_repro_accepts_b4_before_b3_in_frozen_schedule` moves every B4 slot before the remaining arms. Both assert that `open_run` accepts the malformed synthetic manifest. These are deliberately named historical-style reproductions, not acceptance tests; remediation should invert them to rejection assertions and preserve their original source/hash in the review record.

**Impact:** invalid pairing, labels/family distribution or order can be persisted and resumed as if authorized, undermining paired comparisons and the frozen prospective protocol; stale run fingerprints weaken audit identity. **Preconditions:** caller can provide a manifest to the backend with an otherwise valid issued authorization/subject; this is not reachable through the currently disabled productive runtime. **Recommendation:** validate the full frozen schema at the trusted capability boundary: exact family IDs and 4 pairs each; exactly 12 pair IDs with two samples, labels `{0,1}`, same family and required paired context; exact 24 cases; five unique conditions for each case; canonical slot identity; and the frozen schedule constraints/seed-derived schedule or a separately authenticated schedule digest. Define/recompute run identity over all effective manifest fields (including schedule and pairing metadata), or reject a stale/unverifiable fingerprint. Reject unknown/extra schema fields where they can alter semantics. Add mutations for 5/4/3, 6/3/3, 12/0/0, incomplete pairs, mismatched context, and B4-before-B3. Do not infer human semantic correctness from structural validation.

## Verified properties and residuals

Current source/tests support only a synthetic contract conclusion: no arbitrary run pathname enters the facade API; accepted immutable object identity, canonical envelope, hash chain, sequence/CAS, operation idempotency, quota checks and volatile receipt labeling are present. Test threads do not prove process-level locking. Memory is neither durable nor anti-rollback. A lost inference result remains uncertain and must not be repeated automatically. A complete coherent rollback is undetectable without an independent monotonic witness.

SRC-02 remains NOT_AUTHORIZED; `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED`, and all eight gates PENDING. **Do not begin Linux native implementation until SCI-REV-01 is fixed and independently re-reviewed.**
