# Dataset Sources

This directory contains adversarial prompt datasets used by AETHON.

Canonical loader aliases:

| Alias | Local file | Rows | Label policy | Source |
|---|---|---:|---|---|
| `prompt_injections_train` | `hf_prompt-injections_train.parquet` | 546 | existing `label` | Existing local dataset |
| `prompt_injections_test` | `hf_prompt-injections_test.parquet` | 116 | existing `label` | Existing local dataset |
| `red_team_attempts` | `hf_red_team_attempts.jsonl` | 38,961 | adversarial by default | Anthropic HH-RLHF red-team attempts, `Anthropic/hh-rlhf` |
| `kaggle_redteam` | `kaggle_red_team_prompts.json` | 99 | existing `answer` | Existing local Kaggle export |
| `advbench_harmful` | `advbench_harmful_behaviors.csv` | 520 | adversarial by default | `llm-attacks/llm-attacks`, AdvBench harmful behaviors |
| `jailbreakbench_behaviors` | `jailbreakbench_behaviors.jsonl` | 200 | `harmful` = 1, `benign` = 0 | `JailbreakBench/JBB-Behaviors`, `behaviors` config |
| `wildjailbreak_eval` | `wildjailbreak_eval.jsonl` | 2,210 | `adversarial_harmful` = 1, `adversarial_benign` = 0 | `walledai/WildJailbreak` evaluation set |
| `prompt_injection_core` | `neuralchemy_prompt_injection_core.jsonl` | 6,274 | existing `label` | `neuralchemy/Prompt-injection-dataset`, `core` config |
| `notinject` | `notinject.jsonl` | 339 | benign hard negatives (`0`) | `leolee99/NotInject` |
| `cyberseceval_prompt_injection` | `cyberseceval_prompt_injection.json` | 251 | adversarial prompt-injection cases (`1`) | Meta PurpleLlama `CybersecurityBenchmarks/datasets/prompt_injection/prompt_injection.json` |

`load_dataset("all")` concatenates only the canonical aliases above and does not include local backups or downloaded compressed archives.
