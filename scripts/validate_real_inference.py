"""Bounded offline inference of reviewed cached models; never a benchmark/ASR run.

Registry mode exercises the unchanged actual AETHON driver on raw inputs plus a
native chat-template control. Native mode supports explicit memory-saving dtype.
No mocked models, remote code, pickle weights, downloads or silent substitutions.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
REVIEWED = {
    "llama-3.2-1b-instruct": ("meta-llama/Llama-3.2-1B-Instruct", "9213176726f574b556790deb65791e0c5aa438b6", "llama"),
    "qwen2.5-3b-instruct": ("Qwen/Qwen2.5-3B-Instruct", "aa8e72537993ba99e69dfaafa59ed015b17504d1", "qwen2"),
}


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def review_snapshot(path, key):
    repo, revision, model_type = REVIEWED[key]
    if path.name != revision or not re.fullmatch("[0-9a-f]{40}", path.name):
        raise ValueError("Require the reviewed exact cached revision")
    config = json.loads((path / "config.json").read_text(encoding="utf-8"))
    tokenizer = json.loads((path / "tokenizer_config.json").read_text(encoding="utf-8"))
    if config.get("model_type") != model_type or config.get("auto_map") or tokenizer.get("auto_map"):
        raise ValueError("Unreviewed/custom model or tokenizer code")
    files = [p for p in path.rglob("*") if p.is_file()]
    if any(p.suffix in {".py", ".bin", ".pkl", ".pt", ".pth"} for p in files):
        raise ValueError("Remote code/pickle-like weights are outside this protocol")
    weights = [p for p in files if p.suffix == ".safetensors"]
    if not weights:
        raise FileNotFoundError("Local safetensors weights unavailable")
    index = path / "model.safetensors.index.json"
    if index.exists():
        names = set(json.loads(index.read_text(encoding="utf-8"))["weight_map"].values())
        if any(Path(name).name != name or not name.endswith(".safetensors") or not (path / name).is_file() for name in names):
            raise ValueError("Invalid/missing shard path")
    cache_model_root = path.parents[1].resolve()
    for p in files:
        if not p.resolve().is_relative_to(cache_model_root):
            raise ValueError("Snapshot link escapes its model cache")
    return {"model_id": repo, "revision": revision, "model_type": model_type,
            "review": "Native Transformers architecture, static tokenizer/config, safetensors only; hashes establish identity, not safety",
            "artifacts": {p.relative_to(path).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(files)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=REVIEWED, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--mode", choices=["registry", "native"], default="registry")
    parser.add_argument("--dtype", choices=["float32", "bfloat16"], default="float32")
    parser.add_argument("--environment", choices=["maintained", "historical"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "registry" and args.dtype != "float32":
        parser.error("Unchanged CPU registry driver uses float32")
    # Applied before importing HF libraries; authorization checks happen separately.
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                      HF_HUB_DISABLE_IMPLICIT_TOKEN="1", TOKENIZERS_PARALLELISM="false")
    protocol_path = ROOT / "tests/fixtures/readiness_smoke.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {"status": "NOT_RUN", "real_inference": False, "environment": args.environment,
              "started_utc": datetime.now(timezone.utc).isoformat(), "mode": args.mode,
              "protocol_sha256": sha(protocol_path), "script_sha256": sha(Path(__file__)),
              "seed": protocol["seed"], "device": "cpu", "dtype_requested": args.dtype,
              "generation": {k: protocol[k] for k in ["max_new_tokens", "do_sample", "temperature", "cpu_threads", "interop_threads"]},
              "python": platform.python_version(), "platform": platform.platform(),
              "versions": {p: importlib.metadata.version(p) for p in ["torch", "transformers", "tokenizers", "safetensors"]},
              "records": [], "asr": "NOT_RUN", "scientific_performance_estimate": False}
    def save():
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    save()
    try:
        report.update(review_snapshot(args.snapshot.resolve(), args.model))
        report["stage"] = "HASHED_REVIEWED_SNAPSHOT"
        save()
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.set_num_threads(protocol["cpu_threads"])
        torch.set_num_interop_threads(protocol["interop_threads"])
        torch.manual_seed(protocol["seed"])
        torch.use_deterministic_algorithms(True)
        started = time.perf_counter()
        if args.mode == "registry":
            from model_registry import get_model_driver
            driver = get_model_driver(args.model, model_id=str(args.snapshot.resolve()), device="cpu")
            if not driver.available:
                raise RuntimeError("Actual registry driver failed to load")
            model, tokenizer = driver.model, driver.tokenizer
        else:
            tokenizer = AutoTokenizer.from_pretrained(args.snapshot, local_files_only=True, trust_remote_code=False)
            model = AutoModelForCausalLM.from_pretrained(args.snapshot, local_files_only=True,
                        trust_remote_code=False, use_safetensors=True, torch_dtype=getattr(torch, args.dtype)).eval()
        report.update(load_seconds=time.perf_counter()-started, parameter_count=sum(p.numel() for p in model.parameters()),
                      dtype_observed=str(next(model.parameters()).dtype), cuda_available=torch.cuda.is_available(),
                      special_tokens={"bos_id": tokenizer.bos_token_id, "eos_id": tokenizer.eos_token_id,
                                      "pad_id": tokenizer.pad_token_id, "map": tokenizer.special_tokens_map},
                      chat_template_sha256=hashlib.sha256((tokenizer.chat_template or "").encode()).hexdigest(), stage="LOADED")
        if not tokenizer.chat_template:
            raise ValueError("Required chat template missing")
        save()
        # Instrumentation calls the original real generate unchanged and records
        # actual generated IDs. It never replaces inference with a stub.
        generated = []
        original_generate = model.generate
        def observed_generate(*a, **kw):
            output = original_generate(*a, **kw)
            sequences = output.sequences if hasattr(output, "sequences") else output
            inputs = kw.get("input_ids", a[0] if a else None)
            generated.append({"input_ids": inputs[0].detach().cpu().tolist(),
                              "output_ids": sequences[0].detach().cpu().tolist()})
            return output
        model.generate = observed_generate
        for row in protocol["inputs"]:
            messages = [{"role": "system", "content": protocol["system"]}, {"role": "user", "content": row["text"]}]
            rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            template_ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
            if template_ids != tokenizer(rendered, add_special_tokens=False)["input_ids"]:
                raise ValueError("Chat-template tokenization contract differs")
            mode = "registry_raw" if args.mode == "registry" else "native_chat"
            started = time.perf_counter()
            if args.mode == "registry":
                text = driver.infer(row["text"], max_tokens=protocol["max_new_tokens"], temperature=0.0)
            else:
                inputs = tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
                with torch.inference_mode():
                    outputs = model.generate(**inputs, max_new_tokens=protocol["max_new_tokens"], do_sample=False,
                                             pad_token_id=tokenizer.eos_token_id)
                text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            elapsed = time.perf_counter()-started
            tokens = generated[-1]
            continuation = tokens["output_ids"][len(tokens["input_ids"]):]
            if not isinstance(text, str) or not text.strip() or text.startswith(("[MODEL_NOT_LOADED]", "[INFER_ERROR]")) or not 0 < len(continuation) <= protocol["max_new_tokens"]:
                raise ValueError("Real inference violated the output contract")
            report["records"].append({"id": row["id"], "mode": mode, "text": text,
                                      "input_token_ids": tokens["input_ids"], "generated_token_ids": continuation,
                                      "template_token_ids": template_ids, "elapsed_seconds": elapsed,
                                      "contract_status": "PASS"})
            report["real_inference"] = True
            save()
        if args.mode == "registry":
            # Independently execute a correctly tokenized chat template on the
            # same loaded model; the legacy raw driver is not silently changed.
            row = protocol["inputs"][0]
            messages = [{"role": "system", "content": protocol["system"]}, {"role": "user", "content": row["text"]}]
            rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
            with torch.inference_mode():
                outputs = model.generate(**inputs, max_new_tokens=protocol["max_new_tokens"], do_sample=False, pad_token_id=tokenizer.eos_token_id)
            continuation = outputs[0][inputs.input_ids.shape[1]:].tolist()
            text = tokenizer.decode(continuation, skip_special_tokens=True)
            if not text.strip() or not 0 < len(continuation) <= protocol["max_new_tokens"]:
                raise ValueError("Native chat control failed")
            report["chat_control"] = {"status": "PASS", "id": row["id"], "text": text, "generated_token_ids": continuation}
        report.update(status="PASS", stage="COMPLETE", completed_utc=datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        report.update(status="FAIL", error_type=type(exc).__name__, error=str(exc))
    save()
    print(json.dumps({"status": report["status"], "stage": report.get("stage"), "records": len(report["records"]), "output": str(args.output)}))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
