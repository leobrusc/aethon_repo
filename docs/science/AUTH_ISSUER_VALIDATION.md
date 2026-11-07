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
| Direct API negative pytest | Test body PASS marker; runner incomplete | `. [100%]` printed, but Windows pytest process did not exit; interrupted with exit 1, so suite result is not PASS |
| Legitimate lifecycle pytest | Test body PASS marker; runner incomplete | `. [100%]` printed, but Windows pytest process did not exit; interrupted with exit 1, so suite result is not PASS |
| Full pytest / focused aggregate | NOT_RUN / INCOMPLETE | Initial multi-file run had message-matcher failures in the newly added test, corrected; aggregate runner stalled before summary |
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

The synthetic lifecycle test emitted its pass marker, but did not yield a clean
pytest exit and therefore requires an independent CI rerun. Do not infer a full
suite pass from that marker or historical CI. Production storage remains
unauthorized; `PILOT_BLOCKED` and all eight gates `PENDING` remain unchanged.

## Parent-review CI (not this candidate)

PR #30 workflow `42330986567` was checked independently: Windows SUCCESS,
Linux SUCCESS, and research/GPU audit SUCCESS. Its Linux and Windows jobs each
reported 407 passed; GPU inference was `NOT_RUN`. That workflow tested the PR
#30 review HEAD, not this remediation branch, and therefore does not validate
these changes. Candidate CI must run after publication.

The first candidate CI run `42396923280` found the same 1 failure / 407 passes
on both Linux and Windows: the preflight test correctly rejected the changed
governance bytes because the implementation SHA allowlist in
`collector_v1.json` still named the old file. The research/GPU job succeeded.
The allowlist was updated to the new source SHA
`31a4e56d624a86c725443f37c531b565bbda67e2520426cd7fc5703440ff0317`; this is
an implementation-integrity seal update only. A follow-up candidate CI run is
required and its result must be recorded before claiming full validation.
