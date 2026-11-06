# Adversarial contract matrix

| Contract | Existing evidence | Review result | Residual/action |
|---|---|---|---|
| Forged/copied/foreign/closed capability | `test_storage_capabilities.py` | PASS in synthetic backend | Does not resist Python reflection/host compromise |
| Expired authorization and cleanup | Existing synthetic test | PASS | Native cleanup ownership/expiry needs OS tests |
| Subject/manifest/budget binding | Existing cross-binding tests | PASS for tested envelope fields | `run_fingerprint` is not recomputed; full scientific manifest validation missing (SCI-REV-01) |
| Object hash, checkpoint identity, no overwrite | Existing corruption/collision tests | PASS for tested backend | Native metadata integrity/durability untested |
| Same operation retry / conflicting intent | Existing idempotency/fault tests | PASS in memory model | Native transaction receipt semantics required |
| Journal sequence/hash/head corruption | Existing recovery tests | PASS for tested corruption | Whole-store coherent rollback remains undetectable |
| Writer ownership/reentry/thread collision | Existing logical-thread test | PASS within one process | No cross-process lease evidence; ensure every native mutation is lease/CAS guarded |
| Interrupted commit before/after acknowledgment | Existing fault-injection tests | PASS for volatile model | Uncertain native commit must fail closed; no inference retry |
| Full 120-slot/B0–B4 matrix | Existing tests | PASS for cardinality/conditions | Pair/family quotas and dependency order are accepted malformed (SCI-REV-01) |
| Missing/error/truncated/review-pending accounting | Existing collector/review tests | PASS for exercised states | Do not compute efficacy from synthetic fixtures |
| B3/B4 reuse | Existing collector tests | PASS for fingerprint divergence tested | Native binding must include every effective input and model/template/settings |
| Facade path-free persistence | AST/monkeypatch tests + source inspection | PASS as code separation | Not proof of kernel-enforced confinement |
| Failed recovery exports no summary | Existing poison-state test | PASS in facade | Persistent review ledger lifecycle still needs a separate authorization design |
| Response to malformed semantic manifest | New `test_storage_capability_review_reproductions.py` | Finding demonstrated: accepted | Convert reproductions to rejection tests after repair |

The two review reproduction tests intentionally pass by observing the current incorrect acceptance. They are not evidence that the contract is satisfied. No fixture yields ASR, efficacy or power estimates.
