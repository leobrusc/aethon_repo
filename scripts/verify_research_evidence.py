"""Verify byte hashes in the working tree and optionally the actual Git tree."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    p = argparse.ArgumentParser(); p.add_argument("--root", default="docs/research_2026_evidence")
    p.add_argument("--git-tree", help="Also verify committed bytes, e.g. HEAD")
    a = p.parse_args(); root = Path(a.root)
    index = json.loads((root/"index.json").read_text(encoding="utf-8"))
    for record in index:
        path = root/record["artifact"].replace("\\", "/")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], f"Working-tree hash mismatch: {path}"
        if a.git_tree:
            raw = subprocess.check_output(["git", "show", f"{a.git_tree}:{path.as_posix()}"])
            assert hashlib.sha256(raw).hexdigest() == record["sha256"], f"Git-tree hash mismatch: {path}"
    print(f"Verified {len(index)} artifact hashes" + (f" in working tree and {a.git_tree}" if a.git_tree else " in working tree"))


if __name__ == "__main__": main()
