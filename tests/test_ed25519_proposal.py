"""Proposal/denial tests only; no approved provider and no new production adapter."""
import base64
import copy
import json
import os
from pathlib import Path
import subprocess

import pytest

from aethon.pilot_governance import OpenSSLVerifier, ReceiptAuthority, canonical, digest, key_identity, verify_gates
from ed25519_contract_cases import (PREFIX, acceptance_cases, illustrative_boolean_bridge,
                                     pem, public_vectors, run_approved_provider_acceptance)
from test_pilot_collector import deny_network, setup_run

__all__ = ["deny_network", "setup_run"]


def test_candidate_metadata_has_exact_unapproved_artifacts():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root/"docs/security/ed25519-v1/artifacts.json").read_text())
    assert data["classification"] == "DEPENDENCY_APPROVAL_REQUIRED"
    assert data["artifact_downloads"] is data["installs"] is data["lock_changes"] is False
    assert {(p["name"], p["version"]) for p in data["packages"]} == {("cryptography","50.0.2"),("cffi","2.1.1"),("pycparser","3.12")}
    assert len(data["artifacts"]) == 5
    assert all(len(a["sha256"]) == 64 and a["artifact_bytes"] == "NOT_DOWNLOADED_NOT_AUDITED" for a in data["artifacts"])


def test_public_vector_shapes_and_exact_spki_alias_identity():
    for vector in public_vectors():
        raw = bytes.fromhex(vector["public_key_hex"])
        assert len(raw) == 32 and len(bytes.fromhex(vector["signature_hex"])) == 64
        assert key_identity(pem(raw)) == key_identity(b"\n"+pem(raw)+b"\n") == digest(PREFIX+raw)


@pytest.mark.parametrize("der", [b"", PREFIX+b"x"*31, bytes.fromhex("302a300506032b6571032100")+b"x"*32, PREFIX+b"x"*33])
def test_current_key_identity_rejects_malformed_or_alternative_spki(der):
    key = b"-----BEGIN PUBLIC KEY-----\n"+base64.b64encode(der)+b"\n-----END PUBLIC KEY-----\n"
    with pytest.raises(ValueError): key_identity(key)


def test_prepared_provider_cases_are_not_claimed_executed():
    cases = list(acceptance_cases())
    assert len(cases) == 10 and len({case[0] for case in cases}) == 10
    assert sum(case[-1] == "VALID" for case in cases) == 2
    with pytest.raises(AssertionError): run_approved_provider_acceptance(lambda *args: "VALID")
    with pytest.raises(AssertionError): run_approved_provider_acceptance(lambda *args: "INVALID")
    with pytest.raises(RuntimeError, match="NOT_RUN"): run_approved_provider_acceptance(lambda *args: "UNSUPPORTED")


@pytest.mark.parametrize("result,expected", [("VALID",True),("INVALID",False)])
def test_test_only_bridge_is_explicit_not_string_truthiness(result, expected):
    assert illustrative_boolean_bridge(result) is expected


@pytest.mark.parametrize("result", [True,False,1,None,"approved",{"approved":True}])
def test_test_only_bridge_rejects_non_contract_results(result):
    with pytest.raises(ValueError): illustrative_boolean_bridge(result)


def test_test_only_bridge_blocks_unsupported():
    with pytest.raises(PermissionError): illustrative_boolean_bridge("UNSUPPORTED")


@pytest.mark.parametrize("signature_length", [0,63,64,65])
def test_disabled_production_backend_has_no_external_fallback(tmp_path, monkeypatch, signature_length):
    tool = tmp_path/"synthetic-never-executed-tool"; tool.write_bytes(b"synthetic")
    verifier = OpenSSLVerifier(str(tool), digest(tool.read_bytes()))
    def denied(*args, **kwargs): pytest.fail("External execution is forbidden")
    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(os, "system", denied)
    if signature_length != 64:
        assert verifier(b"untrusted", b"synthetic payload", b"x"*signature_length) is False
    else:
        with pytest.raises(PermissionError, match="execution disabled"):
            verifier(b"untrusted", b"synthetic payload", b"x"*64)


def test_shadow_provider_is_not_imported_by_disabled_backend(tmp_path, monkeypatch):
    marker = tmp_path/"must-not-exist"
    (tmp_path/"cryptography.py").write_text("from pathlib import Path\nPath("+repr(str(marker))+").write_text('synthetic shadow imported')\nraise RuntimeError('UNAPPROVED SHADOW PROVIDER')\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    tool = tmp_path/"synthetic-tool"; tool.write_bytes(b"synthetic")
    verifier = OpenSSLVerifier(str(tool), digest(tool.read_bytes()))
    with pytest.raises(PermissionError): verifier(b"key", b"payload", b"x"*64)
    assert not marker.exists()  # No claim of future runtime/import attestation.


def test_changed_runtime_tool_identity_still_denies(tmp_path):
    tool = tmp_path/"synthetic-tool"; tool.write_bytes(b"original")
    verifier = OpenSSLVerifier(str(tool), digest(tool.read_bytes()))
    tool.write_bytes(b"changed")
    with pytest.raises(PermissionError, match="identity changed"): verifier(b"key", b"payload", b"x"*64)


def test_canonical_bytes_are_exact_and_not_reserialized():
    value = {"z":False,"a":"\u00e9","items":[1, None]}
    assert canonical(value) == b'{"a":"\xc3\xa9","items":[1,null],"z":false}'
    assert canonical(dict(reversed(list(value.items())))) == canonical(value)
    with pytest.raises(ValueError): canonical({"x":float("nan")})


@pytest.mark.parametrize("attack", ["replay","policy","alias","approval-flag"])
def test_existing_receipt_controls_remain_required(setup_run, attack):
    f = setup_run; envelopes = copy.deepcopy(f["envelopes"]); subject = copy.deepcopy(f["subject"])
    if attack == "replay": subject["run_id"] = "foreign"
    if attack == "policy":
        f["policy_path"].write_bytes(b'{"schema":"aethon.trust-policy.v1","authorities":{}}')
        with pytest.raises(ValueError, match="Trust-anchor mismatch"):
            ReceiptAuthority(f["policy_path"], f["authority"].policy_sha256, [f["repo"]])
        return
    if attack == "alias":
        f["authority"].policy["authorities"]["review-b"] = copy.deepcopy(f["authority"].policy["authorities"]["review-a"])
        envelopes["semantic_review"]["signatures"][1]["signature_base64"] = envelopes["semantic_review"]["signatures"][0]["signature_base64"]
    if attack == "approval-flag": envelopes["execution_authorization"] = {"approved":True}
    assert verify_gates(f["authority"], envelopes, subject, f["technical"])["classification"] == "PILOT_BLOCKED"
