"""Copy an explicit allowlist of text-free 2026 evidence for academic review."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil


def main():
    p = argparse.ArgumentParser(); p.add_argument("--root", default="results/research_2026")
    p.add_argument("--output", default="docs/research_2026_evidence"); a = p.parse_args()
    root, output = Path(a.root), Path(a.output)
    runs = {
        "integrity": (root/"integrity/integrity-final-2026-10-28", ["summary.json", "summary.md", "summary.tex"]),
        "nested": (root/"generalization/nested-final-2026-10-28", ["summary.json", "summary.md", "summary.tex", "outer_predictions.csv", "fold_metrics.csv", "frozen_selection.json", "reliability.csv", "curves.csv", "diagnostic_curves.svg"]),
        "dp": (root/"dp/dp-final-2026-10-28", ["utility.csv", "utility.json", "utility.md", "utility.tex"]),
        "protectai_smoke": (root/"baselines/protectai-validated-smoke-2026-10-28", ["predictions.csv"]),
        "promptguard": (root/"baselines/promptguard-offline-smoke-2026-10-28", [])}
    index = []
    for name, (source, names) in runs.items():
        manifest = json.loads((source/"manifest.json").read_text(encoding="utf-8"))
        if manifest["status"] not in {"DONE", "NOT_RUN"}: raise ValueError(f"Incomplete run {source}")
        for file in ["manifest.json", *names]:
            raw = (source/file).read_bytes()
            expected = manifest.get("artifact_hashes", {}).get(file)
            actual = hashlib.sha256(raw).hexdigest()
            if expected and actual != expected: raise ValueError(f"Invalid hash {source/file}")
            destination = output/name/file
            if destination.exists() and destination.read_bytes() != raw:
                raise ValueError(f"Refusing to replace existing evidence {destination}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists(): shutil.copyfile(source/file, destination)
            index.append({"run_id": manifest["run_id"], "status": manifest["status"], "artifact": str(destination.relative_to(output)), "sha256": actual})
    output.mkdir(parents=True, exist_ok=True)
    extra_files = [(root/"baselines/protectai-consistency.json", output/"protectai_smoke/consistency.json"),
                   (root/"dp/historical-b3-b4-equivalence.json", output/"dp/historical-b3-b4-equivalence.json")]
    extra_files.extend((root/"paired/historical-b3-protectai-validated-smoke"/n, output/"paired_smoke"/n)
                       for n in ("comparison.json", "comparison.csv", "comparison.tex", "comparison.md"))
    for source, destination in extra_files:
        raw = source.read_bytes()
        if destination.exists() and destination.read_bytes() != raw: raise ValueError("Existing extra evidence differs")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists(): shutil.copyfile(source, destination)
        index.append({"artifact": str(destination.relative_to(output)), "sha256": hashlib.sha256(raw).hexdigest()})
    (output/"index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    versions = sorted({f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions() if d.metadata.get("Name")}, key=str.lower)
    (output/"local-environment.txt").write_text("# Observed Windows environment inventory; not a GPU installation lock\n"+"\n".join(versions)+"\n", encoding="utf-8")
    print(f"Exported {len(index)} allowlisted artifacts; no raw prompts, responses or model weights")


if __name__ == "__main__": main()
