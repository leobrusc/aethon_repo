"""Independent read-only artifact review using existing gh/OpenSSL/static parsers.

Downloads metadata only. Never installs, imports, executes or reacquires wheels.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import uuid

from audit_ed25519_wheels import frozen_inventory, inspect_wheel
from static_native_headers import inspect_native


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, obj):
    raw = obj if isinstance(obj, bytes) else (json.dumps(obj, indent=2) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)


def to_bundle(attestation):
    """Structural PEP740 v1 -> Sigstore v0.3 mapping; preserve signed bytes."""
    if attestation["version"] != 1: raise ValueError("Unsupported attestation")
    for value in [attestation["envelope"]["statement"], attestation["envelope"]["signature"], attestation["verification_material"]["certificate"]]:
        base64.b64decode(value, validate=True)
    return {"mediaType": "application/vnd.dev.sigstore.bundle.v0.3+json",
            "verificationMaterial": {"certificate": {"rawBytes": attestation["verification_material"]["certificate"]},
                                     "tlogEntries": attestation["verification_material"]["transparency_entries"]},
            "dsseEnvelope": {"payloadType": "application/vnd.in-toto+json",
                             "payload": attestation["envelope"]["statement"],
                             "signatures": [{"keyid": "", "sig": attestation["envelope"]["signature"]}]}}


def fetch(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.username or parsed.password: raise ValueError("HTTPS metadata required")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "AETHON-static-trust-review"}), timeout=60) as response:
            raw = response.read(4 * 1024 * 1024 + 1)
            if len(raw) > 4 * 1024 * 1024: raise ValueError("Metadata limit")
            if urllib.parse.urlsplit(response.url).scheme != "https": raise ValueError("Non-HTTPS redirect")
            return raw, {"url": url, "effective_url": response.url, "status": response.status, "sha256": sha(raw)}
    except urllib.error.HTTPError as exc:
        raw = exc.read(65536)
        return raw, {"url": url, "status": exc.code, "sha256": sha(raw)}


def run(quarantine, worktree):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = quarantine / ("trust-review-" + stamp + "-" + uuid.uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    gh = shutil.which("gh")
    if not gh: raise RuntimeError("Existing gh unavailable; no installation permitted")
    tool_hash = sha(Path(gh).read_bytes())
    env = dict(os.environ, XDG_CACHE_HOME=str(out / "cache"), LOCALAPPDATA=str(out / "cache"), GH_PROMPT_DISABLED="1")
    commands = []
    def command(name, args, timeout=180):
        p = subprocess.run(args, capture_output=True, timeout=timeout, env=env)
        write(out / (name + ".stdout"), p.stdout); write(out / (name + ".stderr"), p.stderr)
        commands.append({"name": name, "argv": args, "exit_code": p.returncode,
                         "stdout_sha256": sha(p.stdout), "stderr_sha256": sha(p.stderr)})
        return p
    command("gh-version", [gh, "--version"])
    roots = command("trusted-root", [gh, "attestation", "trusted-root"])
    if roots.returncode == 0:
        write(out / "trusted-root.jsonl", roots.stdout)
    acquired = json.loads((quarantine / "manifests/ACQUISITION.json").read_text())
    artifacts, _ = frozen_inventory(worktree)
    results = []
    for artifact in artifacts:
        wheel = quarantine / "downloads" / artifact["filename"]
        assert sha(wheel.read_bytes()) == artifact["sha256"] and wheel.stat().st_size == artifact["bytes"]
        inspection, native, _ = inspect_wheel(wheel, artifact)
        binaries = [{"member": name, "sha256": sha(raw), "bytes": len(raw), **inspect_native(raw)} for name, raw in native.items()]
        url = "https://pypi.org/integrity/" + artifact["package"] + "/" + artifact["version"] + "/" + artifact["filename"] + "/provenance"
        raw, receipt = fetch(url)
        write(out / (artifact["filename"] + ".provenance.json"), raw)
        item = {"artifact": artifact, "integrity": "VERIFIED", "provenance_http": receipt,
                "inspection": inspection, "native": binaries, "verification": []}
        if receipt["status"] == 200:
            document = json.loads(raw)
            for i, group in enumerate(document["attestation_bundles"]):
                for j, a in enumerate(group["attestations"]):
                    bundle = out / (artifact["filename"] + f".{i}.{j}.bundle.json")
                    write(bundle, to_bundle(a))
                    args = [gh, "attestation", "verify", str(wheel), "--bundle", str(bundle), "--repo", "pyca/cryptography",
                            "--cert-identity", "https://github.com/pyca/cryptography/.github/workflows/pypi-publish.yml@refs/heads/main",
                            "--cert-oidc-issuer", "https://token.actions.githubusercontent.com", "--predicate-type", "https://docs.pypi.org/attestations/publish/v1", "--format", "json"]
                    if roots.returncode == 0: args += ["--custom-trusted-root", str(out / "trusted-root.jsonl")]
                    name = artifact["filename"] + f".{i}.{j}.verify"
                    p = command(name, args)
                    item["verification"].append({"name": name, "exit_code": p.returncode,
                                                  "result": json.loads(p.stdout) if p.returncode == 0 else None,
                                                  "error": p.stderr.decode(errors="replace") if p.returncode else None})
        results.append(item)
        print(json.dumps({"wheel": artifact["filename"], "integrity": "VERIFIED", "provenance_http": receipt["status"], "verification_exit_codes": [v["exit_code"] for v in item["verification"]]}), flush=True)
    assert tool_hash == sha(Path(gh).read_bytes())
    report = {"review_id": out.name, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "source_head": "0eef2cb7797df1ed21ae89cf3286462697aa3a83", "quarantine_id": acquired["acquisition_id"],
              "gh_sha256": tool_hash, "script_sha256": sha(Path(__file__).read_bytes()),
              "root_fetch_exit_code": roots.returncode, "commands": commands, "artifacts": results,
              "scope": "Only existing tools and metadata; no artifact loading, execution, installation or additional artifact acquisition"}
    write(out / "review.json", report)
    print(json.dumps({"review_directory": str(out), "root_fetch_exit_code": roots.returncode}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("quarantine", type=Path); parser.add_argument("worktree", type=Path)
    args = parser.parse_args()
    run(args.quarantine, args.worktree)
