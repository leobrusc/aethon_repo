# Authorization validation report

## Identity

- Branch: `fix/operational-authorization-boundary-v1`
- Parent PR #28 head: `587ec791d0e88476b66f0fc37a817865f3ec70c9`
- PR #27 ancestor: `2034aade9b56bf76ff13f4816a5ff9de73a879a6`
- Engineering baseline: `9ed55709add0fc45f63847a0394315863faa0876`
- Schema and scientific fingerprint formula: unchanged.

## Checks

| Check | Result |
|---|---|
| Historical vulnerable reproduction on PR #28 | REPRODUCED — capability issued, one run created, 120 slots |
| Original reproduction archive | PRESERVED — SHA-256 `D94F984C4EED8AB7EC58BC6EB7CE0CE2D1EE9BBBB4C26C5140E930DFD667CBD9` |
| Corrected synthetic direct harness | PASS — subclass rejected at facade/backend with no run state; legitimate 120-slot write/retry/journal/close/reopen/read passed |
| Focused authorization/storage/manifest pytest | INCOMPLETE — local runner emitted an error without traceback and did not complete |
| Full pytest | NOT_RUN after the focused runner became environment-blocked |
| Ruff | PASS — full repository |
| `pip check` | PASS |
| Publication guard | PASS against parent HEAD (staged-blob check remains for commit time) |
| `git diff --check` | PASS |
| Git LFS fsck | PASS |
| Offline preflight | PASS for fail-closed result: `PILOT_BLOCKED`, `executed=false`; exit 2 is expected |
| Historical controls | 127 protected-file inventory PASS; 31 indexed evidence hashes PASS against worktree and HEAD; six manifests, 9,139 pairs, 80 metrics, five local files reused from PR #28 evidence; LFS fsck PASS |
| CI for remediation | NOT_RUN — no remediation commit/PR yet |

Environment: Windows 10.0.26300 / Python 3.10.11. Process creation later failed with Win32 error 5. No security policy was changed. No dependency installation, model download, inference, production provisioning, or paid operation occurred.

## Disposition

The code changes address the demonstrated virtual-dispatch bypass in the declared threat model. Because tests did not complete and no CI exists for this branch, disposition is `REMEDIATION_PARTIAL`. Keep `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, all eight gates `PENDING`, and `PILOT_BLOCKED`. Do not begin Linux native-backend work until tests complete and independent review accepts the trust boundary and residual in-process limits.
