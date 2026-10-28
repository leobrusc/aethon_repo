"""Local Monte Carlo utility study of sensitivity-bounded Laplace counters.

Synthetic draws assess the noise mechanism, not a privacy audit of stored text.
"""
import argparse
import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path
import numpy as np
import pandas as pd
from baseline_reliability import atomic_write


def utility(epsilon, *, count=100, sensitivity=1, draws=10000, seed=2026, releases=1):
    if epsilon <= 0 or not np.isfinite(epsilon) or sensitivity <= 0 or draws < 2 or count < 0 or releases < 1:
        raise ValueError("Invalid privacy/noise simulation parameters")
    rng = np.random.default_rng(seed)
    # Warmup is measured separately and excluded from recorded timing.
    for _ in range(100): rng.laplace(0, sensitivity/epsilon)
    noise, latency = [], []
    for _ in range(draws):
        before = time.perf_counter_ns()
        value = rng.laplace(0, sensitivity/epsilon)
        latency.append((time.perf_counter_ns()-before)/1e6)
        noise.append(value)
    noise = np.asarray(noise)
    return {"epsilon_per_release": epsilon, "sensitivity": sensitivity, "synthetic_count": count,
            "draws": draws, "seed": seed, "warmup": 100, "releases": releases,
            "basic_composition_epsilon": releases*epsilon,
            "mean_absolute_error": float(np.abs(noise).mean()),
            "mean_relative_error": float(np.abs(noise).mean()/count) if count else None,
            "empirical_bias": float(noise.mean()), "empirical_variance": float(noise.var(ddof=1)),
            "theoretical_variance": 2*(sensitivity/epsilon)**2,
            "audit_draw_p50_ms": float(np.quantile(latency, .5)),
            "audit_draw_p95_ms": float(np.quantile(latency, .95)),
            "audit_draw_p99_ms": float(np.quantile(latency, .99)),
            "privacy_scope": "bounded counter releases only; not raw text or per-record identity"}


def main():
    p = argparse.ArgumentParser(); p.add_argument("--run-id", required=True)
    p.add_argument("--output", default="results/research_2026/dp"); p.add_argument("--draws", type=int, default=10000)
    p.add_argument("--seed", type=int, default=2026); a = p.parse_args()
    output = Path(a.output)/a.run_id
    configuration = {"draws": a.draws, "seed": a.seed, "epsilon": [.5, 1.2, 2.5],
                     "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "numpy": np.__version__}
    fp = hashlib.sha256(json.dumps(configuration, sort_keys=True).encode()).hexdigest()
    manifest_path = output/"manifest.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        if old.get("fingerprint") != fp: raise ValueError("Existing timing study has different parameters or implementation")
        if old["status"] == "DONE":
            for name, sha in old["artifact_hashes"].items():
                if hashlib.sha256((output/name).read_bytes()).hexdigest() != sha: raise ValueError("Artifact hash mismatch")
            print(json.dumps(old, indent=2)); return
    atomic_write(manifest_path, json.dumps({"run_id": a.run_id, "status": "RUNNING", "configuration": configuration,
                                            "fingerprint": fp, "checkpoint": "restart deterministic simulation on interruption"}, indent=2))
    started = time.perf_counter()
    rows = [utility(e, draws=a.draws, seed=a.seed) for e in (.5, 1.2, 2.5)]
    f = pd.DataFrame(rows)
    for name, value in (("utility.csv", f.to_csv(index=False)), ("utility.json", json.dumps(rows, indent=2)),
                        ("utility.tex", f.to_latex(index=False)), ("utility.md", "# Synthetic DP utility\n\n"+f.to_string(index=False))):
        atomic_write(output/name, value)
    atomic_write(output/"manifest.json", json.dumps({"run_id": a.run_id, "status": "DONE", "fingerprint": fp, "configuration": configuration,
        "artifact_hashes": {n: hashlib.sha256((output/n).read_bytes()).hexdigest() for n in ("utility.csv", "utility.json", "utility.tex", "utility.md")},
        "experiment": "synthetic noise Monte Carlo, no model inference or private dataset",
        "commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True)),
        "hardware": platform.uname()._asdict(), "python": platform.python_version(), "numpy": np.__version__,
        "duration_seconds": time.perf_counter()-started, "expected_records": 3*a.draws,
        "processed_records": 3*a.draws, "batch_size": 1, "warmup_per_epsilon": 100,
        "seed": a.seed, "checkpoint": "whole deterministic restart with a new timing run ID",
        "adjacency": "add/remove one event; contribution bounded by one per released counter",
        "production_dp_claim": False, "model": None, "dataset": None, "threshold": None,
        "temperature": None, "token_limit": None, "errors": [], "exclusions": []}, indent=2))
    print(f.to_string(index=False))


if __name__ == "__main__": main()
