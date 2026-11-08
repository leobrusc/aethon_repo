# Scientific JSONL Integrity Audit

## Method

Read-only inspection compared working-tree bytes and sizes against `docs/modernization/scientific-integrity.json`, Git HEAD blobs, index entries, LFS pointer metadata, and JSONL parsing. No dataset was rewritten, normalized, restored, or repaired. Current review worktree is fully hydrated; previous Phase 7C worktree was not.

All five current working-tree SHA-256 values equal the protected inventory values, and all worktree paths are clean. Four files parse as JSONL. `hf_red_team_attempts.jsonl` fails JSON parsing on physical line 1, column 4020, despite its exact expected size/hash. The same bytes/hash are present in the original checkout and in the hydrated review checkout. This is a content-format defect in the pinned canonical bytes, not evidence of byte corruption.

| Relative path | WT bytes | WT SHA-256 / protected SHA-256 | HEAD blob / index | LFS materialized | Lines | JSONL |
|---|---:|---|---|---|---:|---|
| `datasets/hf_red_team_attempts.jsonl` | 55,487,878 | `1b197f9c836ce9a927f7d82f8c48c27439ad713ddcf2958a87faa7f09be2effd` / equal | `411858800ea111fe49c4f3e93090481001f3698d` / same pointer blob | Yes; blob is 133-byte LFS pointer | 38,961 | FAIL, line 1 col 4020 |
| `datasets/jailbreakbench_behaviors.jsonl` | 60,175 | `4f3a40e85e5be7314ae8e6cb5dc73f4197eca0e691b67d6a25a915b1a934a850` / equal | `2904e31a54f5e09ee8d5901cfd50004dcad86b4e` / same | Yes; 130-byte pointer | 200 | PASS |
| `datasets/neuralchemy_prompt_injection_core.jsonl` | 2,165,752 | `e7a1b0b9a21032df8b3ffcac1605841324d1266f30fb4d70e6d058af0cde685f` / equal | `7c7106cb42ee53df5b84742b7b8065d3a69fc033` / same | Yes; 132-byte pointer | 6,274 | PASS |
| `datasets/notinject.jsonl` | 67,357 | `e41959c6cd149a4f921cb70deff86f9aab10bfede0894b958e99980bf71349b8` / equal | `7d67d22910c48162cbb278380652279be5803f91` / same | Yes; 130-byte pointer | 339 | PASS |
| `datasets/wildjailbreak_eval.jsonl` | 1,825,386 | `2e74645416c7daa3b30ae11cb845a50cc9fe5d0b147e4ddc2ef5b0af23ec88a5` / equal | `78924ae9017777878101c608013cd82d3a6bce89` / same | Yes; 132-byte pointer | 2,210 | PASS |

All files use LF-only line endings in the hydrated worktree. No CRLF/LF transformation explains the parser failure. `filter=lfs` is configured; no text normalization was observed. The source tree's `hf_red_team_attempts.jsonl` blob is materialized rather than an LFS pointer, but its bytes and SHA match the protected canonical content.

## Conclusion

Checkout byte integrity: all five protected hashes match. Dataset syntax: one of five fails JSONL parsing in canonical bytes. No automatic repair is authorized. Consumers must treat that dataset as unusable for strict JSONL processing until a separately governed correction identifies intended content and versions it without overwriting the historical artifact.
