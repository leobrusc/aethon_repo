# Authorization validation report

## Identity

- Branch: `fix/operational-authorization-boundary-v1`
- Parent PR #28 head: `587ec791d0e88476b66f0fc37a817865f3ec70c9`
- PR #27 ancestor: `2034aade9b56bf76ff13f4816a5ff9de73a879a6`
- Engineering baseline: `9ed55709add0fc45f63847a0394315863faa0876`
- Schema and scientific fingerprint formula: unchanged. Implementation seal hashes in `collector_v1.json` now pin the exact remediated modules, so the config digest and any future subject/run identity change; historical manifests are not migrated.

## Checks

| Check | Result |
|---|---|
| Historical vulnerable reproduction on PR #28 | REPRODUCED — capability issued, one run created, 120 slots |
| Original reproduction archive | PRESERVED — SHA-256 `D94F984C4EED8AB7EC58BC6EB7CE0CE2D1EE9BBBB4C26C5140E930DFD667CBD9` |
| Corrected synthetic direct harness | PASS — subclass rejected at facade/backend with no run state; legitimate 120-slot write/retry/journal/close/reopen/read passed |
| Focused authorization/storage/manifest pytest, local Windows | ENVIRONMENT_BLOCKED — local runner emitted an error without traceback and did not complete |
| Full pytest, PR CI run `42328753556` | PASS — Linux 407 passed; Windows 407 passed; one expected warning per platform |
| Ruff | PASS — full repository |
| `pip check` | PASS |
| Publication guard | PASS against parent HEAD (staged-blob check remains for commit time) |
| `git diff --check` | PASS |
| Git LFS fsck | PASS |
| Offline preflight | PASS for fail-closed result: `PILOT_BLOCKED`, `executed=false`; exit 2 is expected |
| Historical controls | 127 protected-file inventory PASS; 31 indexed evidence hashes PASS against worktree and HEAD; six manifests, 9,139 pairs, 80 metrics, five local files reused from PR #28 evidence; LFS fsck PASS |
| CI for remediation | `42328753556` PASS — Linux, Windows and research/GPU audit jobs all SUCCESS; GPU execution NOT_RUN |

Local test environment: Windows 10.0.26300 / Python 3.10.11. Pre-fix pytest attempts did not complete and omitted a traceback; later process creation returned Win32 error 5. No final local pytest pass is claimed. No security policy was changed. No local dependency installation, model download, inference, production provisioning, or paid operation occurred. The PR-triggered CI used its configured isolated dependency bootstrap; it was not treated as local runtime approval.

## First PR workflow attempt

The automatically triggered run `42327652086` failed on the first commit. Linux reported 396 passed, 2 failed, 9 errors: the new test module had not registered `setup_run`, the existing clone test expected the base rejection message, and the preflight implementation seal did not pin the changed `tests/pilot_memory_backend.py`. Windows showed the same categories; the research/GPU audit job succeeded (GPU execution `NOT_RUN`). Follow-up commit `20662acb840dd6dd0a6c773dc1d4121a163c871c` fixes these issues. Run `42328753556` then passed all three jobs; Linux and Windows each reported 407 passed and one warning, with research/GPU audit `SUCCESS` and GPU execution `NOT_RUN`.

## Disposition

The historical subclass reproduction is rejected, the authorized synthetic lifecycle is preserved, and the final CI is green on Linux and Windows. Disposition: `AUTH_REV_01_REMEDIATED`, pending independent review of the implementation and residual in-process limits. This does not authorize production storage or pilot execution. Keep `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, all eight gates `PENDING`, and `PILOT_BLOCKED`. Do not begin Linux native-backend work until independent review accepts the boundary and residual risks.
