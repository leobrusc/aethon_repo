# Phase 7A validation and preservation record

Base reviewed: PR #32 HEAD `ada83b59ac2eb22ea7abc9acc31913b7fef6a220`. Worktree branch: `design/src02-native-storage-contract-v1`. No native backend or filesystem primitives were implemented or executed.

## Checks run

| Check | Result | Evidence / qualification |
|---|---|---|
| Full pytest | PASS | 408 passed, one expected warning from the existing mocked model-load failure test; 94.52 s, Python 3.10.11 existing environment |
| Abstract commit model | PASS | `ABSTRACT_COMMIT_MODEL_PASS`; pure Python standard library; no filesystem operations |
| Ruff | PASS | Abstract model file; `All checks passed!` |
| `pip check` | PASS | No broken requirements; no installation performed |
| Protected scientific inventory | PASS | 127 files verified against recorded base `544c363c19a08574d30e7e2c064a78ce1bdfb601` |
| Research evidence index | PASS | 31 artifact hashes verified in working tree and Git HEAD |
| Six historical evidence manifests | PASS | Hashes in `EVIDENCE_SHA256SUMS.txt`; each was also part of the 127-file verification |
| Publication guard | PASS | `repository_guard.py --staged`; Git blob guard passed |
| Whitespace | PASS | `git diff --cached --check`; no output |
| Git LFS | PASS | `git lfs fsck` OK; `git lfs ls-files` lists five payloads |
| Offline preflight | PASS for fail-closed expectation | `PILOT_BLOCKED`, `executed=false`, all eight gates `PENDING`; exit 2 is the intended blocked status |
| B3/B4 historical comparison | PASS | Read-only in-memory comparison: 9,139 pairs; all pair joins and labels matched; zero decision mismatches; no report written |
| Historical 80 metric values | REUSED | Prior receipt `docs/science/remediation-v1/validation/summary.json`, SHA-256 `a4c7fab61d0f70469b0faa1960bf1c0519c01012711ab07fbd63cce1fcf49342`; not recomputed in Phase 7A |
| Native Linux/Windows fault matrix | NOT_RUN | No native backend, provisioning, or native tests in this phase |

## Historical bytes

The B3/B4 CSV working-tree SHA-256 during the read-only comparison was `914901a1ed82836dfb42567cb376ec90f20459d1ad0f9b12d72568f4bfca202a`. The committed Git blob at reviewed HEAD has SHA-256 `66130f23a92ea05fca856c808a4049245a31d0f6c530bbba517473be389e7a15` and size 6,718,635 bytes, matching the preserved CI/reanalysis source identity. The working-tree and Git-blob hashes differ; this is reported rather than normalized or treated as the same byte identity. The read-only comparison found the required 9,139 paired rows and zero decision mismatches in the working tree. Repository inventory validation accepts the recorded working-tree or Git-blob identity for protected files.

## Local-file and branch preservation

The original checkout retained its pre-existing status unchanged: modified `src/close_harness.py` and `tests/test_harness_closure.py`, plus untracked `close_harness.validated.backup.py`, `test_harness_closure.validated.backup.py`, and `validated_tpr_auroc_closure.patch`. All five paths were present there after this work. They were not copied into the isolated worktree, staged, or modified. No dependency, lock, dataset, model, baseline, threshold, receipt, or result file is staged in this branch. `main` and earlier PR branches were not changed.

The historical reanalysis script `scripts/validate_historical_decisions.py` was not used because it writes a report under `results/`; the equivalent data comparison was performed read-only in memory. No scientific result was written or overwritten.

## Operational state

This validation is documentation plus a pure abstract model. It does not establish native durability, ACL confinement, freshness, rollback resistance, or operational authorization. `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED`, and all eight gates `PENDING` remain.
