# Expected Runtime Estimates

## Basis

Estimates use observed benchmark `latency_ms` medians from existing local result CSVs under `results/`. They are hardware- and cache-dependent. The observed runs appear to be local live Hugging Face inference with very slow per-response generation for some model/dataset combinations, so these numbers should be treated as conservative local-machine estimates, not GPU/server estimates.

Where a target model has no direct observations yet:

- `phi-3-mini-4k-instruct` uses observed `llama-3.2-3b-instruct` timings as a 3B-class proxy.
- `qwen2.5-3b-instruct` uses observed `llama-3.2-3b-instruct` timings as a 3B-class proxy.
- `qwen2.5-7b-instruct` uses observed `llama-2-7b-chat` timings as a 7B-class proxy.

Dataset row counts:

| Dataset | Rows |
|---|---:|
| `notinject` | 339 |
| `prompt_injection_core` | 6,274 |
| `jailbreakbench_behaviors` | 200 |
| `red_team_attempts` | 38,961 |
| `cyberseceval_prompt_injection` | 251 |
| Total source rows | 46,025 |
| Total prompt-condition evaluations per profile | 230,125 |

## Profile Estimates

| Profile | Model | Timing source | Estimated full runtime |
|---|---|---|---:|
| `llama1b_benchmark` | `llama-3.2-1b-instruct` | observed same model | 774:18:20 |
| `llama3b_benchmark` | `llama-3.2-3b-instruct` | observed same model | 2944:53:56 |
| `phi3_benchmark` | `phi-3-mini-4k-instruct` | observed 3B-class proxy | 2944:53:56 |
| `qwen3b_benchmark` | `qwen2.5-3b-instruct` | observed 3B-class proxy | 2944:53:56 |
| `llama7b_benchmark` | `llama-2-7b-chat` | observed same model | 7042:16:56 |
| `qwen7b_benchmark` | `qwen2.5-7b-instruct` | observed 7B-class proxy | 7042:16:56 |

## Interpretation

These full-profile estimates are dominated by:

- `red_team_attempts`, because it contains 38,961 rows;
- live inference conditions where prompts are allowed to reach the model;
- local CPU or otherwise slow inference throughput in observed runs.

Several B2-B4 estimates are near-zero for adversarial-only datasets because observed runs frequently blocked prompts before downstream model inference. That behavior is valid for estimating this benchmark pipeline, but it should not be used as a pure model-throughput estimate.

## Recommended Calibration

Before committing to a full run, run a model-specific live probe:

```bash
python src/run_benchmark.py \
  --config configs/llama1b_benchmark.json \
  --dataset-limit 20 \
  --condition-filter B0 B1 \
  --run-id llama1b_timing_probe
```

Then recompute expectations from that model's `results/<profile>/aggregated/master_results.csv`.

## Practical Minimum Runs

For development and validation:

| Purpose | Suggested command shape | Expected scale |
|---|---|---:|
| Config smoke test | `--fast-validation --dry-run` | 5 rows, B0 only |
| Live model sanity check | `--dataset-limit 5 --condition-filter B0` | 25 prompt-condition rows |
| Timing probe | `--dataset-limit 20 --condition-filter B0 B1` | 200 prompt-condition rows |
| Publication run | full profile config | 230,125 prompt-condition rows |
