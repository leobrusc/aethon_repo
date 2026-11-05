"""Audit every locked dependency and explicitly cross-check PyTorch local builds.

Native scanner output is preserved, including unknown builds. The additional
upstream-version query is separate coverage, not an exemption or binary proof.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def locked_packages(lock, torch_record):
    packages = {}
    for line in lock.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^\s;\\]+)", line)
        if match:
            name, version = match.groups()
            packages[re.sub(r"[-_.]+", "-", name).lower()] = version
        elif line.startswith("torch @ "):
            if torch_record["url"] not in line or torch_record["sha256"] not in line:
                raise ValueError("Torch URL/hash does not match the official-artifact manifest")
            packages["torch"] = torch_record["version"]
        elif line and not line[0].isspace() and not line.startswith("#"):
            raise ValueError(f"Unrecognized lock requirement: {line}")
    if not packages or "torch" not in packages:
        raise ValueError("Missing dependency or explicit torch coverage")
    return packages


def scan(requirements, destination, site_packages=None):
    command = [sys.executable, "-m", "pip_audit",
               "--progress-spinner", "off", "--format", "json", "--output", str(destination)]
    if requirements:
        command.extend(["--strict", "--no-deps", "--disable-pip", "-r", str(requirements)])
    elif site_packages:
        command.extend(["--path", site_packages])
    environment = {**os.environ, "PIPAPI_PYTHON_LOCATION": sys.executable, "VIRTUAL_ENV": sys.prefix}
    # Native mode retains all unknown builds in JSON instead of aborting on the
    # first one. The separate lock/upstream query remains strict for every entry.
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, env=environment)
    destination.with_suffix(".log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    raw = json.loads(destination.read_text(encoding="utf-8")) if destination.exists() else {}
    skipped = [{"name": p["name"], "reason": p["skip_reason"]}
               for p in raw.get("dependencies", []) if p.get("skip_reason")]
    findings = [{"package": p["name"], "version": p.get("version"), "advisory": v}
                for p in raw.get("dependencies", []) for v in p.get("vulns", [])]
    status = "FAIL" if findings else "NOT_AUDITED" if skipped else "FAIL" if completed.returncode else "PASS"
    return {"status": status, "exit_code": completed.returncode, "skipped": skipped,
            "findings": findings, "raw": str(destination.relative_to(ROOT)),
            "raw_sha256": hashlib.sha256(destination.read_bytes()).hexdigest() if destination.exists() else None}


def provenance(record):
    distribution = importlib.metadata.distribution("torch")
    receipt = json.loads(distribution.read_text("direct_url.json") or "{}")
    actual_hash = receipt.get("archive_info", {}).get("hashes", {}).get("sha256")
    if receipt.get("url") != record["url"] or actual_hash != record["sha256"]:
        raise ValueError("Installed PyTorch wheel origin/hash is not the locked official artifact")
    import torch
    if torch.__version__ != record["version"]:
        raise ValueError("Imported torch version differs from locked build")
    return {"status": "PASS", "url": receipt["url"], "sha256": actual_hash,
            "version": torch.__version__, "cuda_runtime": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
            "exact_binary_catalog": "NOT_AUDITED", "meaning": "Verified official artifact, not a binary vulnerability proof"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lock", type=Path)
    parser.add_argument("--installed", action="store_true", help="Also verify installed versions, native audit and torch receipt")
    parser.add_argument("--target-python", default=sys.executable, help="Interpreter of the installed profile; scanner remains in the tool environment")
    parser.add_argument("--output", type=Path, default=Path("results/security/audits"))
    args = parser.parse_args()
    lock = args.lock.resolve()
    records = json.loads((ROOT / "docs/security/torch-artifacts.json").read_text(encoding="utf-8"))
    record = records[lock.name]
    if hashlib.sha256(lock.read_bytes()).hexdigest() != record["lock_sha256"]:
        raise SystemExit("Lock hash differs from recorded resolution")
    packages = locked_packages(lock, record)
    output = (ROOT / args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    prefix = output / lock.stem
    requirements = prefix.with_suffix(".requirements.txt")
    # PEP 440 public-version identity is queried separately from the +cpu/+cu build.
    requirements.write_text("\n".join(f"{name}=={record['upstream_version'] if name == 'torch' else version}"
                                      for name, version in sorted(packages.items())) + "\n", encoding="utf-8")
    report = {"lock": lock.name, "package_count": len(packages),
              "platform_installation": "NOT_RUN", "torch_binary_catalog": "NOT_AUDITED",
              "upstream_and_dependency_audit": scan(requirements, prefix.with_suffix(".upstream.json"))}
    if args.installed:
        collector = (
            "import json,sys,sysconfig,importlib.metadata,re; "
            "sys.path.insert(0,sys.argv[1]); import audit_security_environment as audit; "
            "data=json.load(sys.stdin); "
            "versions={re.sub(r'[-_.]+','-',d.metadata['Name']).lower():d.version for d in importlib.metadata.distributions()}; "
            "print(json.dumps({'versions':versions,'site':sysconfig.get_path('purelib'),'torch':audit.provenance(data['torch'])}))"
        )
        installed = json.loads(subprocess.check_output(
            [args.target_python, "-c", collector, str(ROOT / "scripts")],
            input=json.dumps({"torch": record}), text=True, cwd=ROOT))
        mismatches = [{"name": name, "expected": version, "actual": installed["versions"].get(name, "MISSING")}
                      for name, version in packages.items() if installed["versions"].get(name) != version]
        mismatches.extend({"name": name, "expected": "UNDECLARED", "actual": version}
                          for name, version in installed["versions"].items()
                          if name not in packages and name != "aethon-research")
        report["platform_installation"] = "FAIL" if mismatches else "PASS"
        report["version_mismatches"] = mismatches
        report["torch_provenance"] = installed["torch"]
        report["native_scanner"] = scan(None, prefix.with_suffix(".native.json"), installed["site"])
    prefix.with_suffix(".summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["upstream_and_dependency_audit"]["status"] != "PASS" or report["platform_installation"] == "FAIL" or report.get("torch_provenance", {}).get("status") == "FAIL" or report.get("native_scanner", {}).get("status") == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
