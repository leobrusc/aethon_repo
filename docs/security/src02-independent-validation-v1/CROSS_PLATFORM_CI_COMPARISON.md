# Cross-Platform CI Comparison

## Workflow runs

Both requested GitHub Actions runs completed all three jobs successfully.

| Run | Tested revision | Linux CPU dev | Windows CPU dev | Research/GPU audit | Tests |
|---|---|---|---|---|---|
| `42412776565` | Merge ref `35a3b266d55292be6f86a74d8855ed400a48a41b`, containing implementation `e1821ce83b714cde52ea917f48e7fd1453fc95e5` on base #34 | SUCCESS | SUCCESS | SUCCESS | 432 passed on each OS |
| `42413419166` | Merge ref `4c17071...`, containing PR #35 HEAD `f49f1ce6481719fc6696a08769cbb7cfde46dfb9` on base #34 | SUCCESS | SUCCESS | SUCCESS | 432 passed on each OS |

The second run tests the requested final PR HEAD, not merely the earlier implementation commit. Runners were Ubuntu 24.04 and Windows Server 2025. GPU inference was `NOT_RUN`. The workflow used LFS checkout/fetch and reports the repository inventory check passing for 127 files against base `544c363c19a08574d30e7e2c064a78ce1bdfb601`.

CI logs include explicit normalization/count outputs for `jailbreakbench_behaviors` (200), `neuralchemy_prompt_injection_core` (6,274), `notinject` (339), and `wildjailbreak_eval` (2,210). They do not provide explicit evidence that `hf_red_team_attempts.jsonl` was parsed record by record. Do not infer all-five JSONL syntax validation from the inventory check.

## Local Windows validation

On the current Windows review environment, the complete pytest suite produced `437 passed, 1 failed` (one warning). The failure is `tests/test_pilot_collector.py::test_production_ed25519_verifier_with_ephemeral_synthetic_key`: Git-for-Windows OpenSSL returned `3221225794` and could not create a signal pipe (`Win32 error 5`). This is an environment/process-creation failure, not evidence that the native SRC-02 model is incorrect. The test was not mocked or bypassed; no security policy, EDR, or privilege setting was changed.

The local full-suite revision included six independent audit tests, accounting for the difference from the 432 tests in CI. CI had no such local-only tests. Hosted CI installed its declared isolated test profiles; no package was installed in the local audit environment.

## Interpretation

CI proves its declared test jobs succeeded on those merge refs and environments. It does not prove native backend behavior, GPU inference, all-five JSONL parsing, or safety beyond tests/model bounds. The local OpenSSL test remains environment-blocked; retain that result transparently.
