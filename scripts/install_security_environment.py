"""Install a hashed binary-only profile in a new dedicated repository venv.

The local editable AETHON source is the only authorized source build. Existing
historical environments are rejected by the path and ownership checks.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lock", type=Path)
    parser.add_argument("venv", type=Path)
    args = parser.parse_args()
    target = args.venv.resolve()
    marker = target / ".aethon-security-profile.json"
    if target.parent != ROOT or not target.name.startswith(".venv-"):
        parser.error("Use a dedicated .venv-* directly inside this worktree")
    if target.exists() and not marker.exists():
        parser.error("Refusing to change an existing environment without a security-profile marker")
    if not target.exists():
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(target)], check=True)
        marker.write_text(json.dumps({"purpose": "security-remediation", "lock": args.lock.name}), encoding="utf-8")
    python = target / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.run([sys.executable, "-m", "pip", "--isolated", "--python", str(python), "install",
                    "--index-url", "https://pypi.org/simple", "--require-hashes", "--only-binary=:all:",
                    "-r", str(args.lock.resolve())], check=True, cwd=ROOT)
    subprocess.run([sys.executable, "-m", "pip", "--isolated", "--python", str(python), "install",
                    "--no-deps", "--no-build-isolation", "-e", str(ROOT)], check=True, cwd=ROOT)
    print(f"Installed {args.lock.name} in {target.name}; historical environments untouched")


if __name__ == "__main__":
    main()
