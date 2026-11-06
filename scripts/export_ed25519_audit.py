"""Export redacted static evidence; never copies wheel or native binary bytes."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(quarantine, before, after, destination):
    destination.mkdir(parents=True, exist_ok=False)
    evidence = destination / "evidence"
    evidence.mkdir()
    acquisition = json.loads((quarantine / "manifests/ACQUISITION.json").read_text())
    analysis_path = quarantine / "manifests/analysis-20261106T135358Z.json"
    analysis = json.loads(analysis_path.read_text())
    advisory_path = quarantine / "metadata/advisories-20261106T1408.json"
    advisories = json.loads(advisory_path.read_text())
    inventory_before = json.loads((before / "inventory.json").read_text())
    inventory_after = json.loads((after / "inventory.json").read_text())
    assert inventory_before == inventory_after, "Preserved inventory changed"
    assert len(acquisition["artifacts"]) == 5
    for item in acquisition["artifacts"]:
        path = quarantine / "downloads" / item["filename"]
        assert digest(path) == item["expected_sha256"] == item["observed_sha256"]
        assert path.stat().st_size == item["expected_bytes"] == item["observed_bytes"]
    private_digest = digest(quarantine / "manifests/ACQUISITION.json")
    acquisition["operator_local"] = "REDACTED_LOCAL_OPERATOR"
    acquisition["quarantine"] = "%LOCALAPPDATA%/AETHON-Quarantine/" + acquisition["acquisition_id"]
    acquisition["private_original_manifest_sha256"] = private_digest
    analysis["private_original_manifest_sha256"] = digest(analysis_path)
    for artifact in analysis["artifacts"]:
        for license_item in artifact["inspection"]["licenses"]:
            license_item.pop("bounded_text", None)
    def put(name, value):
        text = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False) + "\n"
        assert "C:\\Users\\leolima" not in text and "C:/Users/leolima" not in text
        with (destination / name).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    put("evidence/acquisition.json", acquisition)
    put("evidence/static-analysis.json", analysis)
    put("evidence/advisories.json", advisories)
    put("evidence/openssl-advisory-receipt.json", json.loads((quarantine / "metadata/openssl-advisory-receipt.json").read_text()))
    preservation = {"status": "PASS", "before": json.loads((before / "summary.json").read_text()),
                    "after": json.loads((after / "summary.json").read_text()),
                    "inventory_identical": True, "inventory_sha256": digest(before / "inventory.json"),
                    "preserved_inventory": inventory_before,
                    "independent_raw_dataset_hash": "NOT_AUDITED",
                    "scope": "Tracked requirements/locks, installed distribution metadata and interpreter hashes; not every runtime byte or bytecode cache."}
    put("evidence/preservation.json", preservation)
    rows = []
    for item, detail in zip(acquisition["artifacts"], analysis["artifacts"]):
        rows.append(f"| `{item['filename']}` | {item['observed_bytes']} | `{item['observed_sha256']}` | PASS | {detail['provenance']['status']} |")
    matrix = "| Wheel | Bytes | Expected = observed = PyPI SHA-256 | Integrity | Provenance |\n|---|---:|---|---|---|\n" + "\n".join(rows) + "\n"
    origin = "b3f7819b94e8710cc4df9e7fb8ab87d5b323fc15"
    common = "\nInstallation: **DEPENDENCY_APPROVAL_REQUIRED**. Prospective execution: **PILOT_BLOCKED**; all eight operational gates remain PENDING.\n"
    put("INTEGRITY_MATRIX.md", "# Acquired artifact integrity\n\n" + matrix + "\nAll five artifacts passed exact frozen allowlist, official JSON digest/size/URL and local byte checks. Five archives passed bounded ZIP/CRC/RECORD, filename, distribution/version, tags and member consistency checks. RECORD establishes internal consistency, not authenticity. No wheel code was executed/imported.\n" + common)
    put("ACQUISITION_REPORT.md", f"""# Controlled wheel acquisition — Phase 5B

Overall: **SUPPLY_CHAIN_REVIEW_PENDING**. Artifact integrity: **ARTIFACTS_VERIFIED**, 5/5. No artifact rejected.

