# Historical scientific-integrity revalidation

Worktree: `review/scientific-manifest-closure-v1`, HEAD `2034aade9b56bf76ff13f4816a5ff9de73a879a6`. Source historical dataset hash was checked before and after the B3/B4 comparison.

| Item | Result | Evidence and scope |
|---|---|---|
| 127 protected scientific files | PASS, recalculated | `scripts/repository_inventory.py verify`; verified against baseline `544c363c19a08574d30e7e2c064a78ce1bdfb601` |
| 31 indexed evidence items | PASS, recalculated | `scripts/verify_research_evidence.py --git-tree HEAD`; 31 hashes matched working tree and HEAD |
| Six historical manifests | PASS, recalculated | `scripts/verify_historical_dependencies.py`; preserved from `a6090ae3030ef52f333fe14380839df4a7d879eb` |
| 9,139 B3/B4 pairs | PASS, recalculated read-only | Same CSV read/outer-join/one-to-one/label/mismatch assertions as `validate_historical_decisions.py`; 9,139 pairs, zero decision mismatches; no inference |
| B3/B4 source CSV | PASS, identity | SHA-256 `914901a1ed82836dfb42567cb376ec90f20459d1ad0f9b12d72568f4bfca202a` before and after |
| 80 historical metric values | REUSED, source identity rechecked | `metrics_by_dataset.csv` SHA-256 `e2b9746d98d3645668969c6eed881844b66bd82673f702bd6f3bd157638b7f34` matches `frozen-metrics-comparison.json`, which records 80 values, `atol=1e-12`, zero mismatches. The numeric comparison receipt was not regenerated in this review. |
| Five LFS payloads | PASS, hashes recalculated | Each current payload SHA-256 matches the preserved five-file receipt; `git lfs fsck` reports OK |
| Five preexisting local files | PASS, hashes recalculated | All five original checkout files match their previous preserved SHA-256 receipt; no stash or overwrite |
| Independent raw dataset canonical hash | NOT_AUDITED | No independent trusted canonical reference was present |

The existing `validate_historical_decisions.py` was invoked separately. Its assertions completed, but the script failed while creating its new output directory under `results/research_2026` (`WinError 5`). No historical output was overwritten. To preserve the requested read-only scope, the same read/merge/assertion calculation was rerun with JSON printed to stdout and file writing omitted; the result above is from that full 9,139-pair calculation. CI #42322507843 also ran the unmodified verifier successfully on Windows and Linux.
