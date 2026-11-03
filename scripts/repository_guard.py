"""Check new Git blobs for large files and recognizable credential formats.

Reads Git objects, so hydrated LFS content is never mistaken for a Git blob.
Does not print matching values. This is a scoped heuristic, not a privacy proof.
"""
import argparse
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 5 * 1024 * 1024
PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b"),
    re.compile(rb"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b"),
)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def violations(name, raw):
    findings = []
    if len(raw) > LIMIT:
        findings.append("Git blob exceeds 5 MiB; use LFS or a source manifest")
    if any(pattern.search(raw) for pattern in PATTERNS):
        findings.append("Possible credential: review privately")
    if Path(name).name == ".env" or name.endswith((".pem", ".key", ".token")):
        findings.append("Credential file must not be committed")
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--base", help="Compare new/modified files against this commit")
    args = parser.parse_args()
    if args.staged:
        names = git("diff", "--cached", "--name-only", "--diff-filter=ACM", "-z")
    elif args.base:
        names = git("diff", args.base, "HEAD", "--name-only", "--diff-filter=ACM", "-z")
    else:
        parser.error("Specify --staged or --base; unchanged historical blobs are not exempted implicitly")
    failed = False
    for name in filter(None, names.decode().split("\0")):
        raw = git("show", f":{name}" if args.staged else f"HEAD:{name}")
        for reason in violations(name, raw):
            print(f"{name}: {reason}")
            failed = True
    if failed:
        raise SystemExit(1)
    print("Git blob guard passed")


if __name__ == "__main__":
    main()
