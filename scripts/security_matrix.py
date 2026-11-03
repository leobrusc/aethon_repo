"""Normalize advisory aliases for analysis only; never change scanner inputs.

Reads the original PR #2 report and actual CI logs. OSV records enrich aliases,
severity and vectors. Failed enrichment is explicit, never treated as safety.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def components(records):
    parent = {}
    def find(value):
        parent.setdefault(value, value)
        if parent[value] != value:
            parent[value] = find(parent[value])
        return parent[value]
    for row in records:
        identifiers = [row["id"], *row.get("aliases", [])]
        for value in identifiers:
            parent[find(value)] = find(identifiers[0])
    groups = {}
    for value in parent:
        groups.setdefault(find(value), set()).add(value)
    return {value: sorted(group) for group in groups.values() for value in group}


def canonical(identifiers):
    return min(identifiers, key=lambda value: (
        0 if value.startswith("CVE-") else 1 if value.startswith("GHSA-") else 2, value
    ))


PATHS = {
    "transformers": ("P0", "Untrusted model/config/tokenizer loading; deserialization and file access",
                     "src/baseline_detectors.py:TransformerDetector; src/research_baseline.py; src/models/*_driver.py"),
    "torch": ("P0", "Untrusted serialized weights and distributed/model inputs",
              "HF AutoModel.from_pretrained in src/baseline_detectors.py and src/models/"),
    "accelerate": ("P0", "Checkpoint shard indexes can control filesystem access",
                   "src/models/hf_causal_driver.py:device_map='auto'; optional GPU loading"),
    "sentence-transformers": ("P0", "External model/config loading in optional research",
                              "requirements-research.txt; no direct internal import; external use REVIEW"),
    "filelock": ("P1", "Shared-cache locks, symlinks and local filesystem races",
                 "HF snapshot/model cache and download paths; transitive file locks"),
    "datasets": ("P0", "Untrusted data source, cache and remote dataset operations",
                 "Optional HF research environment; canonical src/dataset_loader.py uses pandas instead"),
    "pillow": ("P1", "Malformed image decoding; external/model assets",
               "Transitive matplotlib/Transformers image stack; no direct image upload entry point found"),
    "setuptools": ("P0", "Untrusted package metadata/archives and build-time code",
                   "pyproject.toml build backend; package installation, not prompt scoring"),
    "aiohttp": ("P1", "Untrusted HTTP/WebSocket requests, responses and headers",
                "Optional datasets/fsspec HTTP clients; no AETHON aiohttp server found"),
    "anyio": ("P1", "Untrusted network inputs and asynchronous resource exhaustion",
              "OpenAI/httpx networking in src/models/openai_driver.py, deepseek_driver.py and benchmark/asr.py"),
    "urllib3": ("P1", "Proxy/TLS/network traffic and remote downloads",
                "Transitive requests/data/model downloads; no direct proxy configuration found"),
    "certifi": ("P1", "TLS trust store used for untrusted network peers",
                "HTTPS clients for model/data downloads and API drivers"),
    "multidict": ("P1", "Untrusted HTTP header/key parsing",
                  "Optional aiohttp transitive dependency; no direct internal import"),
    "fsspec": ("P1", "Untrusted filesystem URLs and dataset paths",
               "Optional datasets remote filesystems; canonical loaders use local paths"),
}


def enrich(identifier, cache):
    path = cache / f"{identifier}.json"
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        if previous.get("retrieval_status") == "PASS":
            return previous
    try:
        request = urllib.request.Request(f"https://api.osv.dev/v1/vulns/{identifier}",
                                         headers={"User-Agent": "AETHON-security-audit"})
        with urllib.request.urlopen(request, timeout=40) as response:
            result = json.load(response)
        result["retrieval_status"] = "PASS"
        result["retrieval_url"] = request.full_url
    except (OSError, ValueError, urllib.error.URLError) as exc:
        result = {"id": identifier, "retrieval_status": "NOT_AUDITED",
                  "reason": f"{type(exc).__name__}: {exc}"}
        if identifier.startswith("CVE-"):
            try:
                url = f"https://api.github.com/advisories?cve_id={identifier}"
                request = urllib.request.Request(url, headers={"User-Agent": "AETHON-security-audit"})
                with urllib.request.urlopen(request, timeout=40) as response:
                    advisories = json.load(response)
                if advisories:
                    advisory = advisories[0]
                    result = {"id": identifier, "aliases": [v["value"] for v in advisory.get("identifiers", [])],
                              "summary": advisory.get("summary"), "database_specific": {"severity": advisory.get("severity", "UNKNOWN").upper()},
                              "severity": [{"type": "CVSS_V3", "score": advisory.get("cvss", {}).get("vector_string")}]
                              if advisory.get("cvss", {}).get("vector_string") else [],
                              "affected": [{"package": {"name": v["package"]["name"]}, "ranges": [{"events": [{"fixed": v["first_patched_version"]}]}]}
                                           for v in advisory.get("vulnerabilities", []) if v.get("first_patched_version")],
                              "retrieval_status": "PASS", "retrieval_url": url}
            except (OSError, ValueError, urllib.error.URLError):
                pass
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ci-log", default="results/security/pr2-security.log")
    args = parser.parse_args()
    original = ROOT / "docs/modernization/dependency-audit.json"
    data = json.loads(original.read_text(encoding="utf-8"))
    rows = []
    for package in data["packages"]:
        for advisory in package["advisories"]:
            rows.append({**advisory, "package": package["name"], "version": package["version"],
                         "source": "PR2-Windows"})
    ci = ROOT / args.ci_log
    for line in ci.read_text(encoding="utf-8-sig").splitlines():
        match = re.search(r"\b([a-z][a-z0-9_-]*)\s+(\d[^\s]*)\s+((?:CVE|GHSA|PYSEC)-\S+)(?:\s+(.*))?$", line)
        if match:
            package, version, identifier, fixes = match.groups()
            rows.append({"package": package, "version": version, "id": identifier,
                         "aliases": [], "fix_versions": (fixes or "").split(","), "source": "PR2-Linux-CI"})
    identifiers = {row["id"] for row in rows}
    cache = ROOT / "results/security/osv"
    cache.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        details = dict(zip(sorted(identifiers), pool.map(lambda value: enrich(value, cache), sorted(identifiers))))
    enriched = [{**row, "aliases": sorted(set(row.get("aliases", [])) |
                 set(details[row["id"]].get("aliases", [])))} for row in rows]
    groups = components(enriched)
    merged = {}
    for row in enriched:
        identity = canonical(groups[row["id"]])
        key = (row["package"], identity)
        item = merged.setdefault(key, {"package": row["package"], "vulnerability": identity,
                                      "aliases": groups[row["id"]], "occurrences": [], "records": []})
        item["occurrences"].append({"source": row["source"], "version": row["version"], "scanner_id": row["id"]})
        item["records"].append(details[row["id"]])
    matrix = []
    for item in sorted(merged.values(), key=lambda value: (PATHS.get(value["package"], ("P2",))[0], value["package"], value["vulnerability"])):
        records = item.pop("records")
        priority, vector, paths = PATHS.get(item["package"], ("P2", "REVIEW", "REVIEW"))
        severity = sorted({r.get("database_specific", {}).get("severity", "UNKNOWN") for r in records})
        vectors = sorted({s["score"] for r in records for s in r.get("severity", []) if "score" in s})
        fixes = set()
        for r in records:
            for affected in r.get("affected", []):
                if affected.get("package", {}).get("name", "").lower().replace("_", "-") == item["package"].replace("_", "-"):
                    fixes.update(e["fixed"] for region in affected.get("ranges", []) for e in region.get("events", []) if "fixed" in e)
        fixes.update(v for row in enriched if row["package"] == item["package"] and canonical(groups[row["id"]]) == item["vulnerability"] for v in row.get("fix_versions", []) if v)
        item.update(severity=severity, cvss_vectors=vectors, priority=priority,
                    exploitation_vector=vector, affected_code_paths=paths,
                    reachability="Potential path, not proof of exploitability; per-advisory details require operator review",
                    fixed_versions=sorted(fixes),
                    compatibility="Updated profile requires Python 3.12; historical profiles remain unchanged; validation in REPORT.md",
                    decision="Upgrade maintained profile; historical environment isolated and retains FAIL findings",
                    summaries=sorted({r.get("summary", "Metadata not supplied") for r in records}),
                    enrichment_status="PASS" if all(r.get("retrieval_status") == "PASS" for r in records) else "NOT_AUDITED",
                    metadata_sources=sorted({r["retrieval_url"] for r in records if r.get("retrieval_url")}),
                    sources=[f"https://api.osv.dev/v1/vulns/{identifier}" for identifier in sorted({o["scanner_id"] for o in item["occurrences"]})])
        matrix.append(item)
    output = ROOT / "docs/security"
    output.mkdir(parents=True, exist_ok=True)
    report = {"scanner_occurrences": len(rows), "windows_occurrences": sum(r["source"] == "PR2-Windows" for r in rows),
              "ci_occurrences": sum(r["source"] == "PR2-Linux-CI" for r in rows), "normalized_package_vulnerabilities": len(matrix),
              "unique_vulnerabilities": len({item["vulnerability"] for item in matrix}),
              "normalization": "Transitive alias components; preserve every raw scanner occurrence; CVE preferred over GHSA",
              "inputs": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in [original, ci]},
              "matrix": matrix}
    (output / "vulnerability-matrix.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    fields = ["package", "versions", "vulnerability", "aliases", "severity", "cvss_vectors", "priority",
              "summaries", "exploitation_vector", "affected_code_paths", "reachability", "fixed_versions", "compatibility", "decision", "enrichment_status", "sources", "metadata_sources"]
    with (output / "vulnerability-matrix.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in matrix:
            row = {key: item[key] for key in fields if key != "versions"}
            row["versions"] = sorted({o["version"] for o in item["occurrences"]})
            writer.writerow({key: json.dumps(value) if isinstance(value, list) else value for key, value in row.items()})
    print(json.dumps({key: value for key, value in report.items() if key not in {"matrix", "inputs"}}, indent=2))


if __name__ == "__main__":
    main()
