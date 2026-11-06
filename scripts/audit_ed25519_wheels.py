"""Five-wheel HTTP acquisition and bounded static inspection. NEVER installs/imports.

All wheel bytes remain in an external quarantine. Network acquisition is explicit;
importing this audit module performs no network or filesystem mutation.
"""
from __future__ import annotations

import argparse
import base64
import csv
from datetime import datetime, timezone
from email.parser import BytesParser
import getpass
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile

from packaging.utils import canonicalize_name, parse_wheel_filename

AUTHORIZED_HEAD = "b3f7819b94e8710cc4df9e7fb8ab87d5b323fc15"
FROZEN_INVENTORY = "docs/security/ed25519-v1/artifacts.json"
ALLOWLIST = {
    "cryptography-50.0.2-cp311-abi3-win_amd64.whl": "7afa5a6602a9f29af1f3a2965f831bae7c9d5d597b7cbb716d41ab3b7d89879c",
    "cryptography-50.0.2-cp311-abi3-manylinux_2_28_x86_64.whl": "4061c0079120205fb760c58acab6443e217307dcf05e3702cf970e0689972856",
    "cffi-2.1.1-cp312-cp312-win_amd64.whl": "f53e442b08449d42821fa4a4fba000095af9f62742a500f978a9f557ec44339a",
    "cffi-2.1.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl": "c1453022f490d2459a11819d83ad1d586e9ff65a12ac3e705ffebd46d3685dcf",
    "pycparser-3.12-py3-none-any.whl": "a076f3f489b39b43ed13563a1dafe42447445bec2e294154ec5c57fcdda4c85e",
}
MAX_MEMBER = 64*1024*1024
MAX_TOTAL = 128*1024*1024
MAX_ENTRIES = 10000


class Rejected(ValueError):
    pass


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()


def write_once(path, value):
    raw = value if isinstance(value, bytes) else (json.dumps(value, indent=2, ensure_ascii=False)+"\n").encode()
    with Path(path).open("xb") as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return sha(raw)


def validate_url(url, host, filename=None):
    p = urllib.parse.urlsplit(url)
    if (p.scheme != "https" or p.hostname != host or p.username or p.password
            or p.port not in (None, 443) or p.query or p.fragment or "\\" in url):
        raise Rejected("Untrusted HTTP origin or credentials")
    if filename and urllib.parse.unquote(p.path).rsplit("/", 1)[-1] != filename:
        raise Rejected("Redirect/download filename mismatch")
    return url


class StrictRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, host, filename=None):
        self.host, self.filename, self.chain = host, filename, []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl, self.host, self.filename)
        if len(self.chain) >= 5: raise Rejected("Redirect limit")
        self.chain.append({"status": code, "from": req.full_url, "to": newurl})
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_https(url, host, filename=None, data=None):
    validate_url(url, host, filename)
    redirects = StrictRedirects(host, filename)
    opener = urllib.request.build_opener(redirects)
    request = urllib.request.Request(url, data=data, headers={
        "User-Agent": "AETHON-static-wheel-audit/1", "Accept-Encoding": "identity",
        **({"Content-Type": "application/json"} if data is not None else {})})
    response = opener.open(request, timeout=30)
    validate_url(response.geturl(), host, filename)
    if response.status != 200: raise Rejected("Unexpected HTTP status")
    return response, redirects


def metadata_bytes(url, host="pypi.org"):
    response, redirects = open_https(url, host)
    with response:
        raw = response.read(2*1024*1024+1)
    if len(raw) > 2*1024*1024: raise Rejected("Oversized metadata")
    return raw, {"url": url, "effective_url": response.geturl(), "redirects": redirects.chain, "sha256": sha(raw)}


def safe_name(name):
    if (not name or name.startswith(("/", "\\")) or "\\" in name or ":" in name
            or any(unicodedata.category(c).startswith("C") for c in name)):
        raise Rejected("Unsafe ZIP name")
    parts = name.rstrip("/").split("/")
    reserved = {"con", "prn", "aux", "nul", *[f"com{i}" for i in range(1, 10)], *[f"lpt{i}" for i in range(1, 10)]}
    if any(p in ("", ".", "..") or p.endswith((" ", ".")) or p.split(".")[0].casefold() in reserved for p in parts):
        raise Rejected("Unsafe ZIP path component")
    return unicodedata.normalize("NFC", "/".join(parts)).casefold()


def binary_kind(name):
    lower = name.lower()
    if lower.endswith((".pyd", ".dll", ".exe")): return "PE"
    if re.search(r"\.so(?:\.|$)", lower): return "ELF"
    if lower.endswith((".a", ".lib")): return "ARCHIVE"
    return None


