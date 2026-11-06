"""Read acquired wheels; static OS parsers and partial public-attestation checks.

Never loads/imports wheel code. Existing OpenSSL processes public certificate/DSSE
data only. No trust-root bootstrap or complete Sigstore claim is made.
"""
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error

from audit_ed25519_wheels import (AUTHORIZED_HEAD, file_sha, frozen_inventory, inspect_wheel,
                                  metadata_bytes, sha, utc, write_once)
from static_native_headers import inspect_native

OPENSSL = Path("C:/Program Files/Git/usr/bin/openssl.exe")
WSL = Path(os.environ.get("SystemRoot", "C:/Windows"))/"System32/wsl.exe"


def dsse_pae(statement):
    kind = b"application/vnd.in-toto+json"
    return b"DSSEv1 "+str(len(kind)).encode()+b" "+kind+b" "+str(len(statement)).encode()+b" "+statement


def b64(value):
    return base64.b64decode(value, validate=True)


def verify_statement_subject(statement, artifact):
    obj = json.loads(statement)
    subjects = obj.get("subject", [])
    return (obj.get("_type") == "https://in-toto.io/Statement/v1" and len(subjects) == 1
            and subjects[0].get("name") == artifact["filename"]
            and subjects[0].get("digest", {}).get("sha256") == artifact["sha256"])


def trusted_command(args, output, name):
    p = subprocess.run(args, capture_output=True, timeout=60)
    raw = p.stdout+p.stderr
    write_once(output/(name+".txt"), raw)
    return p.returncode, p.stdout, sha(raw)


def provenance(artifact, quarantine, out):
    filename = artifact["filename"]
    url = "https://pypi.org/integrity/"+artifact["package"]+"/"+artifact["version"]+"/"+filename+"/provenance"
    result = {"filename": filename, "url": url, "full_verification": "PROVENANCE_NOT_VERIFIED"}
    try:
        raw, receipt = metadata_bytes(url)
    except urllib.error.HTTPError as exc:
        body = exc.read(65536)
        write_once(out/(filename+".http-error.txt"), body)
        return {**result, "http_status": exc.code, "status": "MISSING" if exc.code == 404 else "NOT_AUDITED", "response_sha256": sha(body)}
    write_once(out/(filename+".provenance.json"), raw)
    result.update(http_status=200, response_sha256=sha(raw), redirects=receipt["redirects"])
    document = json.loads(raw)
    checks = []
    for bundle_index, bundle in enumerate(document.get("attestation_bundles", [])):
        for index, attestation in enumerate(bundle.get("attestations", [])):
            prefix = f"{artifact['package']}-{artifact['target']}-{bundle_index}-{index}"
            item = {"publisher_claim": bundle.get("publisher"), "version": attestation.get("version"),
                    "certificate_chain": "NOT_AUDITED_NO_INDEPENDENT_TRUST_ROOT", "transparency_verification": "NOT_AUDITED"}
            if attestation.get("version") != 1:
                item.update(status="NOT_AUDITED", reason="UNSUPPORTED_ATTESTATION_VERSION"); checks.append(item); continue
            try:
                statement = b64(attestation["envelope"]["statement"])
                signature = b64(attestation["envelope"]["signature"])
                certificate = b64(attestation["verification_material"]["certificate"])
                item["subject_matches_acquired_bytes"] = verify_statement_subject(statement, artifact)
                item["statement_sha256"] = sha(statement)
                parsed = json.loads(statement)
                item["subject"] = parsed.get("subject")
                item["predicate_type"] = parsed.get("predicateType")
                item["transparency_entries"] = [{k: entry.get(k) for k in ["logIndex", "integratedTime", "logId", "kindVersion"]} for entry in attestation["verification_material"].get("transparency_entries", [])]
                cert_path, sig_path, pae_path, key_path = [out/(prefix+extension) for extension in [".cert.der", ".signature", ".pae", ".pub.pem"]]
                for path, content in [(cert_path, certificate),(sig_path, signature),(pae_path, dsse_pae(statement))]: write_once(path, content)
                if not item["subject_matches_acquired_bytes"]:
                    item["status"] = "INVALID"; checks.append(item); continue
                if not OPENSSL.is_file():
                    item.update(status="PARTIALLY_VERIFIED", dsse_signature="NOT_AUDITED_TOOL_UNAVAILABLE"); checks.append(item); continue
                before = file_sha(OPENSSL)
                code, key, _ = trusted_command([str(OPENSSL), "x509", "-inform", "DER", "-in", str(cert_path), "-pubkey", "-noout"], out, prefix+"-key-extraction")
                if code: raise ValueError("Certificate public-key parsing failed")
                write_once(key_path, key)
                code, key_info, _ = trusted_command([str(OPENSSL), "pkey", "-pubin", "-in", str(key_path), "-text", "-noout"], out, prefix+"-key-type")
                if code or b"prime256v1" not in key_info: raise ValueError("PEP740 P-256 key not confirmed")
                code, _, digest = trusted_command([str(OPENSSL), "dgst", "-sha256", "-verify", str(key_path), "-signature", str(sig_path), str(pae_path)], out, prefix+"-dsse-verification")
                item["dsse_signature"] = "VERIFIED_LEAF_KEY_ONLY" if code == 0 else "INVALID"
                item["signature_check_log_sha256"] = digest
                cert_code, cert_info, cert_digest = trusted_command([str(OPENSSL), "x509", "-inform", "DER", "-in", str(cert_path), "-noout", "-subject", "-issuer", "-dates", "-ext", "subjectAltName"], out, prefix+"-certificate")
                item["certificate_display"] = cert_info.decode(errors="replace") if cert_code == 0 else "NOT_AUDITED"
                item["certificate_log_sha256"] = cert_digest
                if before != file_sha(OPENSSL): raise ValueError("Audit verifier identity changed")
                item["audit_openssl_sha256"] = before
                item["status"] = "PARTIALLY_VERIFIED" if code == 0 else "INVALID"
            except (KeyError, ValueError, TypeError, OSError) as exc:
                item.update(status="NOT_AUDITED", error_type=type(exc).__name__, reason=str(exc))
            checks.append(item)
    result["checks"] = checks
    result["status"] = ("INVALID" if any(c.get("status") == "INVALID" for c in checks)
                        else "PARTIALLY_VERIFIED" if checks and all(c.get("status") == "PARTIALLY_VERIFIED" for c in checks) else "NOT_AUDITED")
    return result


