"""Reanalyze B3/B4 identity without rerunning detectors or altering history."""
import hashlib
import json
from pathlib import Path
import sys
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from baseline_reliability import atomic_write


def main():
    source = Path("results/revision/detection/per_prompt_results.csv")
    frame = pd.read_csv(source, dtype={"prompt_id": str})
    keys = ["dataset", "prompt_id", "prompt_sha256"]
    a, b = [frame[frame.condition == condition] for condition in ("B3", "B4")]
    paired = a.merge(b, on=keys, how="outer", validate="one_to_one", indicator=True)
    assert len(paired) and (paired._merge == "both").all(), "Unpaired historical decisions"
    assert (paired.true_label_x == paired.true_label_y).all(), "Truth mismatch"
    mismatches = int((paired.final_prediction_x != paired.final_prediction_y).sum())
    assert mismatches == 0, "B3/B4 historical decisions differ"
    result = {"status": "DONE", "historical_reanalysis": True, "new_detector_inference": False,
              "n_paired": len(paired), "decision_mismatches": mismatches,
              "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    destination = Path("results/research_2026/dp/historical-b3-b4-equivalence.json")
    atomic_write(destination, json.dumps(result, indent=2)); print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
