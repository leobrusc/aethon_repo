"""
run_experiment.py (updated)
- Orquestra execuções usando model_registry.get_model_driver(...)
- Suporta: --model, --dataset, --temp, --seed, --condition, --aethon-epsilon, --limit, --dry-run
- Grava resultados em results/{model}/{dataset}/{...}.json e atualiza experiment_manifest.json
"""
import argparse
import json
from datetime import datetime
from pathlib import Path
import time
import os

from dataset_loader import load_dataset
from aethon_heuristic import is_adversarial_heuristic
from aethon_full_pipeline import AethonFull
from model_registry import get_model_driver

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = PROJECT_ROOT / "results"
MANIFEST_PATH = PROJECT_ROOT / "experiment_manifest.json"

def log_manifest(entry: dict):
    if MANIFEST_PATH.exists():
        data = json.loads(MANIFEST_PATH.read_text())
    else:
        data = []
    data.append(entry)
    MANIFEST_PATH.write_text(json.dumps(data, indent=4))
    print(f"[MANIFEST] appended: {entry.get('run_id')}")

def safe_filename(s: str) -> str:
    return s.replace(" ", "_").replace("/", "_")

def run_experiment(model_name: str, dataset_name: str, temp: float = 0.2, seed: int = 42,
                   condition: str = "B0", aethon_epsilon: float = 1.2, limit: int = None, dry_run: bool = False, openai_model_override: str = None):
    print(f"[RUN] model={model_name} dataset={dataset_name} temp={temp} seed={seed} cond={condition} dry_run={dry_run}")

    df = load_dataset(dataset_name)  # returns standardized df with prompt_id, prompt_text, label
    if limit:
        df = df.head(limit)

    # instantiate model driver only when inference is needed
    model_driver = None
    if not dry_run:
        model_driver = get_model_driver(model_name, model_name=openai_model_override) if model_name.startswith("gpt") else get_model_driver(model_name)

    # aethon full object (for mitigation/audit)
    aethon = AethonFull(ml_model_path=None, epsilon=aethon_epsilon)

    results = []
    start = time.time()
    for idx, row in df.iterrows():
        pid = row["prompt_id"]
        text = row["prompt_text"]
        label = int(row.get("label", 1))  # 1 = adversarial by default

        # Heuristic detection
        hflag = is_adversarial_heuristic(text)

        # AETHON-ML (if implemented): for now we call AethonFull.decide to combine heuristic+ml
        decision = aethon.decide(text)  # returns action and meta

        if dry_run:
            resp_text = "[DRY-RUN]"
        else:
            try:
                # If model driver is OpenAI and override present, use that
                if model_name.startswith("gpt") and openai_model_override:
                    resp_text = model_driver.infer(text, max_tokens=256, temperature=temp)
                else:
                    resp_text = model_driver.infer(text, max_tokens=256, temperature=temp)
            except Exception as e:
                resp_text = f"[INFER_ERROR] {e}"

        out = {
            "prompt_id": pid,
            "prompt_excerpt": text[:200],
            "label": label,
            "heuristic_flag": bool(hflag),
            "aethon_action": decision.get("action"),
            "aethon_meta": decision.get("meta"),
            "response": resp_text
        }
        results.append(out)

    runtime = time.time() - start

    # write results
    out_dir = RESULTS_ROOT / safe_filename(model_name) / safe_filename(dataset_name)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = f"{safe_filename(model_name)}_{safe_filename(dataset_name)}_{condition}_s{seed}_t{str(temp).replace('.','')}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    out_file = out_dir / f"{run_id}.json"
    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"[SAVE] results -> {out_file}")

    # log manifest entry
    manifest_entry = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "model": model_name,
        "dataset": dataset_name,
        "condition": condition,
        "temperature": temp,
        "seed": seed,
        "n_samples": len(results),
        "runtime_seconds": runtime,
        "nodes": os.getenv("HOSTNAME", "local"),
    }
    log_manifest(manifest_entry)
    print("[DONE]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--temp", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--condition", type=str, default="B0")
    parser.add_argument("--aethon-epsilon", type=float, default=1.2)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--openai-model-override", type=str, default=None, help="If you want to call a specific OpenAI model id")
    args = parser.parse_args()

    run_experiment(args.model, args.dataset, temp=args.temp, seed=args.seed, condition=args.condition,
                   aethon_epsilon=args.aethon_epsilon, limit=args.limit, dry_run=args.dry_run,
                   openai_model_override=args.openai_model_override)


