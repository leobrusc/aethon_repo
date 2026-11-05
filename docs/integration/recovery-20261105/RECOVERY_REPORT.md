# Session recovery and PR #1 blocker cross-verification

Run ID: `recovery-20261105`. Date: 2026-11-05. This report supplements, never
replaces, `.worktrees/pr1-audit/results/audit/PR1_FINAL_READINESS.md`.

## Recovery

The original checkout remains on `research/jorge-2026-experimental-upgrade`,
`544c363c19a08574d30e7e2c064a78ce1bdfb601`. Its two modified source/test files,
two validated backups and patch remain untouched. Their five SHA-256 values match
`docs/modernization/preserved-local-state.json`; values are recorded again in
`recovered-state.json`. No stash, reset, clean, rebase, merge, deletion or main
update was performed.

The last completed audit was the isolated PR #1 review, whose 5,566-byte report
was found in detached worktree `pr1-audit` at `544c363`. It correctly reported
101 tests passing and readiness failing. Do not confuse that clean-tree result
with the original dirty checkout's earlier 106-test result.

Interrupted follow-up: `fix/scientific-artifact-guard-2026` in
`.worktrees/artifact-guard-fix`, based on PR #5 `ae351cd`, contained five uncommitted
files: `.gitattributes`, `BENCHMARK_STATUS.md`, `scripts/repository_guard.py`,
`src/final_harness_diagnostics.py`, `tests/test_repository_guard.py`. The recovered
patch was copied to the ignored local recovery directory before continuing; its
digest is in `recovered-state.json`. These edits implement the narrowly bounded
artifact exception and whitespace dispositions. They were not presumed tested.

Initial branch/upstream inspection found PR branches synchronized, with no
unpublished commits on the interrupted fix branch. The unrelated historical
revision branch remains 12 ahead/1 behind its upstream; it was not synchronized.
Worktree-specific heads, statuses and reflogs are recorded in recovered state.
The first Git-lock scan returned no lock paths; no lock was removed. Initial
process inspection through CIM was denied, so it did not establish process
absence. New validation Python processes are expected during this recovery.

Fetch succeeded after a sandbox permission failure. Transient process-creation
failures also occurred; the diagnostic recursive directory listing was interrupted
after it encountered protected cache directories. Only this session's listing
was stopped. No test or Git process from a prior session was terminated.

GitHub API metadata independently confirmed all five PRs open, draft and unmerged,
with the original reference heads unchanged; #1 targets main at `2964556`.
No previous successful execution was inferred from cache directories. New checks
were necessary for the uncommitted fix; bounded inference and previous seven
same-day advisory queries were not repeated.

## Cross-PR blocker matrix

| Blocker | Origin | Correction | Executed evidence | Isolated #1 | Consolidated #1–#5 | Consolidated plus this fix |
| --- | --- | --- | --- | --- | --- | --- |
| Readiness pytest | #1 | `3a211656a208e95dc8c6aa22874693d9ee95ab04`, PR #2 | Targeted test and full maintained suite; ancestry control | FAIL | PASS | PASS |
| 5 MiB guard | #1 artifact/#2 control | `bbafc48`, absent from existing #1–#5 heads | Guard regression tests; main-to-candidate Git-object scan | FAIL with modern guard | FAIL on aggregate main diff | PASS |
| Whitespace | #1 | `bbafc48`, absent from existing #1–#5 heads | `git diff --check origin/main` | FAIL, three findings | FAIL | PASS |
| Dependencies | #1/#2 | PR #3: `15b03c1` locks, `0199546` controls, `ac1e2c2` runtime, `3ca7eaf` final evidence | Seven same-day strict queries reused with hashes/locks verified; pip check | Known vulnerable historical stack: FAIL; new live scan NOT_RUN | PASS for maintained upstream queries | Same scoped PASS |

Readiness now writes to pytest `tmp_path`, independent of `results/diagnostics`.
The exact change remains in PR #2's head and descendants; the ancestry check and
current source establish that independently of general CI success.

The artifact exception binds exactly
`results/revision/detection/per_prompt_results.csv` to Git-blob SHA-256
`66130f23a92ea05fca856c808a4049245a31d0f6c530bbba517473be389e7a15`.
It is 6,718,635 bytes in Git. The hydrated Windows file has a different byte hash
because of existing CRLF checkout behavior; both identities are recorded in
`scientific-reuse.json`. No CSV bytes or attributes were changed. The guard reads
Git objects and retains credential checks even for an allowed large artifact.
Tests exercise exact acceptance, changed-content rejection and new-large-file
rejection. This grants no path wildcard, size increase or generic exemption.

