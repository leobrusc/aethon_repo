# Phase 7C validation record

Validation was performed on branch `fix/src02-native-contract-safety-v1`,
implementation commit `e1821ce83b714cde52ea917f48e7fd1453fc95e5`, based on
`c5567fd947f9a776da98cbf0b3ac98e93bac51e7`. GitHub Actions run
`42412776565` tested that implementation commit; Linux, Windows and
research/GPU-audit jobs all completed successfully. The hosted workflow used
its configured isolated CI profiles. Local dependency installation was not
performed. GPU inference remained NOT_RUN.

## Results

| Check | Result | Evidence / limitation |
|---|---|---|
| Corrected safety-model tests | PASS | `python -B -m pytest -q -p no:cacheprovider tests/test_src02_safety_model.py`: 24 passed. |
| Bounded state exploration | PASS | 16,642 reachable states, 32,651 accepted transitions, 339,477 rejected attempts, depth 12; zero asserted safety violations. |
| Full pytest | FAIL (environment/repository inputs) | 423 passed, 9 failed. Eight failures are dataset-loader/benchmark tests because the five JSONL datasets in this checkout are empty/unparseable. The remaining legacy OpenSSL test fails to start the Git-for-Windows executable (`couldn't create signal pipe, Win32 error 5`, process exit 3221225794). No tests were skipped or replaced to hide this. |
| Ruff | PASS | `python -B -m ruff check --no-cache .worktrees\\src02-contract-remediation`: All checks passed. |
| pip check | PASS | `No broken requirements found`; no packages installed. |
| Research evidence index | PASS | `verify_research_evidence.py --git-tree HEAD`: 31 artifact hashes verified in working tree and HEAD. |
| Historical dependency manifests | PASS | Six manifests preserved from `a6090ae3030ef52f333fe14380839df4a7d879eb`. |
| Repository scientific inventory | FAIL | Existing verifier reports five protected JSONL mismatches: `hf_red_team_attempts.jsonl`, `jailbreakbench_behaviors.jsonl`, `neuralchemy_prompt_injection_core.jsonl`, `notinject.jsonl`, `wildjailbreak_eval.jsonl`. No file was normalized or rewritten. This prevents claiming a fresh 127-file integrity PASS. |
| Git LFS | PASS | `git lfs fsck`: `Git LFS fsck OK`. |
| Offline preflight | PASS (fail-closed expected) | Exit 2, `PILOT_BLOCKED`, `executed: false`; all eight gates PENDING. |
| `git diff --check` | PASS | No output. |
| Five local files / 80 metrics | REUSED, not recalculated | Phase 7A receipt states five local files preserved; historical 80 metric values are linked to receipt SHA-256 `a4c7fab61d0f70469b0faa1960bf1c0519c01012711ab07fbd63cce1fcf49342`. This phase did not rewrite or recompute them. |
| 9,139 B3/B4 paired rows | REUSED | Phase 7A read-only comparison recorded 9,139 rows and zero decision mismatches. Its working-tree CSV hash differs from the Git blob hash because of line-ending/content representation; no normalization was performed. |

## Evidence hashes

SHA-256 values below identify the current working-tree bytes, not Git blob IDs:

| Evidence | SHA-256 |
|---|---|
| Corrected model `models/safety_model.py` | `8dc2c581a3e4adbf9216ebeac41b72869dac2601c7636a93c580784e44136287` |
| Active test `tests/test_src02_safety_model.py` | `c787bafec9b983f3b25000f90feabc6a7c44c68e43623f88ff93d98939e81073` |
| Prior Phase 7A validation record | `891c230766c8d2a9418a42c5bfe6aafba057ba6e2ff311e10fac1315fd506b04` |
| PR #34 original model source (historical) | `c4dd46acb740dd2cf8960857b788507291908fe673d574f769757b2e7c1ecae2` |
| PR #34 original model Git blob | `04490105d90603f131f8baf3663eaaf59cb6e021` |
| PR #34 false-commit review (historical) | `67148a524be9d2fc338de9970c97ac38e1ba8d724f340ec08727b410c75b54eb` |

The historical reproductions and reports were not edited. Their historical
hashes are carried forward from the PR #34 evidence record; they were not
recomputed in this phase.

## Disposition

The abstract model's scoped safety result is `SRC02_CONTRACT_REMEDIATED`,
subject to independent review. The overall repository validation is not clean:
the full suite has environmental/input failures and the protected-file
inventory currently reports the five JSONL mismatches above. These results do
not authorize a native backend. Keep `SRC-02 NOT_AUTHORIZED`,
`DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED`, and all eight operational gates
`PENDING`.
