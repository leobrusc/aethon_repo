# ProtectAI GPU execution

The runner uses deterministic run directories under `results/revision/baselines/runs/<run-id>/`, atomic JSONL checkpoints, stable prompt keys, and strict scientific-fingerprint validation on resume. Device and batch size are operational metadata; detector/model, tokenizer, datasets, labels, max length, and truncation are scientific configuration.

Windows PowerShell smoke test:

```powershell
python src/run_baseline_benchmark.py --run-id protectai_smoke_cpu_v1 --device auto --smoke --output-root results/revision/baselines
```

PowerShell multiline continuation uses a backtick (`). Bash uses `\`.

Linux GPU:

```bash
python src/run_baseline_benchmark.py \
  --run-id protectai_gpu_full_v1 --device cuda --auto-batch \
  --checkpoint-every 100 --output-root results/revision/baselines
```

Resume:

```bash
python src/run_baseline_benchmark.py \
  --run-id protectai_gpu_full_v1 --device cuda --auto-batch \
  --checkpoint-every 100 --resume --output-root results/revision/baselines
```

Offline analysis is transformer-free:

```bash
python src/analyze_baseline_results.py --run-id protectai_gpu_full_v1 --output-root results/revision/baselines
```

Tokenization cache status: **NONE** (correctness takes precedence; tokenization is performed by the adapter per batch). No publication inference is run by tests.
