# CI and preservation evidence

## CI identity

- PR #29 final HEAD: `853d4fb95023461432397b4bab81803757209497`.
- CI run `42328753556` tested implementation commit `20662acb840dd6dd0a6c773dc1d4121a163c871c`.
- `git compare` confirms the only two later commits changed three validation-report files; no implementation or tests changed after the tested commit.
- Linux: `SUCCESS`, 407 passed, one warning.
- Windows: `SUCCESS`, 407 passed, one warning.
- Research/GPU audit: `SUCCESS`; GPU inference `NOT_RUN`.
- First run `42327652086`: Linux/Windows failed with fixture registration, rejection-message expectation, and implementation-seal mismatches. Those were fixed in `20662ac`; the failed run remains preserved as history.

## Reproductions

- AUTH original command: SHA-256 `d94f984c4eed8ab7ec58bc6eb7ce0ce2d1ee9bbbb4c26c5140e930dfd667cbd9`; rerun on PR #28 reproduced acceptance and one run; rerun on PR #29 rejected the subclass before a capability was issued.
- SCI-REV-01 historical reproduction archive: SHA-256 `cb1677420f58268ec310190442e4363f2b37962d0a5fb7451b21b868624151f4`; Git blob `5df1607ada22ebac330e106b5421e6fa36a13e4e`, unchanged.
- New private-issuer reproduction: `tests/review_private_issuer_registration.py`, SHA-256 `abe4426c99ae52332a5ae6799d55a74a8dafabda5784bff2d1d6cf099ebddc4a`; output shows a fresh manual object received a capability and one run.

## Fresh checks in independent review worktree

- 127 scientific files: PASS via `repository_inventory.py verify`.
- 31 indexed evidence hashes: PASS in worktree and HEAD.
- Git LFS fsck: PASS.
- Ruff: PASS.
- `pip check`: PASS.
- `git diff --check`: PASS before report files were added.
- Offline preflight: `PILOT_BLOCKED`, `executed=false`, all eight gates `PENDING`.
- Local targeted pytest reached 100% progress but hung before the summary/exit status; it is **incomplete**, not reported as PASS. Cross-platform CI evidence is reported separately.

## Review-branch CI

The draft review PR workflow `42330986567` completed successfully on Linux, Windows, and research/GPU audit. Linux and Windows each reported 407 passed with one warning; each CI job verified 127 scientific files, 31 evidence hashes, and the publication guard. The review reproduction is an explicit synthetic script, not a pytest-collected test; its execution result is separately recorded in the independent review. GPU inference remained `NOT_RUN`. This CI result validates the review branch's regression suite, but does not disprove the private-issuer reproduction.

## Reused historical evidence

Six manifests, 9,139 paired B3/B4 rows, 80 metric values, and five preexisting local files were verified in prior PR #28 evidence and were not recalculated in this review. The five LFS payloads were not separately rehashed here; `git lfs fsck` and prior PR #28 receipts are retained as evidence. No scientific result, dataset, threshold, lock, or environment was changed.

The original checkout still contains its five preexisting local changes; this review did not modify them.