def linux_path(path):
    value = Path(path).as_posix()
    if len(value) < 3 or value[1:3] != ":/": raise ValueError("WSL path unsupported")
    return "/mnt/"+value[0].lower()+value[2:]


def analyze(quarantine):
    root = Path(__file__).resolve().parents[1]
    artifacts, _ = frozen_inventory(root)
    acquisition = json.loads((quarantine/"manifests/ACQUISITION.json").read_text())
    if acquisition["authorized_head"] != AUTHORIZED_HEAD: raise ValueError("Foreign acquisition")
    analysis_id = "analysis-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = quarantine/"static-analysis"/analysis_id; out.mkdir(exist_ok=False)
    attest_dir = quarantine/"attestations"/analysis_id; attest_dir.mkdir(exist_ok=False)
    results, binaries = [], []
    tools = {"openssl": {"available": OPENSSL.is_file(), "sha256": file_sha(OPENSSL) if OPENSSL.is_file() else None},
             "readelf": {"preexisting_version": "GNU Binutils 2.46", "sha256": "c857339616bbbfa5eba32733e22365048903fbaf6ed2126b897dd138bcb741fc"},
             "objdump": {"preexisting_version": "GNU Binutils 2.46", "sha256": "44f07f8da860b15bd4dec909f229dec536595fb170a616fe3ab29c7b21c9736f"}}
    for artifact in artifacts:
        path = quarantine/"downloads"/artifact["filename"]
        if file_sha(path) != artifact["sha256"] or path.stat().st_size != artifact["bytes"]: raise ValueError("Acquired wheel changed")
        report, native, selected = inspect_wheel(path, artifact)
        for member, content in native.items():
            item = {"artifact":artifact["filename"], "member":member, "sha256":sha(content), "bytes":len(content), **inspect_native(content)}
            native_path = out/f"native-{len(binaries):04d}.data"
            write_once(native_path, content)  # Selected bytes only, external quarantine; never loaded.
            parser = "/usr/bin/readelf" if content.startswith(b"\x7fELF") else "/usr/bin/objdump"
            flags = ["--wide", "--file-header", "--dynamic"] if parser.endswith("readelf") else ["-p"]
            code, output, digest = trusted_command([str(WSL), "--distribution", "Ubuntu", "--exec", parser, *flags, linux_path(native_path)], out, f"native-{len(binaries):04d}-static-tool")
            item.update(static_tool=parser.rsplit("/",1)[-1], static_tool_exit_code=code, static_tool_log_sha256=digest)
            text = output.decode(errors="replace")
            if parser.endswith("objdump"):
                item["tool_imports"] = sorted(set(re.findall(r"DLL Name:\s*([^\r\n]+)", text)))
            else:
                item["tool_needed"] = sorted(set(re.findall(r"\(NEEDED\).*?\[([^\]]+)\]", text)))
            binaries.append(item)
        for license_item in report["licenses"]:
            license_item["bounded_text"] = selected[license_item["path"]][:256*1024].decode("utf-8", errors="replace")
        # Full license text stays in quarantine, public export redacts it.
        write_once(out/(artifact["filename"]+".inspection.json"), report)
        prov = provenance(artifact, quarantine, attest_dir)
        results.append({"artifact":artifact, "inspection":report, "provenance":prov})
        print(json.dumps({"filename":artifact["filename"],"members":report["member_count"],"licenses":[v["path"] for v in report["licenses"]],"provenance":prov["status"]}),flush=True)
    final = {"analysis_id":analysis_id,"timestamp_utc":utc(),"acquisition_id":acquisition["acquisition_id"],
             "acquisition_manifest_sha256":file_sha(quarantine/"manifests/ACQUISITION.json"),
             "analysis_script_sha256":file_sha(__file__),"native_parser_sha256":file_sha(Path(__file__).with_name("static_native_headers.py")),
             "audit_tools":tools,"artifacts":results,"native":binaries,"execution":"NO_WHEEL_CODE_EXECUTED_OR_IMPORTED"}
    write_once(quarantine/"manifests"/(analysis_id+".json"),final)
    print(json.dumps({"analysis_id":analysis_id,"native_count":len(binaries),"manifest":str(quarantine/"manifests"/(analysis_id+".json"))}),flush=True)
    return final


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("quarantine",type=Path)
    analyze(parser.parse_args().quarantine)