def inspect_wheel(path, artifact):
    """Stream every member/CRC/RECORD; only bounded selected bytes held in memory."""
    members, selected, folded = {}, {}, set()
    with Path(path).open("rb") as source:
        if source.read(4) != b"PK\x03\x04": raise Rejected("Wheel is not an ordinary ZIP archive")
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if not entries or len(entries) > MAX_ENTRIES: raise Rejected("ZIP entry limit")
        if sum(i.file_size for i in entries) > MAX_TOTAL: raise Rejected("ZIP total limit")
        for info in entries:
            key = safe_name(info.orig_filename)
            if info.orig_filename != info.filename or key in folded: raise Rejected("Duplicate/ambiguous ZIP name")
            folded.add(key)
            mode = info.external_attr >> 16
            if stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR): raise Rejected("Link/special ZIP entry")
            if ((stat.S_ISDIR(mode) and not info.is_dir()) or (stat.S_ISREG(mode) and info.is_dir())):
                raise Rejected("Inconsistent file/directory attributes")
            if info.flag_bits & 1 or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise Rejected("Encrypted/unsupported ZIP member")
            if (info.file_size > MAX_MEMBER or info.file_size < 0 or info.compress_size < 0
                    or info.file_size > max(info.compress_size, 1)*200):
                raise Rejected("ZIP member/bomb limit")
            if info.is_dir(): continue
            h, size, capture = hashlib.sha256(), 0, []
            keep = (binary_kind(info.filename) is not None or ".dist-info/" in info.filename)
            with archive.open(info) as stream:
                for block in iter(lambda: stream.read(65536), b""):
                    size += len(block)
                    if size > min(info.file_size, MAX_MEMBER): raise Rejected("Actual ZIP size limit")
                    h.update(block)
                    if keep: capture.append(block)
            if size != info.file_size: raise Rejected("ZIP declared/actual size mismatch")
            members[info.filename] = {"sha256": h.hexdigest(), "bytes": size, "compressed_bytes": info.compress_size,
                                      "kind": binary_kind(info.filename) or ("PYTHON" if info.filename.endswith(".py") else "DATA")}
            if keep: selected[info.filename] = b"".join(capture)
    for name in members:
        if any("/".join(name.split("/")[:n]) in members for n in range(1, len(name.split("/")))):
            raise Rejected("File/directory prefix collision")
    roots = {name.split("/")[0] for name in members if name.split("/")[0].endswith(".dist-info")}
    expected_root = artifact["package"].replace("-", "_")+"-"+artifact["version"]+".dist-info"
    if roots != {expected_root}: raise Rejected("Unexpected dist-info identity")
    for required in ["METADATA", "WHEEL", "RECORD"]:
        if expected_root+"/"+required not in members: raise Rejected("Missing wheel metadata")
    meta = BytesParser().parsebytes(selected[expected_root+"/METADATA"])
    wheel = BytesParser().parsebytes(selected[expected_root+"/WHEEL"])
    if (len(meta.get_all("Name", [])) != 1 or len(meta.get_all("Version", [])) != 1
            or canonicalize_name(meta["Name"]) != canonicalize_name(artifact["package"])
            or meta["Version"] != artifact["version"]): raise Rejected("Wheel package/version mismatch")
    filename_tags = {str(t) for t in parse_wheel_filename(artifact["filename"])[3]}
    if set(wheel.get_all("Tag", [])) != filename_tags: raise Rejected("WHEEL/filename tag mismatch")
    if wheel.get("Wheel-Version") != "1.0": raise Rejected("Unsupported Wheel-Version")
    record_name = expected_root+"/RECORD"
    rows = list(csv.reader(io.StringIO(selected[record_name].decode("utf-8"), newline="")))
    records = set()
    for row in rows:
        if len(row) != 3: raise Rejected("Malformed RECORD row")
        name, value, size = row
        safe_name(name)
        if name in records or name not in members: raise Rejected("RECORD duplicate/foreign member")
        records.add(name)
        if name == record_name:
            if value or size: raise Rejected("RECORD self hash must be empty")
            continue
        if not value or not size.isdigit() or int(size) != members[name]["bytes"]:
            raise Rejected("Missing RECORD hash/size or size mismatch")
        algorithm, encoded = value.split("=", 1)
        if algorithm != "sha256": raise Rejected("Unsupported RECORD digest; audit cannot claim PASS")
        expected = base64.urlsafe_b64encode(bytes.fromhex(members[name]["sha256"])).rstrip(b"=").decode()
        if encoded != expected: raise Rejected("RECORD digest mismatch")
    unlisted = set(members)-records
    if unlisted - {expected_root+"/RECORD.jws", expected_root+"/RECORD.p7s"}:
        raise Rejected("ZIP files absent from RECORD")
    native = {name: data for name, data in selected.items() if binary_kind(name)}
    if wheel.get("Root-Is-Purelib") == "true" and native: raise Rejected("Pure wheel has native payload")
    licenses = []
    for name, data in selected.items():
        if re.search(r"(?:license|copying|notice|authors)", name, re.I):
            text = data[:256*1024].decode("utf-8", errors="replace")
            hints = [token for token in ["Apache License", "MIT", "BSD", "OpenSSL", "libffi", "Redistribution", "Permission", "copyright"] if token.casefold() in text.casefold()]
            licenses.append({"path": name, **members[name], "text_hints": hints, "full_text_available_in_quarantine": True})
    embedded = []
    for name, data in selected.items():
        if ("sbom" in name.lower() or "cyclonedx" in name.lower()) and name.endswith(".json") and len(data) < 2*1024*1024:
            try: embedded.append({"path": name, "document": json.loads(data)})
            except ValueError: embedded.append({"path": name, "status": "UNPARSED_JSON"})
    result = {"filename": artifact["filename"], "status": "PASS", "member_count": len(members),
              "total_uncompressed_bytes": sum(m["bytes"] for m in members.values()), "members": members,
              "metadata": {key: meta.get_all(key, []) for key in ["Name", "Version", "Requires-Python", "Requires-Dist", "License-Expression", "License", "License-File", "Classifier"]},
              "wheel": {key: wheel.get_all(key, []) for key in ["Wheel-Version", "Generator", "Root-Is-Purelib", "Tag"]},
              "record_checked_files": len(records)-1, "record_authenticity": "NOT_A_SIGNATURE",
              "licenses": licenses, "embedded_sboms": embedded}
    return result, native, selected


