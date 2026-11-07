# Scientific preservation review

## Recomputed checks

| Control | Result | Evidence |
|---|---|---|
| Protected scientific inventory | PASS | 127 files against recorded base `544c363c19a08574d30e7e2c064a78ce1bdfb601` |
| Indexed research evidence | PASS | 31 hashes in working tree and Git HEAD |
| Historical manifests | PASS | All six working-tree hashes equal their Git HEAD blob hashes; see table below; all are inside the protected inventory |
| Historical B3/B4 pairs | PASS | Both byte representations parse to equal 36,556 × 14 tables; 9,139 pairs; all join keys and labels match; zero decision mismatches |
| Git LFS | PASS | `git lfs fsck` OK; five payloads listed |
| Five original local paths | PASS for preservation | Original checkout retains the same two modified tracked paths and three untracked files; none was changed by the separate review worktree |
| 80 historical metric values | REUSED | Receipt `docs/science/remediation-v1/validation/summary.json`, SHA-256 `a4c7fab61d0f70469b0faa1960bf1c0519c01012711ab07fbd63cce1fcf49342`; not recalculated here |

### Six historical evidence manifests

| Manifest | SHA-256 (working tree = Git HEAD) |
|---|---|
| `docs/research_2026_evidence/dp/manifest.json` | `c68278d53090c9018f2277ed5b6752b2a69da55b03881b75bf36766865da8e3d` |
| `docs/research_2026_evidence/integrity/manifest.json` | `500b77a4b3487c13903ef0457a4ef60134f886acb6d826f44d132c3b8aa21dc6` |
| `docs/research_2026_evidence/promptguard/manifest.json` | `3a5f6fa677f17297d0f3d856f4e94e986d35331403bbbe040500c8db314ca8d2` |
| `docs/research_2026_evidence/nested/manifest.json` | `10396786da2ba56ca6e413a8ef3f257a561efbed6e687f57bcb6765c34c3a4d6` |
| `docs/research_2026_evidence/protectai_smoke/manifest.json` | `77247b37f7c2288406cb6d526f048e4954bf40273c64bc9e68830b65acc37cee` |
| `docs/validation/evidence/protectai-current-manifest.json` | `68b6ee149bf42703c4b597353000f6dd2badd32a037bcbb23b6a3630fc1244b5` |

## CSV SHA discrepancy explained

The current Windows worktree CSV SHA-256 is `914901a1ed82836dfb42567cb376ec90f20459d1ad0f9b12d72568f4bfca202a`; the Git blob at the exact reviewed HEAD is `66130f23a92ea05fca856c808a4049245a31d0f6c530bbba517473be389e7a15` (6,718,635 bytes). They are **not byte-identical**. The working tree contains CRLF line endings while the Git blob contains LF; replacing each CRLF byte pair with LF in memory yields byte-for-byte equality with the Git blob. No file was rewritten or normalized. Independently parsing both byte sequences produced equal dataframes (36,556 rows × 14 columns) and the same 9,139 paired B3/B4 rows with zero prediction mismatches. This is a verified line-ending transformation and semantic equality, not raw-byte identity.

## Boundaries

The 80 metric-value comparison is evidence reuse only, not a fresh recalculation. The five local files are verified present/status-preserved in the original checkout; their untracked copies are intentionally absent from the review worktree. No thresholds, labels, seeds, manifests, datasets, locks or results were altered. No scientific inference was run.
