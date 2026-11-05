"""Tooling smoke: pair cached historical B3 decisions with ProtectAI's 18 rows."""
import hashlib
import json
from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from baseline_reliability import atomic_write
from research_paired import KEYS, compare


def main():
    baseline_path = Path("results/research_2026/baselines/protectai-validated-smoke-2026-10-28/predictions.csv")
    historical_path = Path("results/revision/detection/per_prompt_results.csv")
    output = Path("results/research_2026/paired/historical-b3-protectai-validated-smoke")
    if output.exists(): raise ValueError("Existing paired smoke artifacts; choose an explicit new comparison")
    baseline = pd.read_csv(baseline_path, dtype={"prompt_id": str})
    historical = pd.read_csv(historical_path, dtype={"prompt_id": str})
    historical = historical[historical.condition == "B3"].rename(columns={"final_prediction": "prediction"})
    first = historical.merge(baseline[KEYS], on=KEYS, validate="one_to_one")
    result = compare(first, baseline, iterations=200)
    result.update(smoke_only=True, note="No confirmatory significance claim; reused historical B3 predictions on the exact baseline smoke rows",
                  provenance={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (baseline_path, historical_path)})
    atomic_write(output/"comparison.json", json.dumps(result, indent=2))
    frame = pd.json_normalize(result)
    atomic_write(output/"comparison.csv", frame.to_csv(index=False))
    atomic_write(output/"comparison.tex", frame.to_latex(index=False))
    atomic_write(output/"comparison.md", "# Exploratory paired tooling smoke\n\n"+json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
