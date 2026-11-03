"""Record tracked-file decisions, static imports and scientific byte integrity.

Run snapshot BEFORE cleanup; verify never updates the baseline.
LFS files are hashed after hydration, not as pointer text.
"""
import argparse
import ast
import csv
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/modernization"


def tracked():
    return subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT
    ).decode().strip("\0").split("\0")


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def git_digest(revision, name):
    raw = subprocess.check_output(["git", "show", f"{revision}:{name}"], cwd=ROOT)
    if raw.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        return raw.decode().split("oid sha256:")[1].splitlines()[0]
    return hashlib.sha256(raw).hexdigest()


def scientific(name):
    return name.startswith(("datasets/", "results/", "configs/", "src/models/",
                            "docs/research_2026_evidence/")) or name == "experiment_manifest.json"


def classify(name):
    if name in {"json", "pd", ".Rhistory"}:
        assert (ROOT / name).stat().st_size == 0
        return "REMOVE", "Empty scratch/session file; no content or executable behavior"
    if name in {"INVENTORY_REPORT.md", "GITHUB_CLEANUP_PLAN.md"}:
        return "ARCHIVE", "Dated June inventory/plan; superseded by audited modernization report"
    if name.startswith("src/"):
        return "REFACTOR", "Keep legacy imports, dynamic registry, CLI and pickle module paths compatible"
    if scientific(name) or name.startswith("tests/"):
        return "KEEP", "Scientific input/configuration/evidence or regression coverage"
    if name in {"CLOUD_EXECUTION_PLAN.md", "experiment_plan.md", "expected_runtime_estimates.md", "EXPERIMENT_FLOW.md"}:
        return "REVIEW", "Historical operational plan; external scientific use not disproven"
    return "KEEP", "Documentation or operation; no evidence authorizing deletion"


def snapshot():
    REPORT.mkdir(parents=True, exist_ok=True)
    target = REPORT / "scientific-integrity.json"
    if target.exists():
        raise SystemExit("Baseline already exists; refusing overwrite")
    names = tracked()
    records = {name: {"sha256": digest(ROOT / name), "bytes": (ROOT / name).stat().st_size,
                      "git_sha256": git_digest("HEAD", name)}
               for name in names if scientific(name)}
    target.write_text(json.dumps({"base_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "files": records}, indent=2) + "\n", encoding="utf-8")
    with (REPORT / "file-decisions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["path", "classification", "evidence", "sha256", "bytes"])
        for name in names:
            writer.writerow([name, *classify(name), digest(ROOT / name), (ROOT / name).stat().st_size])
    imports = {}
    for name in names:
        if name.endswith(".py"):
            tree = ast.parse((ROOT / name).read_text(encoding="utf-8-sig"))
            imports[name] = sorted({node.module or "<relative>" for node in ast.walk(tree)
                                    if isinstance(node, ast.ImportFrom)} |
                                   {alias.name for node in ast.walk(tree)
                                    if isinstance(node, ast.Import) for alias in node.names})
    (REPORT / "import-graph.json").write_text(json.dumps(imports, indent=2) + "\n", encoding="utf-8")
    print(f"Inventoried {len(names)} tracked files; protected {len(records)} scientific files")


def verify():
    baseline = json.loads((REPORT / "scientific-integrity.json").read_text(encoding="utf-8"))
    errors = [name for name, record in baseline["files"].items()
              if not (ROOT / name).is_file()
              or digest(ROOT / name) not in {record["sha256"], record["git_sha256"]}
              or git_digest("HEAD", name) != record["git_sha256"]]
    if errors:
        raise SystemExit("Scientific integrity mismatch: " + ", ".join(errors))
    print(f"Verified {len(baseline['files'])} scientific files against {baseline['base_commit']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["snapshot", "verify"])
    args = parser.parse_args()
    snapshot() if args.action == "snapshot" else verify()