Whitespace findings were `BENCHMARK_STATUS.md:13` (Markdown hard break),
`src/final_harness_diagnostics.py:59` (trailing space), and
`results/revision/error_analysis/wildjailbreak_diagnosis.md:7` (blank EOF).
The first uses an explicit HTML break; the second loses only trailing whitespace.
The protected third artifact remains byte-identical: a path-specific
`whitespace=-blank-at-eof` attribute documents its intentional historical EOF.
Existing CRLF evidence/lock attributes remain in force. No bulk normalization.

Maintained security upgrades address the affected model/tokenizer, networking,
image and build dependencies in independent hashed profiles. They do not repair
the preserved historical Python 3.10 runtime. Historical vulnerabilities remain
FAIL for untrusted workloads. Exact `+cpu`/`+cu` binary catalog coverage remains
NOT_AUDITED; official wheel receipts prove identity, not absence of flaws.

## Validation and scientific preservation

`checks.json` records exact commands, cwd, exit codes and output SHA-256 values.
Raw output is retained in adjacent files. Tests ran with Python 3.12.13 from the
maintained development/security venv, explicit candidate `src` on PYTHONPATH,
offline HF/datasets flags and pytest cache writes disabled. No packages or locks
were changed; the local editable installation still belongs to its original
security checkout, so these checks deliberately test candidate source paths.

- PASS: targeted readiness plus five guard cases (six tests).
- PASS: 144 full tests; one expected mocked model-download failure warning.
- PASS: Ruff, 127 protected scientific files, 31 indexed evidence payloads,
  six historical dependency manifests and aggregate whitespace check.
- PASS: consolidated main-diff Git-object guard, staged guard, pip check,
  Git LFS fsck and all five hydrated LFS entries; exact outcomes in `checks.json`.
- PASS: 9,139 historical B3/B4 pairs, matching truth and zero decision mismatches;
  original PR #1 CSV Git bytes equal current candidate bytes.
- PASS: 80-metric frozen-source comparison reused; all lock and relevant
  implementation identities checked. 103 prior validation evidence files were
  verified against their manifest, using the original validation worktree for
  ignored logs absent from the new checkout. See `continuation.json`.
- PASS: original five user-file hashes match their previous preservation record;
  no Git locks found. Neither `.codex` nor `.agents` exists in the project.
- Replay pairs historical records on dataset/prompt_id/prompt_sha256 and checks
  both truth and decisions; it is historical reanalysis, never new inference.
- The earlier 80-metric comparison is reused only after checking its frozen source
  digest. No thresholds, seeds, labels, splits, datasets or results are rewritten.
- Independent canonical raw-dataset identity: NOT_AUDITED. The local/LFS digest
  `1b197f9c836ce9a927f7d82f8c48c27439ad713ddcf2958a87faa7f09be2effd`
  establishes continuity, not an independent authoritative canonical reference.
- GPU, downloads, external API inference, prospective campaigns: NOT_RUN.

## Integration decision

**BLOCKED** for merge pending current-candidate GitHub CI. All bounded local
recovery controls have completed successfully; code is committed as `bbafc48`.
Existing PR #1 alone is not ready; existing #1–#5 also lack the
artifact exception and the whitespace dispositions. A green general CI does not
override those independently reproduced findings. This dependent fix is the
appropriate scope for a new draft PR based on #5, preserving every scientific
source commit. Local engineering disposition is eligible for
`READY_TO_MERGE_STACKED` after current-candidate CI passes. No isolated PR #1
approval, merge, new scientific-campaign approval or historical-runtime security
approval is implied.

Recovery-only retries: initial implementation hash and advisory-summary byte
assertions encountered existing CRLF checkout differences; comparison against
canonical Git objects and scanner raw digests resolved these without editing
inputs. A later evidence-index traversal found ignored scanner logs only in the
original validation worktree; those were verified there. Tests were not rerun
for these evidence-reader corrections. The local recovery scripts and their
checkpoint remain in `results/audit/recovery-20261105/`; copies accompany this
report for review. Recovered worktree reflog includes a pre-existing `reset:
moving to HEAD` entry; this session executed no reset and did not infer its mode.
