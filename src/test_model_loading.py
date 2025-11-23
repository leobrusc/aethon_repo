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

from model_registry import MODEL_REGISTRY, get_model_driver

TEST_PROMPT = "Please summarize in one sentence: The quick brown fox jumps over the lazy dog."

OUT = Path("/home/leonardo/Documentos/aethon_repo/results/model_load_check.json")

def main(allow_openai=False, timeout_per_model=60):
    summary = []
    for key, Driver in MODEL_REGISTRY.items():
        entry = {"model_key": key, "status": "unknown", "note": "", "time_s": None}
        start = time.time()
        try:
            # For OpenAI drivers, skip infer unless allow_openai True
            if key.startswith("gpt") and not allow_openai:
                try:
                    inst = Driver() if key != "gpt-4o-mini" else Driver(model_name=key)
                    entry["status"] = "loaded (openai - inference skipped)"
                except Exception as e:
                    entry["status"] = "init_error"
                    entry["note"] = str(e)
                entry["time_s"] = time.time() - start
                summary.append(entry)
                continue

            # instantiate driver
            inst = Driver() if key != "gpt-4o-mini" else Driver(model_name=key)
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
                entry["status"] = "ok"
                entry["note"] = f"infer_ok len={len(str(out))}"
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
    p.add_argument("--allow-openai", action="store_true", help="Enable OpenAI inference tests (consumes tokens).")
    args = p.parse_args()
    main(allow_openai=args.allow_openai)
