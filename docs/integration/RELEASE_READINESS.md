# Release readiness

## Recommendation

**READY_FOR_REVIEW** for engineering integration of PRs #1–#4. Reviewers can
assess the chain against its current SHAs. This is not merge approval, model
safety certification, residual-risk acceptance or authorization for a final
scientific campaign.

The PR and push workflows for exact commit
`147747cf855dbacbb221f2074908dde1b0c77860` passed on Linux, Windows and the
research/CUDA audit job. Local quality, integrity and replay checks passed in
their stated scope. The 127 scientific files, 31 evidence files, six historical
dependency manifests and 9,139 paired B3/B4 records retain verified identities.

Audit PR #5 snapshot `e8942ae7adc0f37f19515b4ec2193a195a167878` passed all
three initial CI jobs: Linux CPU, Windows CPU and research/GPU audit in
[workflow run 42019751311](https://github.com/leobrusc/aethon_repo/actions/runs/42019751311).
PR #5 remains directly based on validation head
`147747cf855dbacbb221f2074908dde1b0c77860`; the correction adds documentation
only. Main remains an ancestor of the report branch with no divergence. The
corrected PR #5 head `dcc6d3bef8fac5a184a33a30c96900ba3d0614bd`, directly based
on validation head `147747cf855dbacbb221f2074908dde1b0c77860`, passed all three
jobs in [run 42022134734](https://github.com/leobrusc/aethon_repo/actions/runs/42022134734).
The report-only commit recording that result does not change source, locks or
validation inputs.

## Status

| Item | State | Interpretation |
| --- | --- | --- |
| Four PR ancestry and GitHub mergeability | PASS | At the audited snapshot refs form the 20/7/5/8 commit stack; each PR open, draft and mergeable |
| Audit PR ancestry | PASS | PR #5 is a direct documentation-only descendant of PR #4; main is an ancestor with zero divergence |
| Linux/Windows CI and research audit | PASS | PR #4 and PR #5 exact heads `e8942ae` and `dcc6d3b`; both runs passed all three jobs |
| Sequential target merge commits | NOT_YET_CREATED | Existing PR heads descend from one another, but merge commits produced on current sibling target branches are not automatically ancestors of the following source heads |
| Tests, Ruff, package check, install and CLI | PASS | Maintained suite, historical contract tests and isolated install verified |
| Scientific hashes and replay | PASS | 127 files, 31 evidence items, six manifests, 9,139 pairs |
| Upstream advisory scan | PASS | Seven refreshed 2026-11-05 queries: 0 findings and 0 skips; raw evidence is versioned in `evidence/security-audits/` |
| PyTorch exact build vulnerability catalog | NOT_AUDITED | Scanner skips retained; wheel receipt is not a vulnerability audit |
| Historical vulnerable runtime | FAIL for new untrusted workloads | Retain for controlled historical reproduction only |
| CUDA model execution | NOT_RUN | No NVIDIA device in audited environment |
| Prospective ASR/statistical equivalence | NOT_RUN | No independent final campaign or powered equivalence study |
| Repository license | REVIEW | No explicit license file; owner decision required before tagged release or redistribution |
| Citation metadata | PASS with gaps | Basic `CITATION.cff`; version, date, DOI and license absent |

## Approval gates

Before merging, require maintainers to review each PR at the recorded head/base
SHA in dependency order, require all checks to pass on the current refs, review
the historical vulnerability scope and exact-wheel audit limits, and confirm
that no scientific artifacts or dependency locks changed. Confirm whether the
no-license state is intentional for code integration. Add a license only after
the owner verifies authority over code and bundled artifacts; citation metadata
does not grant a license.

The recommended path retargets PRs #1–#4 to `main` and merges them sequentially
with merge commits. Recalculate and review every diff after retargeting. Verify
that each next PR's merge base equals the prior source head; only then will main
contain all source commits and each PR merge commit. If retargeting is prohibited,
use the consolidated PR alternative in `INTEGRATION_PLAN.md` and record that
only source commits and one final integration merge commit reach main.

Before a public release tag, decide the license, rerun dated dependency audits
and archive provenance for the exact release commit. Scientific campaigns need
their frozen prospective protocol, independent data and semantic-overlap review,
objective response rubric and appropriate hardware.

## Post-merge checks

After each sequential PR merge and after the final PR integration to main:

1. Fetch refs and record full SHAs. Verify each target points to the expected
   GitHub merge commit, with the reviewed base as first parent and reviewed PR
   head as second parent. After PR #4, verify all four source heads and all four
   PR merge commits are ancestors of main.
2. Verify all 127 scientific hashes, 31 evidence hashes, six historical
   manifests and five LFS pointers/payloads (`git lfs fsck`).
3. Run repository inventory, research evidence, historical manifest and
   9,139-pair B3/B4 verification scripts.
4. Install a selected existing hashed CPU lock in a fresh isolated environment;
   run pytest, Ruff, pip check, dependency audit, every CLI help and quality CI.
   Mark GPU execution `NOT_RUN` until actual hardware, operators and inference
   succeed.
5. Compare the final diff with the prior main SHA. Confirm historical outputs,
   lock bytes and unrelated user files are unchanged. Archive CI artifacts with
   the release SHA.

Any changed ref or failed gate requires a refreshed audit. The guarded command
sequence is in [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md); the full findings are
in [PRE_MERGE_AUDIT.md](PRE_MERGE_AUDIT.md).
