"""Synthetic archives only; no acquisition, install, hooks, import or native load."""
import base64
import csv
import importlib.util
import io
from pathlib import Path
import stat
import warnings
import zipfile

import pytest


def source_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1]/"scripts"/filename)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


audit = source_module("wheel_audit", "audit_ed25519_wheels.py")
native = source_module("native_headers", "static_native_headers.py")


def fixture_wheel(tmp_path, mode=None):
    root = "fixture-1.0.dist-info"
    files = {"fixture/__init__.py": b"raise RuntimeError('MUST NEVER IMPORT')\n",
             root+"/METADATA": b"Metadata-Version: 2.4\nName: fixture\nVersion: 1.0\n",
             root+"/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"}
    if mode == "traversal": files["../escape.py"] = b"untrusted bytes"
    if mode == "case-collision": files.update({"fixture/A.py":b"a", "fixture/a.py":b"b"})
    if mode == "prefix-collision": files["fixture"] = b"not a directory"
    if mode == "bomb": files["fixture/repetitive.txt"] = b"x"*100000
    if mode == "wrong-version": files[root+"/METADATA"] = b"Name: fixture\nVersion: 2.0\n"
    if mode == "wrong-tag": files[root+"/WHEEL"] = files[root+"/WHEEL"].replace(b"py3-none-any", b"py2-none-any")
    stream = io.StringIO(newline=""); writer = csv.writer(stream, lineterminator="\n")
    for name, data in files.items():
        value = base64.urlsafe_b64encode(bytes.fromhex(audit.sha(data))).rstrip(b"=").decode()
        if mode == "record-hash" and name.endswith("__init__.py"): value = "wrong"
        if mode == "unlisted" and name.endswith("__init__.py"): continue
        writer.writerow([name, "sha256="+value, len(data)])
    writer.writerow([root+"/RECORD", "", ""])
    files[root+"/RECORD"] = stream.getvalue().encode()
    path = tmp_path/"fixture-1.0-py3-none-any.whl"
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            if mode == "symlink" and name.endswith("__init__.py"):
                info = zipfile.ZipInfo(name); info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, data)
            else: archive.writestr(name, data)
        if mode == "duplicate":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr(root+"/METADATA", files[root+"/METADATA"])
    artifact = {"filename": path.name, "package": "fixture", "version": "1.0", "sha256": audit.file_sha(path), "bytes": path.stat().st_size}
    return path, artifact


def test_valid_static_fixture_is_read_not_imported(tmp_path):
    path, artifact = fixture_wheel(tmp_path)
    result, native_payloads, _ = audit.inspect_wheel(path, artifact)
    assert result["status"] == "PASS" and result["record_checked_files"] == 3
    assert not native_payloads and result["record_authenticity"] == "NOT_A_SIGNATURE"


@pytest.mark.parametrize("mode", ["traversal", "case-collision", "prefix-collision", "bomb", "wrong-version", "wrong-tag", "record-hash", "unlisted", "symlink", "duplicate"])
def test_unsafe_or_inconsistent_archives_rejected(tmp_path, mode):
    path, artifact = fixture_wheel(tmp_path, mode)
    with pytest.raises((audit.Rejected, zipfile.BadZipFile)): audit.inspect_wheel(path, artifact)


@pytest.mark.parametrize("name", ["/absolute", "C:/drive", "a\\b", "a/../b", "nul.txt", "x\x00y", "a./b", "a//b"])
def test_zip_name_boundaries(name):
    with pytest.raises(audit.Rejected): audit.safe_name(name)


@pytest.mark.parametrize("url", ["http://files.pythonhosted.org/a.whl", "https://user:password@files.pythonhosted.org/a.whl", "https://evil.invalid/a.whl", "https://files.pythonhosted.org:444/a.whl", "https://files.pythonhosted.org/a.whl?token=x", "https://files.pythonhosted.org/b.whl"])
def test_network_origin_and_filename_fail_closed(url):
    with pytest.raises(audit.Rejected): audit.validate_url(url, "files.pythonhosted.org", "a.whl")


def test_redirect_rejected_before_following():
    handler = audit.StrictRedirects("files.pythonhosted.org", "a.whl")
    with pytest.raises(audit.Rejected): handler.redirect_request(None, None, 302, "", {}, "https://evil.invalid/a.whl")
    assert not handler.chain


def test_frozen_user_allowlist_is_exact():
    root = Path(__file__).resolve().parents[1]
    artifacts, digest = audit.frozen_inventory(root)
    assert len(artifacts) == 5 and len(digest) == 64
    assert {a["filename"]:a["sha256"] for a in artifacts} == audit.ALLOWLIST


def test_no_clobber_evidence_and_publication(tmp_path):
    target, part = tmp_path/"target", tmp_path/"owned.part"
    audit.write_once(target, b"preserved")
    with pytest.raises(FileExistsError): audit.write_once(target, b"replacement")
    part.write_bytes(b"other")
    with pytest.raises(FileExistsError): audit.promote_no_replace(part, target)
    assert target.read_bytes() == b"preserved" and part.read_bytes() == b"other"


def test_unapproved_artifact_rejected_before_network(tmp_path, monkeypatch):
    _, artifact = fixture_wheel(tmp_path)
    monkeypatch.setattr(audit, "open_https", lambda *args, **kwargs: pytest.fail("No network allowed"))
    with pytest.raises(audit.Rejected): audit.acquire_one(artifact, {}, tmp_path)


def test_publication_metadata_mismatch_is_not_substituted():
    root = Path(__file__).resolve().parents[1]; artifacts, _ = audit.frozen_inventory(root)
    item = artifacts[0]
    metadata = {"info":{"name":item["package"],"version":item["version"]},"urls":[{"filename":item["filename"],"digests":{"sha256":"0"*64},"size":item["bytes"],"packagetype":"bdist_wheel","yanked":False,"url":item["url"]}]}
    with pytest.raises(audit.Rejected): audit.validate_published(item, metadata)


@pytest.mark.parametrize("payload", [b"MZ", b"\x7fELF", b"not native"])
def test_native_parser_is_bounded_and_never_loads(payload):
    result = native.inspect_native(payload)
    assert result["parse_status"] == "NOT_AUDITED"


def test_native_literals_are_not_runtime_proof():
    result = native.inspect_native(b"OpenSSL 4.0.3\0 pyo3-0.29.2\0 ffi_prep_cif\0")
    assert result["openssl_version_literals"] == ["OpenSSL 4.0.3"]
    assert result["crate_version_literals"] == ["pyo3-0.29.2"]
    assert "ffi_prep_cif" in result["reference_markers"]
    assert result["interpretation"].endswith("NOT_COMPLETE_COMPONENT_OR_RUNTIME_PROOF")
