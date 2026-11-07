# Authorization issuer adversarial tests

The original PR #30 proof remains byte-for-byte in the review worktree and its
source hash is recorded in `AUTH_ISSUER_ROOT_CAUSE.md`. It was executed against
the PR #29 worktree and demonstrated the vulnerable route. The historical file
is not changed into a passing test.

Active tests add coverage that the issuer token, direct registration helper,
and writable module registry are absent; a manually constructed base object is
rejected by `PrivateRunStore`, `StorageBackend.open_run`, and `ReviewLedger`;
and subclasses whose `check()` returns either `None` or `True` are rejected
without a run or capability. Existing tests cover dataclass clones, snapshots,
subject mismatch, expiry, foreign/closed capabilities, and the legitimate
synthetic lifecycle.

The fixed-branch execution of the unchanged reproduction stopped at import
with `ImportError` for `_AUTHORIZATION_ISSUER` (exit 1). This is distinct from
the historical vulnerable execution and from the active API-level rejection
tests.

Tests use only synthetic fixture receipts and storage. They do not produce
scientific judgments, efficacy estimates, or operational authorization.
