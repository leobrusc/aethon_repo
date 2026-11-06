"""Synthetic attestation boundaries; no wheels, network, keys or tools invoked."""
import base64
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from inspect_ed25519_quarantine import b64, dsse_pae, verify_statement_subject


def test_pae_preserves_exact_bytes():
    payload = b'{"unicode":"\xc3\xa9", "space": true}\n'
    assert dsse_pae(payload) == (b"DSSEv1 28 application/vnd.in-toto+json "
                                + str(len(payload)).encode() + b" " + payload)


@pytest.mark.parametrize("change", ["filename", "digest", "duplicate", "type", "missing"])
def test_subject_rejects_substitution(change):
    artifact = {"filename": "synthetic.whl", "sha256": "a" * 64}
    obj = {"_type": "https://in-toto.io/Statement/v1", "subject": [
        {"name": artifact["filename"], "digest": {"sha256": artifact["sha256"]}}]}
    assert verify_statement_subject(json.dumps(obj).encode(), artifact)
    if change == "filename": obj["subject"][0]["name"] = "other.whl"
    if change == "digest": obj["subject"][0]["digest"]["sha256"] = "b" * 64
    if change == "duplicate": obj["subject"] *= 2
    if change == "type": obj["_type"] = "other"
    if change == "missing": obj.pop("subject")
    assert not verify_statement_subject(json.dumps(obj).encode(), artifact)


def test_base64_rejects_ignored_characters():
    assert b64(base64.b64encode(b"synthetic")) == b"synthetic"
    with pytest.raises(ValueError): b64("c3ludGhldGlj!")


def test_import_has_no_acquisition_or_execution_side_effects(monkeypatch):
    import inspect_ed25519_quarantine as audit
    monkeypatch.setattr(audit.subprocess, "run", lambda *a, **kw: pytest.fail("external execution"))
    monkeypatch.setattr(audit, "metadata_bytes", lambda *a, **kw: pytest.fail("network"))
    assert audit.dsse_pae(b"").endswith(b" 0 ")
