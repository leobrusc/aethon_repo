"""Generate Python 3.12 locks and bind torch to official wheel URL + SHA-256.

Run with uv 0.13.7 on PATH. GPU resolution does not validate GPU execution.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urljoin, urlsplit, parse_qs
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LOCKS = ROOT / "requirements/environments"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.extend(value for key, value in attrs if key == "href")


def torch_wheel(backend, platform, version):
    index = f"https://download.pytorch.org/whl/{backend}/torch/"
    with urllib.request.urlopen(index, timeout=60) as response:
        raw = response.read()
    parser = Links()
    parser.feed(raw.decode())
    candidates = []
    for link in parser.links:
        url = urljoin(index, link)
        parsed = urlsplit(url)
        filename = unquote(parsed.path.rsplit("/", 1)[-1])
        if not filename.startswith(f"torch-{version}+{backend}-cp312-cp312-"):
            continue
        if platform == "windows" and "win_amd64" not in filename:
            continue
        if platform == "linux" and ("linux" not in filename or "x86_64" not in filename):
            continue
        if parsed.hostname not in {"download.pytorch.org", "download-r2.pytorch.org"} or parsed.scheme != "https":
            raise ValueError("Unexpected PyTorch artifact origin")
        sha = parse_qs(parsed.fragment).get("sha256", [None])[0]
        if not sha or not re.fullmatch("[a-f0-9]{64}", sha):
            raise ValueError("Official wheel lacks a SHA-256")
        candidates.append({"url": url.split("#", 1)[0], "sha256": sha, "filename": filename,
                           "index": index, "index_sha256": hashlib.sha256(raw).hexdigest()})
    if len(candidates) != 1:
        raise ValueError(f"Expected one official {platform}/{backend} wheel, found {len(candidates)}")
    return candidates[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["cpu", "dev", "research", "gpu"], required=True)
    parser.add_argument("--platform", choices=["windows", "linux"], required=True)
    args = parser.parse_args()
    if args.profile == "gpu" and args.platform != "linux":
        parser.error("Only Linux CUDA is declared; other GPU environments are NOT_RUN")
    if subprocess.check_output(["uv", "--version"], text=True).split()[1] != "0.13.7":
        raise SystemExit("Use uv==0.13.7 to regenerate locks")
    backend = "cu130" if args.profile == "gpu" else "cpu"
    version = "2.14.1" if args.profile == "gpu" else "2.15.0"
    output = LOCKS / f"{args.profile}-{args.platform}-py312.lock"
    subprocess.run(["uv", "pip", "compile", (LOCKS / f"{args.profile}.in").relative_to(ROOT).as_posix(),
                    "--python-version", "3.12", "--python-platform", args.platform,
                    "--torch-backend", backend, "--generate-hashes", "--emit-index-annotation",
                    "--no-build", "-o", output.relative_to(ROOT).as_posix()], check=True, cwd=ROOT)
    artifact = torch_wheel(backend, args.platform, version)
    text = output.read_text(encoding="utf-8")
    block = re.compile(r"^torch==[^\n]+(?:\n[ \t]+--hash=[^\n]+)*", re.M)
    match = block.search(text)
    if not match or artifact["sha256"] not in match.group():
        raise ValueError("Resolved torch hashes do not match the official platform wheel")
    replacement = f"torch @ {artifact['url']} --hash=sha256:{artifact['sha256']}"
    output.write_text(block.sub(lambda _: replacement, text, count=1), encoding="utf-8")
    evidence = ROOT / "docs/security/torch-artifacts.json"
    records = json.loads(evidence.read_text(encoding="utf-8")) if evidence.exists() else {}
    records[output.name] = {**artifact, "version": f"{version}+{backend}", "platform": args.platform,
                            "python": "3.12", "upstream_version": version,
                            "lock_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                            "binary_execution": "NOT_RUN", "binary_advisory_catalog": "NOT_AUDITED"}
    evidence.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"Locked {output.name} to official {artifact['filename']}")


if __name__ == "__main__":
    main()
