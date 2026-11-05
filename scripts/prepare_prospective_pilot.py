"""Offline preparation only. Exit 2 means a valid plan still has launch blockers."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aethon.prospective import preflight, validate_fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.fixtures.read_text(encoding="utf-8"))
    identities = validate_fixture(rows)
    result = preflight(json.loads(args.manifest.read_text(encoding="utf-8")), ROOT)
    result["synthetic_fixture_count"] = len(identities)
    # No raw fixture text, generated response or model import in public report.
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "preflight.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 2 if result["classification"] == "PILOT_BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
