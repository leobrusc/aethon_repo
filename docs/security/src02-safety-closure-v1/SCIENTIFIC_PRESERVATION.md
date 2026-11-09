# Scientific Preservation

## Scope and controls

This phase changed only the abstract safety model, its contract tests/configuration and security documentation. No dataset, result, model, threshold, manifest, lock, historical receipt, LFS pointer, or inventory entry was edited. The invalid-JSONL finding for `hf_red_team_attempts.jsonl` remains independent and unresolved; the asset was not opened for transformation or rewritten here.

Prior independent review freshly recalculated the five protected JSONL working hashes and all five LFS objects; all expected byte hashes matched, while `hf_red_team_attempts.jsonl` failed JSONL parsing. That dataset validation is **reused** from PR #36 rather than repeated in this phase. The PR #36 evidence reported 127 protected files, 31 evidence hashes, six manifests, 9,139 paired B3/B4 rows with zero decision mismatches, and five LFS payloads verified. The 80 historical metrics were supported by a verified prior receipt and were not recomputed in Phase 7D or 7E.

The five pre-existing local files in the original checkout remain preserved and untouched. No scientific inference, training, evaluation, or prospective campaign was run.

## Historical test preservation

`tests/test_src02_dedup_audit.py` is unchanged from PR #36's Git tree: blob `c15d243c563d40edca0e150faad7b6de83fc9ab8`, canonical blob SHA-256 `96461be57f4101bf899f55399ef91c4f7895946aa959db4c64ae8c6da69716a7`. The Windows working tree has `core.autocrlf=true`, so checkout materialization has 161 CRLF lines and SHA-256 `ffd88f9f30a1a3e51710854dccdc48ca8a41e06737e407a898bf0ca4bb014062`; the Git blob has 161 LF lines. This is checkout conversion, not an edit to the historical Git object. The file is clean/unmodified in Git and is not staged. Because it intentionally asserts the old vulnerable behavior, `pytest.ini` excludes that historical reproduction from default acceptance collection. The code and original reports remain available for explicit forensic replay. New acceptance tests assert safe behavior.
