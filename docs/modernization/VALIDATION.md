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

GitHub publication and remote CI observations are recorded separately below
after the branch is pushed. No CI result is inferred from these local checks.