def frozen_inventory(root):
    raw = subprocess.check_output(["git", "show", AUTHORIZED_HEAD+":"+FROZEN_INVENTORY], cwd=root)
    data = json.loads(raw)
    artifacts = data["artifacts"]
    if len(artifacts) != 5 or {a["filename"]: a["sha256"] for a in artifacts} != ALLOWLIST:
        raise Rejected("Frozen inventory differs from explicit user authorization")
    return artifacts, sha(raw)


def validate_published(artifact, metadata):
    info = metadata["info"]
    if canonicalize_name(info["name"]) != artifact["package"] or info["version"] != artifact["version"]:
        raise Rejected("Published release identity changed")
    matches = [f for f in metadata["urls"] if f["filename"] == artifact["filename"]]
    if len(matches) != 1: raise Rejected("Published filename not unique")
    item = matches[0]
    if (item["digests"]["sha256"] != artifact["sha256"] or item["size"] != artifact["bytes"]
            or item["packagetype"] != "bdist_wheel" or item["yanked"]
            or item["url"] != artifact["url"]): raise Rejected("Frozen/current publication divergence")
    validate_url(item["url"], "files.pythonhosted.org", artifact["filename"])
    return item


def promote_no_replace(part, target):
    if os.name == "nt": os.rename(part, target)  # Windows rename refuses existing destination.
    else:
        os.link(part, target)  # POSIX no-clobber atomic publication, then remove owned temp.
        os.unlink(part)


def acquire_one(artifact, published, quarantine):
    if ALLOWLIST.get(artifact["filename"]) != artifact["sha256"]:
        raise Rejected("Artifact is outside explicit authorization")
    target = quarantine/"downloads"/artifact["filename"]
    if target.exists(): raise Rejected("Existing artifact is immutable; new acquisition ID required")
    part = target.with_name(".download-"+uuid.uuid4().hex+".part")
    receipt = {"filename": artifact["filename"], "package": artifact["package"], "version": artifact["version"],
               "expected_sha256": artifact["sha256"], "expected_bytes": artifact["bytes"], "source_url": published["url"], "started_utc": utc()}
    try:
        response, redirects = open_https(published["url"], "files.pythonhosted.org", artifact["filename"])
        receipt.update(effective_url=response.geturl(), redirects=redirects.chain, content_type=response.headers.get("Content-Type"))
        content_length = response.headers.get("Content-Length")
        if content_length is not None and int(content_length) != artifact["bytes"]: raise Rejected("HTTP size mismatch")
        size, h = 0, hashlib.sha256()
        with response, part.open("xb") as stream:
            for block in iter(lambda: response.read(65536), b""):
                size += len(block)
                if size > artifact["bytes"]: raise Rejected("Download exceeds authorized size")
                h.update(block); stream.write(block)
            stream.flush(); os.fsync(stream.fileno())
        receipt.update(observed_bytes=size, observed_sha256=h.hexdigest())
        if size != artifact["bytes"] or h.hexdigest() != artifact["sha256"] or h.hexdigest() != published["digests"]["sha256"]:
            raise Rejected("Acquired bytes fail frozen/published digest or size")
        report, _, _ = inspect_wheel(part, artifact)
        write_once(quarantine/"static-analysis"/(artifact["filename"]+".json"), report)
        promote_no_replace(part, target)
        receipt.update(status="ARTIFACTS_VERIFIED", wheel_consistency="PASS", custody_scope="QUARANTINE_ONLY_NOT_INSTALLATION_APPROVAL", completed_utc=utc())
    except Exception as exc:
        receipt.update(status="QUARANTINED_REJECTED", error_type=type(exc).__name__, error=str(exc), completed_utc=utc())
        if part.exists(): receipt.update(observed_sha256=file_sha(part), observed_bytes=part.stat().st_size, preserved_partial=part.name)
        write_once(quarantine/"manifests"/(artifact["filename"]+".rejected.json"), receipt)
        raise
    write_once(quarantine/"manifests"/(artifact["filename"]+".json"), receipt)
    return receipt