Authorized source: `{origin}` (PR #20); engineering baseline: `9ed55709add0fc45f63847a0394315863faa0876`; architecture PR #19: `7431d7b423bc6fc34d1db51c12794742481f8428`.
Acquisition `{acquisition['acquisition_id']}` used audit commit `{acquisition['audit_code_head']}`; exact script hashes, timestamps and custody receipts are indexed in evidence. HTTPS URLs came from official exact-version PyPI JSON; redirects were checked before following. Only the five authorized distribution files were fetched. No sdists, alternative wheels, resolution, installation, build, wheel import, native loading, inference or provisioning occurred.

{matrix}
The worktree was created from the authorized source. Original dirty checkout, main refs and PR #15–#20 refs were preserved. Preexisting five local files were hash checked, never stashed or overwritten. Historical CI for PR #20: [42093929291](https://github.com/leobrusc/aethon_repo/actions/runs/42093929291), completed SUCCESS on all three jobs (research-and-gpu-audit; Windows CPU; Linux CPU), associated with the authorized PR head. This is distinct from PR #19 CI #42088936881. No new installation-running CI was authorized; this audit uses `[skip ci]`, and its local checks are separately recorded. Required CI checks may remain pending.

Scientific checks passed before/after: 127 protected files, 31 indexed evidence items, six historical manifests, 9,139 paired B3/B4 records, 80 historical metrics (atol 1e-12, rtol 0), five hydrated LFS payloads and five preexisting local files. No lock/dependency or installed-distribution metadata/interpreter hash changed. Independent raw dataset canonical hash remains NOT_AUDITED.

Provenance is partial for two cryptography wheels and missing for three other wheels. Package advisories and declared Rust dependency coverage are version scoped; exact binary vulnerabilities and unidentified libffi remain NOT_AUDITED. See the dedicated reports and validation evidence.
""" + common)
    put("PROVENANCE_REVIEW.md", """# Provenance review

Two cryptography provenance API responses bind a single filename/SHA-256 subject to the actual acquired bytes. PEP 740 v1 DSSE P-256/SHA-256 signatures verify mathematically with their presented certificate leaf public keys using the preexisting Git OpenSSL 3.5.4. Exact statement bytes, not reserialized JSON, were verified. This tool is audit-only and is not the future SRC-01 production verifier.

Both: **PARTIALLY_VERIFIED / PROVENANCE_NOT_VERIFIED**. Publisher claim: GitHub `pyca/cryptography`, workflow `pypi-publish.yml`; certificate SAN names that workflow at `refs/heads/main`. Certificate issuer claims sigstore-intermediate/sigstore.dev. Validity shown: 2026-09-30 14:43:03–14:53:03 UTC. Transparency log indexes: 3020561492 and 3020563834. These are untrusted claims until independently verified. A currently expired short-lived certificate alone does not invalidate a historical signature.

An independently trusted Fulcio chain/root and Rekor inclusion/checkpoint/identity/time policy were not verified. No trusted complete Sigstore verifier was available; none was installed. Public key possession/signature math does not authenticate publisher identity, certificate chain, timestamp, workflow commit or transparency inclusion. No claim of VERIFIED provenance is made.

cffi Windows, cffi Linux and pycparser: official integrity endpoints returned HTTP 404; **MISSING / PROVENANCE_NOT_VERIFIED**. Exact response hashes are in static-analysis.json. No 404 was converted into approval. No invalid signature or subject mismatch was observed in the available attestations.

References: [PEP 740](https://peps.python.org/pep-0740/), [PyPI Integrity API](https://docs.pypi.org/api/integrity/). Full public evidence structures and private receipt hashes are retained; no private keys were generated.
""" + common)
    native_lines = []
    for n in analysis["native"]:
        imports = n.get("imports", n.get("needed", []))
        native_lines.append(f"- `{n['artifact']}` → `{n['member']}`; {n['bytes']} bytes; SHA-256 `{n['sha256']}`; {n['format']}; imports/NEEDED: {', '.join(imports)}.")
    put("NATIVE_COMPONENTS.md", "# Static native composition\n\n" + "\n".join(native_lines) + "\n\nFour native extensions, no separately shipped DLL/EXE/archive library observed. cryptography: OpenSSL 4.0.3 (29 Sep 2026) literal plus acquired embedded SBOM; Rust/PyO3 0.29.2 and openssl-sys 0.9.117 literals/SBOM. No external libcrypto/libssl import observed; consistent with static linkage, not proof of complete linkage/runtime closure. cffi: libffi/ffi symbols observed, exact version NOT_IDENTIFIED. pycparser contains no native binary.\n\nTrusted preexisting GNU Binutils 2.46 readelf/objdump parsed selected bytes in external quarantine, corroborating bounded stdlib PE/ELF parsing. No ldd, dlopen, Python wheel import or artifact execution was used. Tool hashes and output hashes are recorded. OS import names establish names, not deployed OS library versions or future loader resolution. Build metadata: cryptography maturin 1.14.1; cffi setuptools 83.0.0; pycparser setuptools 84.2.1. These build labels are declarations, not independent build attestations.\n" + common)
    put("LICENSE_REVIEW.md", """# License review

Acquired METADATA and actual LICENSE texts agree: cryptography `Apache-2.0 OR BSD-3-Clause` (LICENSE, LICENSE.APACHE, LICENSE.BSD); cffi `MIT-0`; pycparser `BSD-3-Clause`. Individual member hashes and sizes are preserved in the static evidence. Both platform variants carry matching package license bytes.

cryptography embeds upstream Rust CycloneDX declarations for 39 components, including build/proc-macro dependencies; expressions include MIT, Apache-2.0, BSD-3-Clause, Unicode-3.0, Apache-2.0 WITH LLVM-exception and the choice Apache-2.0 OR GPL-2.0-only for self_cell. These are upstream declarations in acquired bytes, not independent legal certification or proof each crate is linked. Its separate OpenSSL 4.0.3 SBOM has no license entry. OpenSSL upstream declares Apache-2.0; incorporated notices still require review. cffi's MIT-0 package license does not by itself establish the license/notice completeness of embedded libffi (version unknown).

BSD binary redistribution requires notice/disclaimer preservation; Apache redistribution and NOTICE conditions apply as relevant; optional-license choices must be documented before distribution. pycparser text contains copyright 2008–2027; recorded verbatim as publisher metadata, without inference of authenticity from its date. No binaries are redistributed by this PR. Third-party notice completeness and distribution compatibility remain PENDING legal/governance review; this is not a formal legal opinion.
""" + common)
    assert len(advisories["response"]["results"]) == len(advisories["queries"])
    hits = [(q, r) for q, r in zip(advisories["queries"], advisories["response"]["results"]) if r.get("vulns")]
    put("VULNERABILITY_REVIEW.md", f"""# Version-scoped vulnerability review

Fresh [OSV API](https://google.github.io/osv.dev/post-v1-querybatch/) query at {advisories['timestamp_utc']}: {len(advisories['queries'])} exact package/version queries, {len(hits)} returned vulnerable package results. Queries cover cryptography 50.0.2, cffi 2.1.1, pycparser 3.12 (PyPI) and 32 externally named crates in the acquired embedded Rust SBOM. Seven local cryptography crates are not treated as independently registered packages. Full queries/response and SHA-256 are in evidence/advisories.json.

Official PyPI exact-version metadata vulnerability fields were also inspected as source metadata; absence of records is limited source coverage. [OpenSSL 29 Sep 2026 advisory](https://openssl-library.org/news/secadv/20260929.txt) was preserved with a receipt: its OpenSSL 4.0 affected ranges are stated as before 4.0.3, matching the acquired version as a fixing version for those listed issues. This is a scoped advisory comparison, not a complete current binary vulnerability verdict.

Limits: OSV coverage is not platform/build exhaustive; upstream Rust SBOM includes build dependencies and does not prove final linkage. OpenSSL compile options, enabled paths, backports and build provenance are not independently established. libffi version NOT_IDENTIFIED; applicability NOT_AUDITED. OS DLL/SO versions and deployed runtime are NOT_AUDITED. Complete exact-bin vulnerability coverage remains NOT_AUDITED. No zero-findings result authorizes installation or claims binary safety. No audit package or wheel component was installed/executed.
""" + common)
    components, dependencies = [], []
    for index, detail in enumerate(analysis["artifacts"]):
        a = detail["artifact"]; ref = "wheel:" + a["filename"]
        metadata = detail["inspection"]["metadata"]
        license_values = metadata.get("License-Expression", [])
        component = {"type": "library", "bom-ref": ref, "name": a["package"], "version": a["version"],
                     "purl": f"pkg:pypi/{a['package']}@{a['version']}?file_name={a['filename']}",
                     "hashes": [{"alg": "SHA-256", "content": a["sha256"]}],
                     "properties": [{"name": "aethon:scope", "value": "ACQUIRED_WHEEL_NOT_INSTALLED"},
                                    {"name": "aethon:platform", "value": a["target"]},
                                    {"name": "aethon:discovery", "value": "ZIP/METADATA/RECORD; evidence/static-analysis.json"},
                                    {"name": "aethon:provenance", "value": detail["provenance"]["status"]}]}
        if license_values: component["licenses"] = [{"expression": license_values[0]}]
        components.append(component); children = []
        for n in analysis["native"]:
            if n["artifact"] != a["filename"]: continue
            child = ref + ":native:" + n["sha256"]
            components.append({"type": "file", "bom-ref": child, "name": n["member"],
                               "hashes": [{"alg": "SHA-256", "content": n["sha256"]}],
                               "properties": [{"name": "aethon:discovery", "value": "Acquired member bytes; static PE/ELF parsing"}]})
            children.append(child)
        for sbom in detail["inspection"]["embedded_sboms"]:
            for offset, upstream in enumerate(sbom["document"].get("components", [])):
                c = {k: copy.deepcopy(upstream[k]) for k in ["type", "name", "version", "purl", "licenses", "hashes"] if k in upstream}
                child = ref + ":declared:" + sbom["path"] + ":" + str(offset)
                c["bom-ref"] = child
                c["properties"] = [{"name": "aethon:discovery", "value": "DECLARED_IN_ACQUIRED_EMBEDDED_SBOM:" + sbom["path"]},
                                   {"name": "aethon:linkage", "value": "NOT_INDEPENDENTLY_ESTABLISHED; may include build-only components"}]
                components.append(c); children.append(child)
        if a["package"] == "cryptography": children.append("wheel:" + analysis["artifacts"][2 if index == 0 else 3]["artifact"]["filename"])
        if a["package"] == "cffi":
            children.append("wheel:" + analysis["artifacts"][4]["artifact"]["filename"])
            libffi_ref = ref + ":observed:libffi"
            components.append({"type": "library", "bom-ref": libffi_ref, "name": "libffi",
                               "properties": [{"name": "aethon:version", "value": "NOT_IDENTIFIED"},
                                              {"name": "aethon:discovery", "value": "Native literal/symbol references in acquired cffi extension; exact build/version/license NOT_AUDITED"}]})
            children.append(libffi_ref)
        dependencies.append({"ref": ref, "dependsOn": children})
    put("STATIC_SBOM.cdx.json", {"bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1,
        "metadata": {"timestamp": datetime.now(timezone.utc).isoformat(), "component": {"type": "data", "name": "AETHON five acquired wheels static inventory", "version": acquisition["acquisition_id"]},
                     "properties": [{"name": "aethon:limitations", "value": "Artifact inventory, not installation/runtime. Dependencies include declared composition/build relationships; no complete dynamic closure. libffi version unknown. CycloneDX schema validation NOT_RUN: trusted schema validator unavailable."}]},
        "components": components, "dependencies": dependencies})
    put("CHAIN_OF_CUSTODY.md", f"""# Chain of custody

Run `{acquisition['acquisition_id']}`. Private quarantine: `%LOCALAPPDATA%/AETHON-Quarantine/{acquisition['acquisition_id']}`; external to repository, all worktrees and builds. Source commit `{origin}`; acquisition audit code `{acquisition['audit_code_head']}`. Original private manifest SHA-256 `{private_digest}`. Operator identity and absolute local path are retained privately and redacted publicly. This public JSON is explicitly a redacted derivative, not the original signed evidence (no signing authority is claimed).

Per-file exclusive temporary download, streaming SHA-256/size verification, bounded format checks and atomic no-clobber promotion occurred only within quarantine. Existing verified files were never replaced. Immutable create-only per-artifact receipts, original PyPI metadata, attestations/404 responses, selected native analysis bytes and static-tool outputs remain in quarantine. Public manifests record source/effective URLs, expected/observed SHA-256 and size, UTC timestamps, status and evidence hashes. No package binary/native member is published.

Audit files are append-only by application convention; no claim of WORM, authenticated timestamp, adversarial host protection, encryption, privileged ACL hardening or rollback-proof storage. Retain privately pending project governance disposition; no deletion or production storage provisioning was performed. Public SHA256SUMS.json hashes every published document/evidence except itself. This proves later byte consistency only, not source identity or a trusted timestamp.
""" + common)
    put("NEXT_APPROVAL_GATE.md", """# Next approval gate

**SUPPLY_CHAIN_REVIEW_PENDING** overall; **ARTIFACTS_VERIFIED** for five archive identities only. Complete independent Sigstore chain/identity/time/transparency verification for cryptography; decide treatment of missing cffi/pycparser attestations; resolve libffi exact version/notice requirements and third-party license completeness; review native/binary advisory coverage. No invalid artifact was promoted to deployment: all remain quarantined.

A separate explicit authorization is required before any installation, lock update, runtime selection, dependency/native loading or in-process adapter implementation. Approval must name exact wheels/hashes, platforms, isolation/runtime controls, rollback and supply-chain exceptions. Acquisition authorization does not grant these actions. Keep SRC-01 production verifier blocked until implementation/runtime independently reviewed. OS/host compromise guarantees remain outside this static audit.

The eight gates (independent_inventory, semantic_review, rubric_review, reviewer_assignment, private_storage, model_assets, hardware_check, execution_authorization) remain PENDING. No signature or static audit alone authorizes a pilot. No efficacy, ASR or statistical power is estimated from fixtures. Recommended next action: independent review of this evidence and narrowly scoped dependency/runtime approval decision, then adapter/native review; no pilot execution.
""" + common)
    print(json.dumps({"exported": str(destination), "components": len(components), "hashes": "5/5", "status": "SUPPLY_CHAIN_REVIEW_PENDING"}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ["quarantine", "before", "after", "destination"]: p.add_argument(name, type=Path)
    args = p.parse_args()
    export(args.quarantine, args.before, args.after, args.destination)
