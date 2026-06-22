#!/usr/bin/env python3
"""
test_model_loading.py

Verifica automaticamente os drivers registrados em model_registry.py:
- tenta instanciar cada driver
- faz uma inferência curta (com prompt de teste)
- registra status (loaded / not_loaded / infer_error)
- evita chamadas reais ao OpenAI por padrão (use --allow-openai para habilitar)

Uso:
    python src/test_model_loading.py [--allow-openai]

Saída:
    results/model_load_check.json (lista com status por model)
"""
import argparse
import json
import time
from pathlib import Path

from model_registry import MODEL_REGISTRY, get_model_driver, normalize_model_name

TEST_PROMPT = "Please summarize in one sentence: The quick brown fox jumps over the lazy dog."

OUT = Path(__file__).resolve().parents[1] / "results" / "model_load_check.json"

def is_remote_api_model(key: str) -> bool:
    return key.startswith("gpt") or key.startswith("deepseek")

def main(allow_openai=False, model=None, timeout_per_model=60):
    summary = []
    registry_items = MODEL_REGISTRY.items()
    if model:
        key = normalize_model_name(model)
        if key not in MODEL_REGISTRY:
            raise ValueError(f"Model '{model}' not registered. Available: {list(MODEL_REGISTRY.keys())}")
        registry_items = [(key, MODEL_REGISTRY[key])]

    for key, _ in registry_items:
        entry = {"model_key": key, "status": "unknown", "note": "", "time_s": None}
        start = time.time()
        try:
            # For API drivers, skip infer unless allow_openai True
            if is_remote_api_model(key) and not allow_openai:
                entry["status"] = "api_skipped"
                entry["note"] = "Use --allow-api to run live API inference."
                entry["time_s"] = time.time() - start
                summary.append(entry)
                continue

            # instantiate driver
            inst = get_model_driver(key)
            # basic check: does driver have infer method?
            if not hasattr(inst, "infer"):
                entry["status"] = "no_infer_method"
                entry["note"] = "driver missing infer()"
                entry["time_s"] = time.time() - start
                summary.append(entry)
                continue

            # attempt inference (timed)
            try:
                t0 = time.time()
                out = inst.infer(TEST_PROMPT, max_tokens=32, temperature=0.0)
                t1 = time.time()
                out_text = str(out)
                if out_text.startswith("[MODEL_NOT_LOADED]"):
                    entry["status"] = "not_loaded"
                    entry["note"] = out_text
                elif out_text.startswith("[OPENAI_ERROR]") or out_text.startswith("[DEEPSEEK_ERROR]") or out_text.startswith("[INFER_ERROR]"):
                    entry["status"] = "infer_error"
                    entry["note"] = out_text
                else:
                    entry["status"] = "ok"
                    entry["note"] = f"infer_ok len={len(out_text)}"
                entry["time_s"] = t1 - t0
            except Exception as ie:
                entry["status"] = "infer_error"
                entry["note"] = str(ie)
                entry["time_s"] = time.time() - start

        except Exception as e:
            entry["status"] = "init_error"
            entry["note"] = str(e)
            entry["time_s"] = time.time() - start

        summary.append(entry)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"[DONE] wrote {OUT}")
    for s in summary:
        print(s)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--allow-openai", action="store_true", help="Enable remote API inference tests (consumes tokens).")
    p.add_argument("--allow-api", action="store_true", help="Alias for --allow-openai.")
    p.add_argument("--model", type=str, default=None, help="Only test one registered model.")
    args = p.parse_args()
    main(allow_openai=args.allow_openai or args.allow_api, model=args.model)
