"""Check new Git blobs for large files and recognizable credential formats.

Reads Git objects, so hydrated LFS content is never mistaken for a Git blob.
Does not print matching values. This is a scoped heuristic, not a privacy proof.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 5 * 1024 * 1024
# One immutable, reviewed historical result is retained as a Git blob.
# Any content or path change falls back to the standard large-blob rejection.
ALLOWED_LARGE_BLOBS = {
    "results/revision/detection/per_prompt_results.csv":
        "66130f23a92ea05fca856c808a4049245a31d0f6c530bbba517473be389e7a15",
}
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
        allowed_sha256 = ALLOWED_LARGE_BLOBS.get(name)
        actual_sha256 = hashlib.sha256(raw).hexdigest()
        if allowed_sha256 != actual_sha256:
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
