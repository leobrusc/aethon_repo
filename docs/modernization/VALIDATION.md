# Executed validation

Date: 2026-11-03. Runtime: Windows, Python 3.10.11. Commands run from the
modernization worktree. This record distinguishes local validation from future
GitHub and GPU experiments.

| Check | Outcome |
| --- | --- |
| Original checkout before work | PASS: 106 tests, including four uncommitted user tests; one expected mock-download warning |
| Modernization tracked suite | PASS: 111 tests (102 existing + 9 new), one expected mock-download warning; final run 26.73 s |
| Fresh-checkout test issue | Fixed one preexisting test's dependence on ignored `results/diagnostics/` by using `tmp_path`; original user file untouched |
| Ruff | PASS: syntax/correctness gate over src, scripts and tests |
| Pre-commit config and all tracked files | PASS: Ruff and Git-blob guard; final complete branch diff also checked against `544c363` |
| Diff whitespace | PASS; archived originals retain their existing Markdown hard breaks through a scoped attributes rule |
| Protected scientific files | PASS: 127 working-tree and Git payload hashes, including LFS identities |
| Curated PR #1 evidence | PASS: 31 independent artifact hashes, checkout and committed tree |
| Historical B3/B4 reanalysis | PASS: 9,139 paired records, zero decision differences; no new inference |
| Original user edits/backups | PASS: SHA-256 unchanged for all five files |
| Archived documents | PASS: Git payloads equal original documents byte-for-byte |
| Original dependency declarations | PASS: all 21 requirements including exact constraints preserved; three direct dependencies added |
| Build | PASS: sdist and wheel built with setuptools 81 and wheel 0.48; no scientific data bundled |
| Editable installation | PASS: installed in separate `.venv` with original scientific runtime reused via a local `.pth`; no research-runtime upgrade |
| Existing full requirements resolution | PASS: pip dry-run resolves against installed full environment; not a clean GPU install |
| Fresh CPU resolution | PASS: `pip install --dry-run --ignore-installed -e '.[dev]'` resolved 99 install candidates; no fresh GPU installation claimed |
| LFS objects and upload | PASS: `git lfs fsck`; new 55,487,878-byte object uploaded and pointer published |
| Installed/legacy CLI | PASS: help plus two-row B0 dry-runs, zero failures, equal outputs on 19 semantic columns; timing/run IDs excluded |
| Dependency consistency | PASS: `pip check`, no broken requirements |
| YAML and citation parsing | PASS: workflow, Dependabot, pre-commit and CFF parse |
| Known-vulnerability audit | FINDINGS: 168 advisories in 14 installed packages; exit 1, not a security approval |
| Real target LLM/GPU/cloud/human evaluation | NOT_RUN: outside this maintenance validation; no performance or ASR claim |

Raw build/install/resolution/CLI/test logs are regenerable local outputs under
ignored `results/modernization/`. `validation-log-hashes.json` records hashes of
the original build/install/resolution/help logs. `validation-environment.txt`
records observed packages, not a universal lock. The sanitized dependency report
keeps advisory IDs and affected versions; its raw response hash is retained.

The audit command was `python -m pip_audit --progress-spinner off --format json`.
No advisories were suppressed and no packages were auto-upgraded to obtain green
security checks. The full audit includes optional and development dependencies;
the CI job separately audits its actual CPU environment. Results are environment
specific and advisory data can change.

Initial sandbox network/process/cache denials were retried with execution
permission. The first build lacked wheel; installing build tooling resolved it.
The first tooling install chose setuptools 84, conflicting with torch's `<82`;
setuptools was corrected to 81 and `pip check` passed. These infrastructure/tool
incidents are not reported as scientific test successes.

## Publication and remote checks

Published branch: `refactor/repository-modernization-2026`.
[Draft PR #2](https://github.com/leobrusc/aethon_repo/pull/2) targets
`research/jorge-2026-experimental-upgrade`, explicitly depending on draft #1.
The original checkout stays on the scientific branch with its five files intact;
only the generated worktree path was added to the repository-local exclude file.

Code commit `ed64d78` was actually validated on GitHub Ubuntu/Python 3.10:

- [Push run 41669660401](https://github.com/leobrusc/aethon_repo/actions/runs/41669660401):
  `offline-tests` SUCCESS: **111 passed**, expected warning, 9.20 s; Ruff,
  127 scientific hashes, 31 curated evidence hashes, CLI help and Git-blob guard
  all succeeded. `dependency-audit` FAILURE: **102 advisory entries in four
  resolved CPU packages**. Installation succeeded; this was not an infrastructure
  or test failure.
- [PR run 41669838427](https://github.com/leobrusc/aethon_repo/actions/runs/41669838427):
  `offline-tests` SUCCESS; `dependency-audit` FAILURE on known advisories.

The remote scanner explicitly skipped the unpublished `aethon-research` package
and `torch 2.14.1+cpu`, whose exact build version was not found on PyPI. These are
NOT_AUDITED by that check, not implicitly safe. A separate upstream-version/build
provenance review is needed for CPU/CUDA distributions. The local full environment
audit did check its PyPI torch version and reports findings separately.

The 168 local and 102 remote counts are scanner advisory entries, potentially
including aliases/duplicates, not asserted counts of distinct exploitable flaws.
No security gate was bypassed. Final documentation-only publication updates may
trigger new CI runs; the completed runs above identify the exact code SHA tested.
Raw remote logs remain ignored under `results/modernization/`.