def create_quarantine(root, base):
    forbidden = [Path(root).resolve(), Path(subprocess.check_output(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=root, text=True).strip()).resolve()]
    raw = subprocess.check_output(["git", "worktree", "list", "--porcelain", "-z"], cwd=root)
    forbidden += [Path(os.fsdecode(s)[9:]).resolve() for s in raw.split(b"\0") if s.startswith(b"worktree ")]
    base = Path(base)
    if not base.is_absolute(): raise Rejected("Absolute external quarantine required")
    resolved = base.resolve()
    if any(resolved == p or p in resolved.parents for p in forbidden): raise Rejected("Quarantine is in repository/worktree")
    for component in [base, *base.parents]:
        if component.exists():
            info = component.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400: raise Rejected("Quarantine ancestor is reparse/link")
    run_id = "ed25519-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex[:8]
    quarantine = base/run_id
    quarantine.mkdir(parents=True, exist_ok=False)
    for name in ["downloads", "metadata", "attestations", "static-analysis", "logs", "manifests"]: (quarantine/name).mkdir()
    return quarantine, run_id


def acquire(root, base):
    artifacts, inventory_sha = frozen_inventory(root)
    quarantine, run_id = create_quarantine(root, base)
    header = {"acquisition_id": run_id, "authorized_head": AUTHORIZED_HEAD,
              "audit_code_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
              "audit_script_sha256": file_sha(__file__), "frozen_inventory_sha256": inventory_sha,
              "operator_local": getpass.getuser(), "timestamp_utc": utc(), "quarantine": str(quarantine),
              "scope": "ONLY_FIVE_WHEELS_STATIC_NO_INSTALL_NO_IMPORT", "source": "OFFICIAL_PYPI_HTTPS"}
    write_once(quarantine/"manifests"/"START.json", header)
    releases, receipts = {}, []
    try:
        for artifact in artifacts:
            key = (artifact["package"], artifact["version"])
            if key not in releases:
                url = "https://pypi.org/pypi/"+key[0]+"/"+key[1]+"/json"
                raw, evidence = metadata_bytes(url)
                releases[key] = json.loads(raw)
                write_once(quarantine/"metadata"/(key[0]+"-"+key[1]+".json"), raw)
                write_once(quarantine/"metadata"/(key[0]+"-"+key[1]+".receipt.json"), evidence)
            published = validate_published(artifact, releases[key])
            receipts.append(acquire_one(artifact, published, quarantine))
            print(json.dumps({"filename": artifact["filename"], "status": receipts[-1]["status"], "sha256": receipts[-1]["observed_sha256"]}), flush=True)
    except Exception as exc:
        write_once(quarantine/"manifests"/"STOPPED.json", {"header": header, "verified_receipts": receipts, "status": "ACQUISITION_STOPPED", "error_type": type(exc).__name__, "error": str(exc), "timestamp_utc": utc()})
        raise
    final = {**header, "completed_utc": utc(), "artifacts": receipts, "integrity": "ARTIFACTS_VERIFIED", "provenance": "NOT_YET_AUDITED", "installation": "DEPENDENCY_APPROVAL_REQUIRED", "pilot": "PILOT_BLOCKED"}
    write_once(quarantine/"manifests"/"ACQUISITION.json", final)
    print(json.dumps({"acquisition_id": run_id, "private_quarantine": str(quarantine), "status": "ARTIFACTS_VERIFIED"}), flush=True)
    return final


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quarantine-base", required=True)
    args = parser.parse_args()
    acquire(Path(__file__).resolve().parents[1], args.quarantine_base)


if __name__ == "__main__": main()
