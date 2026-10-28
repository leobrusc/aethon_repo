# Experiment Plan

## Objective

Run reproducible single-model AETHON benchmark profiles for the selected open-weight models while preserving ASR evaluation, B0-B4 ablations, metrics, diagnostics, progress tracking, and resumable CSV output.

## Profiles

| Profile | Config | Model | Output root |
|---|---|---|---|
| Phi-3 Mini | `configs/phi3_benchmark.json` | `phi-3-mini-4k-instruct` | `results/phi3_benchmark` |
| Qwen 2.5 3B | `configs/qwen3b_benchmark.json` | `qwen2.5-3b-instruct` | `results/qwen3b_benchmark` |
| Qwen 2.5 7B | `configs/qwen7b_benchmark.json` | `qwen2.5-7b-instruct` | `results/qwen7b_benchmark` |
| Llama 3.2 1B | `configs/llama1b_benchmark.json` | `llama-3.2-1b-instruct` | `results/llama1b_benchmark` |
| Llama 3.2 3B | `configs/llama3b_benchmark.json` | `llama-3.2-3b-instruct` | `results/llama3b_benchmark` |
| Llama 2 7B Chat | `configs/llama7b_benchmark.json` | `llama-2-7b-chat` | `results/llama7b_benchmark` |

## Dataset Matrix

Each profile uses the same five datasets:

| Dataset | Rows | Positive labels | Negative labels | Notes |
|---|---:|---:|---:|---|
| `notinject` | 339 | 0 | 339 | Benign-only false-positive set; AUROC is not computable alone. |
| `prompt_injection_core` | 6,274 | 3,736 | 2,538 | Mixed-class prompt injection set. |
| `jailbreakbench_behaviors` | 200 | 100 | 100 | Mixed ASR-eligible jailbreak set. |
| `red_team_attempts` | 38,961 | 38,961 | 0 | ASR-eligible adversarial-only set; AUROC is not computable alone. |
| `cyberseceval_prompt_injection` | 251 | 251 | 0 | ASR-eligible adversarial-only prompt injection set. |

Total per profile: 46,025 source rows and 230,125 prompt-condition evaluations across `B0`-`B4`.

## Ablations

Every profile enables:

- `B0`: no defense;
- `B1`: regex heuristic only;
- `B2`: TF-IDF + Logistic Regression only;
- `B3`: heuristic OR ML deterministic cascade;
- `B4`: B3 plus differentially private noisy audit count.

## Execution Commands

Run one profile:

```bash
python src/run_benchmark.py --config configs/llama1b_benchmark.json
```

Resume an interrupted run by reusing the original run id:

```bash
python src/run_benchmark.py \
  --config configs/llama1b_benchmark.json \
  --run-id <existing-run-id> \
  --resume
```

Fast validation before a full live run:

```bash
python src/run_benchmark.py \
  --config configs/llama1b_benchmark.json \
  --fast-validation \
  --dry-run
```

Small live timing calibration:

```bash
python src/run_benchmark.py \
  --config configs/llama1b_benchmark.json \
  --dataset-limit 20 \
  --condition-filter B0 B1 \
  --run-id llama1b_timing_probe
```

## Recommended Run Order

1. Run `--fast-validation --dry-run` for every profile to validate config parsing, datasets, B0 path, output roots, diagnostics, and manifests.
2. Run a small live timing probe per model using `--dataset-limit 20 --condition-filter B0 B1`.
3. Start full profiles from smallest to largest expected runtime:
   - `llama1b_benchmark`
   - `llama3b_benchmark`
   - `phi3_benchmark`
   - `qwen3b_benchmark`
   - `llama7b_benchmark`
   - `qwen7b_benchmark`
4. Monitor `progress.json`, `master_results.csv`, `diagnostics.csv`, and `benchmark_readiness_report.md` under each model-specific output root.

## Outputs

Each profile writes to its own output root:

```text
results/<profile>/
|-- aggregated/
|   |-- master_results.csv
|   |-- benchmark_manifest.jsonl
|   |-- diagnostics.csv
|   |-- progress.json
|   |-- benchmark_readiness_report.md
|   |-- metrics_summary_<run_id>.csv
|   `-- metrics_summary_<run_id>.json
|-- per_model/
|   `-- <model>.csv
`-- tables/<run_id>/
```

## Validity Notes

- AUROC is computable only within model/dataset/condition groups containing both positive and negative labels.
- ASR is computable only for eligible adversarial rows with adjudicated `attack_success` values.
- Full-profile publication claims should report `diagnostics.csv`, ASR coverage, metric warnings, and readiness reports alongside headline metrics.
