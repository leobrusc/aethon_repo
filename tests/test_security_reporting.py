"""Exercise transitive alias normalization and lock coverage without network."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


def module(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_aliases_merge_transitively_without_dropping_ids():
    report = module("security_matrix")
    rows = [{"id": "PYSEC-a", "aliases": ["GHSA-a"]},
            {"id": "CVE-a", "aliases": ["GHSA-a", "GHSA-b"]},
            {"id": "PYSEC-b", "aliases": ["GHSA-b"]}]
    groups = report.components(rows)
    assert len(groups["PYSEC-a"]) == 5
    assert groups["PYSEC-a"] == groups["PYSEC-b"]
    assert report.canonical(groups["PYSEC-b"]) == "CVE-a"


def test_torch_direct_artifact_has_explicit_upstream_coverage(tmp_path):
    audit = module("audit_security_environment")
    path = tmp_path / "cpu.lock"
    path.write_text("numpy==2.2.6 --hash=sha256:abc\ntorch @ https://download.pytorch.org/example.whl --hash=sha256:expected\n")
    packages = audit.locked_packages(path, {"url": "https://download.pytorch.org/example.whl",
                                          "sha256": "expected", "version": "2.15.0+cpu"})
    assert packages == {"numpy": "2.2.6", "torch": "2.15.0+cpu"}


def test_scanner_skip_is_not_a_pass(tmp_path, monkeypatch):
    audit = module("audit_security_environment")
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    destination = tmp_path / "native.json"
    def run(*args, **kwargs):
        destination.write_text(json.dumps({"dependencies": [{"name": "unknown-build", "skip_reason": "not catalogued"}]}))
        return SimpleNamespace(returncode=1, stdout="", stderr="unknown build")
    monkeypatch.setattr(audit.subprocess, "run", run)
    assert audit.scan(None, destination)["status"] == "NOT_AUDITED"


def test_scanner_error_cannot_pass(tmp_path, monkeypatch):
    audit = module("audit_security_environment")
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=2, stdout="", stderr="error"))
    assert audit.scan(None, tmp_path / "error.json")["status"] == "FAIL"
