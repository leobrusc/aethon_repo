# Scientific integrity validation

## Scope and status

This report records the Phase 6C test and preservation results. Synthetic fixtures validate structure only; they do not estimate attack success, task utility, statistical power or scientific efficacy. No real inference was run.

## Results

| Control | Result |
|---|---|
| Pytest complete suite | PARTIAL: 397 passed; one unrelated existing OpenSSL subprocess test failed because Windows denied process creation (`Win32 error 5`) in the sandbox. A prior full run before the final config-seal refresh passed 398 tests. |
| Adversarial manifest rejection and valid positive cycle | PASS: targeted shared-manifest/preflight/schedule selection, 29 passed; full suite exercised the new contract tests. |
| Ruff / pip check | PASS: Ruff reported all checks passed; `pip check` reported no broken requirements. Ruff emitted an access-denied cache warning for a nested historical requirements path, but no lint findings. |
| Publication guard / whitespace / Git LFS fsck | `git diff --check` and `git lfs fsck` PASS. Publication guard final invocation pending. |
| Offline preflight | PASS for fail-closed behavior: reports `PILOT_BLOCKED`, `executed=false`, and all eight gates `PENDING` (CLI exit 2 is the expected blocked result). |
| Protected scientific files / indexed evidence | PASS, recalculated: 127 protected files against baseline `544c363c19a08574d30e7e2c064a78ce1bdfb601`; 31 evidence hashes verified in working tree and HEAD. |
| Historical manifests / B3-B4 pairs / metrics | Prior indexed preservation receipt reused: six manifests, 9,139 pairs, 80 metrics; the current combined historical verifier did not complete within this run. |
| Five LFS payloads / five preexisting local files | Prior indexed PR #25 preservation receipt reused (five payloads and five local files); `git lfs fsck` rerun PASS. No historical payload or local file was modified. |

## Scientific contracts

B0–B4 definitions, generation settings, seeds, thresholds, model revisions, labels, rubrics and result data are unchanged. Schema changes are limited to the private run manifest and internal authorization retention-binding fields. The collector config's implementation-file digest list changes, which changes its protocol fingerprint and invalidates prior authorization. No historical manifest migration occurs.

## Operational limits

SRC-02 remains NOT_AUTHORIZED. `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED`, and all eight gates PENDING remain in force. Linux/Windows confinement, ACLs, durability, crash semantics, process isolation and rollback freshness are not implemented or validated here. Full-suite status is not a clean pass because the pre-existing test that invokes Git for Windows OpenSSL could not create its child process under the sandbox; no OpenSSL key was generated in that attempt.
