# Git LFS and Checkout Diagnosis

## Observations

In the previous Phase 7C worktree at `f49f1ce6481719fc6696a08769cbb7cfde46dfb9`, each of the five paths was the small Git LFS pointer text (130–133 bytes). Parsing those pointer texts as JSONL naturally failed on line 1. This was incomplete LFS hydration, not loss of the LFS object.

The Phase 7D review worktree is hydrated. For the four LFS-tracked files, the HEAD and index contain the expected pointer blobs; the working tree contains bytes matching the pointer OID and expected byte size. `git lfs ls-files --long` reports the five expected SHA-256 object IDs and `git lfs fsck` reports OK. The fifth path, `hf_red_team_attempts.jsonl`, is a materialized Git blob in HEAD and has the expected protected SHA-256. No index/worktree mismatch is present.

| File | Pointer in Git blob | Materialized working data | Object verification |
|---|---|---|---|
| hf_red_team_attempts | No; materialized Git blob | Expected bytes/hash | Git inventory match |
| jailbreakbench_behaviors | Yes | Expected bytes/hash | LFS fsck OK |
| neuralchemy_prompt_injection_core | Yes | Expected bytes/hash | LFS fsck OK |
| notinject | Yes | Expected bytes/hash | LFS fsck OK |
| wildjailbreak_eval | Yes | Expected bytes/hash | LFS fsck OK |

## Diagnosis

The five “mismatches” observed in the unhydrated worktree were pointer-versus-content comparisons. They do not establish corruption. In the hydrated worktree all five SHA-256/size checks pass. Separately, `hf_red_team_attempts.jsonl` itself is syntactically invalid JSONL at line 1, column 4020; hydration does not cause or repair this.

No `git lfs pull`, checkout, restore, or write operation was used to repair files in this audit. The review worktree was independently created with the existing checkout configuration; prior worktree and original checkout were preserved.
