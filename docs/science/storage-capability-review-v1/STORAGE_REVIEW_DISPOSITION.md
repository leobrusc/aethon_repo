# Storage review disposition

## Classification

**STORAGE_REMEDIATION_REQUIRED** — one demonstrated scientific-contract defect blocks native implementation readiness. The opaque API and in-memory contract are useful scaffolding; they are not a native security certification.

| ID | Severity | Location | Evidence | Required correction | Residual |
|---|---|---|---|---|---|
| SCI-REV-01 | High, scientific integrity | `tests/pilot_memory_backend.py::MemoryBackend.open_run`; corresponding future shared manifest validator | Two synthetic reproductions accept all cases under one unknown family/pair and accept schedule with B4 before B3 | Validate exact 12 paired attack/control cases, 4 pairs per frozen family, labels/context, unique case identities, 5 arms and frozen schedule/dependency before mint | Structural validation does not establish human semantic correctness; operational gates remain required |

## Test disposition

The independent reproduction module contains two tests that pass by asserting the current incorrect acceptance. The complete local suite including these reproductions passed **372 tests, one existing mocked model-load warning**; the separate reproduction run passed 2/2. Ruff and `pip check` passed without installation. `git diff --check`, Git LFS fsck, `repository_guard.py --base a46cc65d36c90e83a91504bd414e92b6f7ac0299`, and `verify_research_evidence.py --git-tree HEAD` passed. `repository_inventory.py verify` confirmed 127 protected files; `validate_historical_decisions.py` confirmed 9,139 pairs and zero decision mismatches; historical dependency verification confirmed six manifests. Existing PR #25 preservation receipts record 80 metrics, five LFS payloads and five local files; their indexed hashes are checked separately. The offline preflight returned the expected `PILOT_BLOCKED`, executed=false, all eight gates PENDING (exit 1 is the script's expected blocked status).

No code or scientific data were changed by this review. Ruff/pytest/pip were run from the pre-existing security virtual environment; no package installation occurred. CI was not started. Existing #25 evidence logs remain unchanged.

## Decision on Linux work

Do not start a Linux native backend yet. First fix SCI-REV-01 in the shared trusted manifest validation layer, add rejection regressions for invalid family distributions, incomplete/mismatched pairs and B4-before-B3, then obtain an independent review. After that, Linux backend work may begin as a separate implementation phase only with an approved root-capability bootstrap and a concrete durable-commit/freshness design. SRC-02 remains NOT_AUTHORIZED.

`DEPENDENCY_APPROVAL_REQUIRED`; `PILOT_BLOCKED`; all eight operational gates `PENDING`.
