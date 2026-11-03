"""Verify original dependency manifests retained byte-for-byte at their base SHA."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / "docs/security/historical-dependency-hashes.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        raw = (ROOT / "requirements/historical/pr2" / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise SystemExit(f"Historical dependency bytes changed: {name}")
    print(f"PASS: preserved {len(manifest['files'])} dependency manifests from {manifest['commit']}")


if __name__ == "__main__":
    main()
