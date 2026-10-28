"""Pinned, offline-by-default modern detector runner with validated resume."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
import time
from pathlib import Path

import pandas as pd
from huggingface_hub import snapshot_download

from baseline_detectors import TransformerDetector
from baseline_reliability import atomic_write, append_checkpoint, fingerprint, load_checkpoint
from benchmark.detection import EVALUATION_DATASETS, LABEL_PROVENANCE
from dataset_loader import get_dataset_metadata, load_dataset
from research_integrity import implementation_hashes

MODELS = {"protectai": ("protectai/deberta-v3-base-prompt-injection-v2", ("INJECTION",)),
          "promptguard": ("meta-llama/Llama-Prompt-Guard-2-22M", ("MALICIOUS",))}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=MODELS, default="protectai")
    p.add_argument("--revision", required=True, help="Immutable 40-character model/tokenizer commit")
    p.add_argument("--run-id", required=True); p.add_argument("--output", default="results/research_2026/baselines")
    p.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    p.add_argument("--batch-size", type=int, default=4); p.add_argument("--smoke", action="store_true")
    p.add_argument("--threshold", type=float, default=.5)
    p.add_argument("--allow-download", action="store_true"); p.add_argument("--resume", action="store_true")
    a = p.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", a.revision) or a.batch_size < 1 or not 0 <= a.threshold <= 1:
        p.error("Require immutable revision, positive batch size and threshold in [0,1]")
    started = time.perf_counter(); model_id, labels = MODELS[a.model]
    output = Path(a.output)/a.run_id; manifest_path = output/"manifest.json"
    data_metadata = [get_dataset_metadata(n) for n in EVALUATION_DATASETS]
    cfg = {"model": model_id, "model_revision": a.revision, "tokenizer_revision": a.revision,
           "datasets": data_metadata, "threshold": a.threshold, "max_length": 512,
           "smoke": a.smoke, "dtype": "float32", "labels": labels,
           "device": a.device, "batch_size": a.batch_size, "decision": "p(malicious) >= threshold",
           "implementation": implementation_hashes(__file__, Path(__file__).with_name("baseline_detectors.py")),
           "dependencies": {p: importlib.metadata.version(p) for p in ("torch", "transformers", "numpy", "pandas")}}
    # Unlike the legacy fingerprint, preserve device/batch to keep timing comparisons coherent.
    fp = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
    manifest = {"run_id": a.run_id, "fingerprint": fp, "configuration": cfg,
                "commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True)),
                "python": platform.python_version(), "hardware": platform.uname()._asdict(),
                "dependencies": {p: importlib.metadata.version(p) for p in ("torch", "transformers", "numpy", "pandas")},
                "seed": 2026, "temperature": None, "token_limit": 512, "status": "CREATED",
                "warmup": 2, "checkpoint": "checkpoint.jsonl", "errors": [], "exclusions": []}
    if manifest_path.exists():
        if not a.resume: raise ValueError("Existing run; use --resume")
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        if previous["fingerprint"] != fp: raise ValueError("Incompatible scientific/timing fingerprint")
        resume_environment = {"commit_sha": manifest["commit_sha"], "hardware": manifest["hardware"], "python": manifest["python"]}
        manifest = previous.copy()
        manifest.setdefault("resume_events", []).append(resume_environment)
    elif a.resume:
        raise ValueError("Resume requires existing manifest")
    frames = []
    for name in EVALUATION_DATASETS:
        f = load_dataset(name).copy()
        if a.smoke: f = f.groupby("label", group_keys=False).head(2)
        f["dataset"] = name; frames.append(f)
    data = pd.concat(frames, ignore_index=True)
    data["prompt_sha256"] = data.prompt_text.map(lambda t: hashlib.sha256(str(t).encode()).hexdigest())
    expected = {(r.dataset, str(r.prompt_id), r.prompt_sha256, model_id) for r in data.itertuples()}
    if len(expected) != len(data): raise ValueError("Duplicate source identities")
    ck = output/"checkpoint.jsonl"; done = load_checkpoint(ck)
    if not set(done) <= expected: raise ValueError("Foreign checkpoint rows")
    truth = {(r.dataset, str(r.prompt_id), r.prompt_sha256, model_id): int(r.label) for r in data.itertuples()}
    if any(r["true_label"] != truth[k] for k, r in done.items()): raise ValueError("Checkpoint label mismatch")
    manifest.update(expected_records=len(data), processed_records=len(done))
    atomic_write(manifest_path, json.dumps(manifest, indent=2))
    try:
        if len(done) < len(expected):
            try:
                snapshot = Path(snapshot_download(model_id, revision=a.revision, local_files_only=not a.allow_download))
            except Exception as exc:
                manifest.update(status="NOT_RUN", reason=f"Pinned weights unavailable: {type(exc).__name__}: {exc}")
                atomic_write(manifest_path, json.dumps(manifest, indent=2)); print(json.dumps(manifest, indent=2)); return
            model_files = list(snapshot.glob("*.safetensors")) + list(snapshot.glob("*.bin"))
            if not model_files: raise ValueError("Pinned snapshot has no local model weights")
            hashes = {}
            tokenizer_files = [p for p in snapshot.iterdir() if p.is_file() and (p.name.startswith("tokenizer") or p.name in {"special_tokens_map.json", "spm.model", "sentencepiece.bpe.model"})]
            for path in model_files + [snapshot/"config.json"] + tokenizer_files:
                h = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024*1024), b""): h.update(chunk)
                hashes[path.name] = h.hexdigest()
            detector = TransformerDetector(model_id, labels, device=a.device, revision=a.revision, local_files_only=True)
            resolved = getattr(detector.model.config, "_commit_hash", None)
            if resolved != a.revision: raise ValueError("Resolved model revision does not match pinned revision")
            if a.model == "protectai" and detector.model.config.id2label != {0: "SAFE", 1: "INJECTION"}:
                raise ValueError("ProtectAI class semantics changed")
            detector.warmup(["ordinary benign request", "simple text"])
            manifest.update(status="RUNNING", model_hashes=hashes,
                            resolved_model_revision=getattr(detector.model.config, "_commit_hash", None),
                            id2label=detector.model.config.id2label,
                            gpu_name=__import__("torch").cuda.get_device_name() if a.device == "cuda" else None)
            atomic_write(manifest_path, json.dumps(manifest, indent=2))
            pending = [r for r in data.itertuples() if (r.dataset, str(r.prompt_id), r.prompt_sha256, model_id) not in done]
            for start in range(0, len(pending), a.batch_size):
                batch = pending[start:start+a.batch_size]
                prompts = [str(r.prompt_text) for r in batch]
                # Actual lengths before truncation; do not mistake exactly-512 for truncated.
                lengths = [len(detector.tokenizer(t, truncation=False)["input_ids"]) for t in prompts]
                if a.device == "cuda": __import__("torch").cuda.synchronize()
                before = time.perf_counter(); values = detector.predict_batch(prompts)
                if a.device == "cuda": __import__("torch").cuda.synchronize()
                elapsed = (time.perf_counter()-before)*1000
                if len(values) != len(batch): raise ValueError("Incomplete batch output")
                records = [{"dataset": r.dataset, "prompt_id": str(r.prompt_id), "prompt_sha256": r.prompt_sha256,
                            "detector": model_id, "true_label": int(r.label), "label_provenance": LABEL_PROVENANCE[r.dataset],
                            "score": float(v[0]), "prediction": int(v[0] >= a.threshold),
                            "original_token_count": length, "truncated": length > 512,
                            "batch_latency_ms": elapsed, "actual_batch_size": len(batch)}
                           for r, v, length in zip(batch, values, lengths)]
                append_checkpoint(ck, records)
                manifest["processed_records"] += len(records)
                atomic_write(manifest_path, json.dumps(manifest, indent=2))
        done = load_checkpoint(ck)
        if set(done) != expected: raise ValueError("Final checkpoint incomplete")
        serialized = pd.DataFrame(done.values()).to_csv(index=False)
        actual_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        if manifest.get("predictions_sha256") and actual_hash != manifest["predictions_sha256"]:
            raise ValueError("Completed checkpoint content differs from frozen prediction hash")
        atomic_write(output/"predictions.csv", serialized)
        manifest.update(status="DONE", processed_records=len(done), duration_seconds=manifest.get("duration_seconds", 0)+(time.perf_counter()-started),
                        predictions_sha256=hashlib.sha256((output/"predictions.csv").read_bytes()).hexdigest())
        atomic_write(manifest_path, json.dumps(manifest, indent=2))
    except (Exception, KeyboardInterrupt) as exc:
        manifest.update(status="PARTIAL" if isinstance(exc, KeyboardInterrupt) else "FAILED",
                        duration_seconds=time.perf_counter()-started, errors=[f"{type(exc).__name__}: {exc}"])
        atomic_write(manifest_path, json.dumps(manifest, indent=2)); raise


if __name__ == "__main__": main()
