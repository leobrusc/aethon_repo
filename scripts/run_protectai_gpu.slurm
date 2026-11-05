#!/bin/bash
#SBATCH --job-name=aethon-protectai
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
set -euo pipefail
REPO_DIR="${REPO_DIR:-$PWD}"
VENV_DIR="${VENV_DIR:-$REPO_DIR/venv}"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_DIR/results/revision/baselines}"
cd "$REPO_DIR"
source "$VENV_DIR/bin/activate"
python - <<'PY'
import torch, transformers, platform
print(platform.platform()); print(torch.__version__, torch.version.cuda, torch.cuda.is_available())
if torch.cuda.is_available(): print(torch.cuda.get_device_name(0))
PY
python src/run_baseline_benchmark.py --device cuda --auto-batch --resume --output-root "$OUTPUT_DIR" 2>&1 | tee "$OUTPUT_DIR/protectai_gpu_${SLURM_JOB_ID:-local}.log"
