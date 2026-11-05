# Integration and recovery plan

Use GitHub **merge commits** for the stacked PRs in dependency order. Merge
commits retain original scientific commits and record review boundaries. Squash
would replace commit IDs and weaken experiment provenance. Fast-forward retains
SHAs and is currently possible from main to PR #4, but bypasses per-PR merge
records and may conflict with branch protection. Do not cherry-pick or replay
stacked commits.

1. PR #1 `544c363` -> `revision/bracis-reviewer-experiments` (`6ec4b81`).
2. PR #2 `a6090ae` -> `research/jorge-2026-experimental-upgrade` (`544c363`).
3. PR #3 `3ca7eaf` -> `refactor/repository-modernization-2026` (`a6090ae`).
4. PR #4 `147747c` -> `security/dependency-hardening-2026` (`3ca7eaf`).
5. After those merge, create a final integration PR from the updated security
   branch to `main`, then merge it with a merge commit.

The existing four PRs target stacked bases, not `main`. Merging #4 directly to
`main` would bypass those base branches and their review sequence.

## Guarded preflight commands

Run in a clean integration worktree. Expected SHAs are the audit snapshot. If
one changes, stop, fetch and repeat the audit; never force an expected SHA onto
a moved ref.

```powershell
git fetch origin --prune
$expectedMain = '29645563bd64a67aae2482ab6c87bd5e32fecb11'
$expectedP1 = '544c363c19a08574d30e7e2c064a78ce1bdfb601'
$expectedP2 = 'a6090ae3030ef52f333fe14380839df4a7d879eb'
$expectedP3 = '3ca7eaff5dc91701ecf7ea0dabdf7f185700a035'
$expectedP4 = '147747cf855dbacbb221f2074908dde1b0c77860'
if ((git rev-parse origin/main) -ne $expectedMain) { throw 'main moved; redo audit' }
if ((git rev-parse origin/research/jorge-2026-experimental-upgrade) -ne $expectedP1) { throw 'PR1 head moved' }
if ((git rev-parse origin/refactor/repository-modernization-2026) -ne $expectedP2) { throw 'PR2 head moved' }
if ((git rev-parse origin/security/dependency-hardening-2026) -ne $expectedP3) { throw 'PR3 head moved' }
if ((git rev-parse origin/validation/experimental-readiness-2026) -ne $expectedP4) { throw 'PR4 head moved' }
git merge-base --is-ancestor origin/main origin/validation/experimental-readiness-2026
if ($LASTEXITCODE -ne 0) { throw 'main diverged; stop and re-review' }
git rev-list --left-right --count origin/main...origin/validation/experimental-readiness-2026
```

After owner approval and successful required checks, merge each PR in GitHub
with **Create a merge commit**, in order. Check each exact base and head SHA
immediately before merging. After each merge, fetch refs and confirm the target
advanced to the GitHub merge commit, the reviewed head remains an ancestor, and
the next PR still has the intended base. Rerun checks when GitHub recalculates
them against the updated base.

After PR #4 merges, record the resulting security SHA and create the final PR:

```powershell
git fetch origin --prune
$expectedSecurity = '<reviewed post-PR4 security SHA>'
if ((git rev-parse origin/security/dependency-hardening-2026) -ne $expectedSecurity) { throw 'security head moved' }
$expectedMain = '<reviewed main SHA immediately before final PR>'
if ((git rev-parse origin/main) -ne $expectedMain) { throw 'main moved; redo ancestry checks' }
git merge-base --is-ancestor origin/main origin/security/dependency-hardening-2026
if ($LASTEXITCODE -ne 0) { throw 'main is not an ancestor; stop and review' }
gh pr create --base main --head security/dependency-hardening-2026 --draft `
  --title 'Integrate reviewed AETHON research, modernization and security chain' `
  --body-file integration-pr.md
```

Before final merge, verify the new PR's head/base SHAs, approvals and required
checks; use a merge commit. Do not squash, rebase, force push, delete branches
or push directly to `main`.

## Recovery

- Before merge: SHA mismatch, failed check or conflict cancels that step. Fetch
  and regenerate the audit; keep branch refs intact.
- Rehearse only in a disposable worktree. If a local trial conflicts, use
  `git merge --abort`; do not reset or clean a shared checkout.
- If an incorrect merge reaches a target, record its SHA and submit a fix-forward
  PR. Revert a merge commit with `git revert -m 1 <merge-sha>` after review and
  validation. Do not rewrite published ancestry.
- Keep LFS payloads, evidence, lock files and historical outputs intact.
