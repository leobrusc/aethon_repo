# Historical Preservation Recheck

## Fresh checks in this review

| Control | Result | Evidence |
|---|---|---|
| 127 protected scientific files | PASS | `python -B scripts/repository_inventory.py verify` verified 127 against baseline `544c363c19a08574d30e7e2c064a78ce1bdfb601` |
| 31 indexed evidence hashes | PASS | `python -B scripts/verify_research_evidence.py --git-tree HEAD` |
| Six historical manifests | PASS | `python -B scripts/verify_historical_dependencies.py` |
| Five JSONL assets | PASS for bytes/size; one parse failure | Hashes and sizes match protected inventory; see JSONL audit |
| Five Git LFS payloads | PASS | `git lfs fsck`; all expected object IDs present |
| 9,139 B3/B4 pairs | PASS, recalculated read-only | Source `results/revision/detection/per_prompt_results.csv`, SHA-256 `914901a1ed82836dfb42567cb376ec90f20459d1ad0f9b12d72568f4bfca202a`; one-to-one keys paired, labels equal, zero decision mismatches |
| 80 historical metrics | Reused, not recalculated | Existing receipt `docs/science/remediation-v1/validation/summary.json` says 80 checked; receipt itself is within verified evidence tree |
| Five pre-existing local files | Preserved | Original checkout hashes recorded in recovery inventory; no original-worktree writes |

The B3/B4 comparison read both CSV conditions in memory and performed an outer one-to-one merge on dataset, prompt ID, and prompt SHA. It did not write a receipt or alter the CSV. The existing historical equivalence receipt has source hash `914901a1...` and the same 9,139/zero-mismatch result.

## Changes and limits

No scientific dataset, model, threshold, protocol, manifest, dependency lock, or result was edited. Working-tree hashes for the five protected datasets match the inventory. The `hf_red_team_attempts.jsonl` syntax failure is present in the pinned bytes and is not treated as data corruption or silently repaired.

The five local files are in the original checkout, not the review branch; they remain preserved there. This review adds only synthetic test/documentation files to the isolated branch. Historical records for 80 metrics are reused rather than independently recomputed in this phase.
