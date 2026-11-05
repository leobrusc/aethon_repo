# Integration and recovery plan — corrected merge ancestry

Snapshot refs and CI are in [PRE_MERGE_AUDIT.md](PRE_MERGE_AUDIT.md). Current
heads are main `2964556`, PR #1 `544c363`, #2 `a6090ae`, #3 `3ca7eaf`, #4
`147747c`, audit `793356a`. Each source head descends from its predecessor.

## Merge commits in this stack

A GitHub merge commit has the target tip and PR head as parents. It preserves
the original source commits and records the PR merge on the target branch. It
does **not** update the source branch to contain that new merge commit.

The current source branches are stacked, while their PRs target the preceding
source branches. Merging #1 into `revision/...` creates a merge commit on
`revision/...` that is not an ancestor of the unchanged `research/...` head.
The same applies to #2 and #3 target-only merge commits. A final PR from the
current validation head would preserve every source commit and the existing
scientific merge commit, but would omit hypothetical target-only merge commits
from #1–#3. GitHub PR records still exist; those merge commit objects would not
be reachable from main. The earlier plan incorrectly implied that they were.

## Compare integration strategies

| Strategy | Source content and SHAs | PR merge commits in main | Review implications |
| --- | --- | --- | --- |
| Consolidated PR from validation to main | Preserves current source content and all commits reachable from the validation head; adds one final integration merge commit. | Only the final integration merge is added; target-only #1–#4 merges are not part of the source head. | One large 384-path review. Clear final boundary, but less granular acceptance and the four current draft PRs become superseded. |
| Retarget #1–#4 to main, then merge sequentially | Preserves each source commit SHA and content. Descendant heads should diff from the previously merged head. | All four GitHub merge commits stay in main: each later merge has prior main as its first parent. | Keeps four review boundaries and exposes each layer. PR #1 grows to include revision-branch changes; every retarget requires fresh diff review and CI. |

## Recommendation

Prefer **sequential retargeting to main with merge commits** if repository
policy allows it. This best preserves scientific source SHAs, all four PR merge
commits and individual reviews. The current graph supports this: PR #1 head is
an ancestor of #2 head, #2 of #3, and #3 of #4. After each PR is retargeted and
merged, verify that the next PR's merge base is exactly the preceding reviewed
head and that its diff contains only the next increment. If not, stop and
re-review; do not resolve by manually replaying commits.

Retargeting #1 from revision to main enlarges its diff to include the revision
branch content that main lacks. Review that content intentionally. If policy
disallows retargeting, use one consolidated PR from validation to main, with an
explicit acceptance that only source commits and a final merge record will be
in main. Squash replaces source SHAs; fast-forward omits per-PR merge commits
and may violate branch protection. Neither is preferred.

## SHA preflight

Snapshot values below must be refreshed after approval and immediately before
integration. Stop on any mismatch or ancestry change.

```powershell
git fetch origin --prune
$expectedMain = '29645563bd64a67aae2482ab6c87bd5e32fecb11'
$expectedP1 = '544c363c19a08574d30e7e2c064a78ce1bdfb601'
$expectedP2 = 'a6090ae3030ef52f333fe14380839df4a7d879eb'
$expectedP3 = '3ca7eaff5dc91701ecf7ea0dabdf7f185700a035'
$expectedP4 = '147747cf855dbacbb221f2074908dde1b0c77860'
if ((git rev-parse origin/main) -ne $expectedMain) { throw 'main moved; refresh audit' }
if ((git rev-parse origin/research/jorge-2026-experimental-upgrade) -ne $expectedP1) { throw 'PR1 head moved' }
if ((git rev-parse origin/refactor/repository-modernization-2026) -ne $expectedP2) { throw 'PR2 head moved' }
if ((git rev-parse origin/security/dependency-hardening-2026) -ne $expectedP3) { throw 'PR3 head moved' }
if ((git rev-parse origin/validation/experimental-readiness-2026) -ne $expectedP4) { throw 'PR4 head moved' }
git merge-base --is-ancestor origin/main origin/validation/experimental-readiness-2026
if ($LASTEXITCODE -ne 0) { throw 'main diverged; refresh audit' }
git rev-list --left-right --count origin/main...origin/validation/experimental-readiness-2026
```

## Sequential retarget procedure

After maintainer approval, change each PR base to `main` in GitHub, in order.
Wait for GitHub to recalculate its diff, rerun CI and obtain fresh review after
each base change. Merge with **Create a merge commit** only after checking both
full SHAs and the changed-file list.

1. Retarget #1; review the expanded revision-plus-science diff and merge head
   `544c363` to main, creating `M1`.
2. Fetch and verify `M1` has PR #1 head as a parent. Retarget #2; verify
   `git merge-base origin/main origin/refactor/repository-modernization-2026`
   is exactly `544c363`, inspect the modernization-only diff, rerun checks, and
   merge `a6090ae` to create `M2`.
3. Retarget #3; verify merge base exactly `a6090ae`, inspect the security-only
   diff, rerun checks, and merge `3ca7eaf` to create `M3`.
4. Retarget #4; verify merge base exactly `3ca7eaf`, inspect the validation and
   contract diff, rerun Windows/Linux/research checks, and merge `147747c` to
   create `M4`.

After every merge, fetch refs and verify the new merge SHA has the previous main
as first parent and the PR head as second parent. Verify the next source head
descends from the just-integrated PR head. GitHub performs the merge; do not
manufacture local merge commits.

### Prepared text if consolidated integration is selected

This is the alternative if sequential retargeting is disallowed. Create a draft
PR from `validation/experimental-readiness-2026` to `main`, then use this text:

**Title:** `Integrate reviewed AETHON research, modernization, security and validation`

**Body:**

> Integrates the reviewed AETHON chain at validation head
> `147747cf855dbacbb221f2074908dde1b0c77860` into the reviewed main base.
> Preserves original source commit SHAs, scientific files and results,
> dependency locks, security controls and versioned precision/generation
> contracts. This creates one final integration merge commit. Hypothetical
> merge commits from PRs #1–#4 on their current target branches are not
> ancestors of this head and therefore are not included.
>
> Acceptance requires current-head Linux and Windows workflows and research
> audit to pass; integrity verification of 127 scientific files, 31 evidence
> files, six historical manifests and 9,139 B3/B4 pairs; seven upstream lock
> audits with zero findings/skips; and review of source/lock diffs.
>
> Residual risks: exact PyTorch binary vulnerability coverage is NOT_AUDITED;
> historical vulnerable packages remain restricted to controlled reproduction;
> CUDA and prospective ASR/statistical campaigns are NOT_RUN; and the repository
> has no explicit license, requiring an owner decision before tagged release or
> redistribution. Engineering review does not approve final scientific campaigns.

## Recovery and post-merge verification

- A SHA mismatch, failed job, unexpected diff or merge-base change cancels that
  step. Fetch and regenerate the audit; retain every branch.
- Rehearse only in a disposable worktree. Abort local conflicts with
  `git merge --abort`; do not reset or clean shared checkouts.
- If an incorrect merge lands, record its SHA and revert it through a reviewed
  PR with `git revert -m 1 <merge-sha>`. Do not rewrite history.
- After M4, verify all four source heads and all four PR merge commits are
  ancestors of main. Then verify 127 scientific hashes, 31 evidence hashes,
  six manifests, LFS payloads and 9,139 B3/B4 pairs.
- Rerun tests, Ruff, pip check, lock audit, CLI checks and required Actions on
  main. Compare the diff against the pre-merge main SHA. Preserve all historical
  outputs and locks. Mark GPU NOT_RUN absent actual hardware validation.
