# Authorization issuer validation

## Identity and reproduction

- Vulnerable PR #29: `853d4fb95023461432397b4bab81803757209497`.
- Review base PR #30: `b8104f5a7e5970018b9c1e58b83e2eab0009b056`.
- Historical proof SHA-256: `abe4426c99ae52332a5ae6799d55a74a8dafabda5784bff2d1d6cf099ebddc4a`.
- Vulnerable execution: accepted manual object; emitted capability; created one
  run with 120 slots.
- Corrected execution of the unchanged proof: `ImportError` for the removed
  `_AUTHORIZATION_ISSUER`, exit 1; no capability or run was created.

## Validation ledger

Record each local command and its actual result here before publication:

| Check | Result | Evidence/limitations |
|---|---|---|
| Historical PR #29 reproduction | PASS (vulnerability reproduced) | Synthetic only; not a fix test |
| Corrected unchanged proof | REJECTED as expected | Import fails because removed issuer token no longer exists |
| Direct API negative pytest (local) | Test body PASS marker; runner incomplete | `. [100%]` printed, but Windows pytest process did not exit; interrupted with exit 1; authoritative clean result is candidate CI |
| Legitimate lifecycle pytest (local) | Test body PASS marker; runner incomplete | `. [100%]` printed, but Windows pytest process did not exit; interrupted with exit 1; authoritative clean result is candidate CI |
| Full pytest candidate CI | PASS | Latest code CI run `42398791189` on implementation commit `803451e2045e73de103e8f4ddd8c2ea47d06a9a6`; Linux and Windows each report 408 passed, 1 warning |
| Ruff | PASS | `python -m ruff check --no-cache src/aethon/pilot_governance.py tests/test_authorization_boundary.py` |
| pip check | PASS | `No broken requirements found` |
| Publication guard | PASS | `scripts/repository_guard.py --base b8104f5a7e5970018b9c1e58b83e2eab0009b056` |
| `git diff --check` | PASS | No whitespace errors |
| Git LFS fsck | PASS | `Git LFS fsck OK` |
| Research evidence hashes | PASS | 31 artifacts verified in working tree |
| Historical scientific inventory | PASS | 127 scientific files verified against recorded baseline `544c363c19a08574d30e7e2c064a78ce1bdfb601` |
| Six manifests / 9,139 pairs / 80 metrics | NOT_RUN | No historical replay or metric computation performed |
| Five local files | PRESERVED | Root checkout's pre-existing modified/untracked files were not touched |
| Offline preflight | NOT_RUN | Not needed to validate this API-only change; eight gates remain pending |

The synthetic lifecycle test emitted its pass marker locally without a clean
pytest exit; the final candidate CI provides the clean full-suite evidence.
Production storage remains unauthorized; `PILOT_BLOCKED` and all eight gates
`PENDING` remain unchanged.

## Candidate CI

Latest code run `42398791189` tested implementation commit
`803451e2045e73de103e8f4ddd8c2ea47d06a9a6` and completed successfully:

- Linux: SUCCESS, 408 passed, 1 warning.
- Windows: SUCCESS, 408 passed, 1 warning.
- Research/GPU audit: SUCCESS; GPU inference `NOT_RUN`.

The successful predecessor run `42397370217` tested commit `5467c931` after
updating the implementation seal. Commit `803451e` then removed the closure
factory name from the module namespace and updated the seal to
`a50ff66acdde02045dce308b522d7224805c26bf96428a9ad59e3335b12425c6`; the
latest successful run includes that change. The first candidate run
`42396923280` failed on Linux and Windows with 407 passes and one failure each
because the implementation seal still named the old governance source. That
failure is preserved. The workflow checks scientific preservation and
publication guards.

## Parent-review CI (not this candidate)

PR #30 workflow `42330986567` was checked independently: Windows SUCCESS,
Linux SUCCESS, and research/GPU audit SUCCESS. Its Linux and Windows jobs each
reported 407 passed; GPU inference was `NOT_RUN`. That workflow tested the PR
#30 review HEAD, not this remediation branch, and therefore does not validate
these changes. Candidate CI is reported above.
