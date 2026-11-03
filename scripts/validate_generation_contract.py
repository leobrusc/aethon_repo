"""Bounded real offline generation.v1 validation; not a benchmark or ASR study."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import sys
import time

from validate_real_inference import ROOT, REVIEWED, review_snapshot, sha

sys.path.insert(0, str(ROOT / "src"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=REVIEWED, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--dtype", choices=["float32", "bfloat16"], required=True)
    parser.add_argument("--environment", choices=["historical", "maintained"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Preserve existing evidence; select a new output path")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                      HF_HUB_DISABLE_IMPLICIT_TOKEN="1", TOKENIZERS_PARALLELISM="false")
    fixture = ROOT / "tests/fixtures/readiness_smoke.json"
    protocol = json.loads(fixture.read_text(encoding="utf-8"))
    report = {"status": "NOT_RUN", "real_inference": False, "environment": args.environment,
              "started_utc": datetime.now(timezone.utc).isoformat(), "dtype_requested": args.dtype,
              "python": platform.python_version(), "platform": platform.platform(), "device": "cpu",
              "seed": protocol["seed"], "threads": protocol["cpu_threads"],
              "fixture_sha256": sha(fixture), "script_sha256": sha(Path(__file__)),
              "implementation_sha256": sha(ROOT / "src/aethon/generation.py"),
              "records": [], "scientific_performance_estimate": False, "asr_study": "NOT_RUN"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def save():
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    save()
    try:
        report.update(review_snapshot(args.snapshot.resolve(), args.model))
        import torch
        from model_registry import get_model_driver
        from aethon.generation import GenerationResult, evaluation_response
        torch.set_num_threads(protocol["cpu_threads"])
        torch.set_num_interop_threads(protocol["interop_threads"])
        torch.manual_seed(protocol["seed"])
        torch.use_deterministic_algorithms(True)
        started = time.perf_counter()
        driver = get_model_driver(args.model, model_id=str(args.snapshot.resolve()), device="cpu",
                                  precision=args.dtype, revision=report["revision"])
        report.update(load_seconds=time.perf_counter()-started, parameter_count=sum(p.numel() for p in driver.model.parameters()),
                      precision_loaded=driver.observation, cuda_available=torch.cuda.is_available())
        for row in protocol["inputs"]:
            messages = [{"role": "system", "content": protocol["system"]}, {"role": "user", "content": row["text"]}]
            started = time.perf_counter()
            result = driver.generate_result(row["text"], max_tokens=protocol["max_new_tokens"], temperature=0, messages=messages)
            if not result.generated_ids or len(result.generated_ids) > protocol["max_new_tokens"]:
                raise ValueError("Invalid generated-token count")
            if GenerationResult.from_json(result.to_json()) != result:
                raise ValueError("Serialization roundtrip changed output")
            report["records"].append({"id": row["id"], "status": "PASS", "elapsed_seconds": time.perf_counter()-started,
                                      "result": result.to_dict()})
            report["real_inference"] = True
            save()
        # Exercise actual evaluation routing and legacy .infer (two additional
        # real raw-prompt calls). Raw EOS-only continuation is valid empty output.
        row = protocol["inputs"][0]
        response = evaluation_response(driver, row["text"], max_tokens=protocol["max_new_tokens"], temperature=0)
        legacy = driver.infer(row["text"], max_tokens=protocol["max_new_tokens"], temperature=0)
        report["raw_interface_checks"] = {"status": "PASS", "continuation": response, "legacy_full_text": legacy,
                                          "real_calls": 2, "scope": "Deterministic same-process raw prompt; legacy string retained separately"}
        report.update(status="PASS", completed_utc=datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        report.update(status="FAIL", error_type=type(exc).__name__, error=str(exc))
    save()
    print(json.dumps({"status": report["status"], "real_inference": report["real_inference"], "records": len(report["records"]), "output": str(args.output)}))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
