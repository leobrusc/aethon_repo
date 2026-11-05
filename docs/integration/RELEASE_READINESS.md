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

## Status

| Item | State | Interpretation |
| --- | --- | --- |
| Four PR ancestry and GitHub mergeability | PASS | Current refs form the declared 20/7/5/8 commit stack; every PR open, draft and mergeable |
| Final branch ancestry | PASS | 60 commits ahead of main, zero behind; merge-tree found no conflicts |
| Linux/Windows CI and research audit | PASS | Both push and PR workflows for `147747c`; all jobs successful |
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

Before a public release tag, decide the license, rerun dated dependency audits
and archive provenance for the exact release commit. Scientific campaigns need
their frozen prospective protocol, independent data and semantic-overlap review,
objective response rubric and appropriate hardware.

## Post-merge checks

After each stacked PR merge and after final integration to main:

1. Fetch refs and record full SHAs. Verify the target points to the expected
   GitHub merge commit and the prior reviewed head remains its ancestor.
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
