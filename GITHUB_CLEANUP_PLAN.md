# Incremental repository cleanup

Use the [audited modernization report](docs/modernization/REPORT.md).
The 55,487,878-byte red-team dataset is converted to an LFS pointer in a new
commit, preserving its hydrated SHA-256. The old blob remains in history.

No history migration, force push, garbage collection or remote deletion is part
of this work. Removing historical blobs would require separate authorization,
collaborator coordination and a recoverable mirror backup.

The [June plan](docs/archive/2026-06/GITHUB_CLEANUP_PLAN.md) is retained only as
historical context. Its destructive recommendations are superseded and must
not be followed as routine maintenance.
