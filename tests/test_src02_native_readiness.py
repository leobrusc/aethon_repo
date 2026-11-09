"""Synthetic negative checks for the SRC-02 design-only readiness manifest.

These tests never open a native storage root, provision a witness, or authorize a pilot.
"""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts/check_src02_native_readiness.py"
SPEC = importlib.util.spec_from_file_location("src02_native_readiness_checker", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


@pytest.fixture
def proposal():
    return checker.load_manifest()


def test_design_manifest_stays_blocked(proposal):
    result = checker.assess(proposal)
    assert result["status"] == "DESIGN_ONLY_BLOCKED"
    assert result["authorized"] is False
    assert result["pilot_execution"] is False
    assert result["native_execution"] is False
    assert result["issues"] == []


@pytest.mark.parametrize("field,value", [
    ("root_bootstrap", "APPROVED"),
    ("freshness_witness", "APPROVED"),
    ("linux_native_profile", "READY"),
    ("lease_commit_authority", "APPROVED"),
])
def test_candidate_cannot_self_approve(proposal, field, value):
    altered = copy.deepcopy(proposal)
    altered["decisions"][field]["status"] = value
    assert checker.assess(altered)["status"] == "INVALID_FAIL_CLOSED"


@pytest.mark.parametrize("field", sorted(checker.GATES))
def test_none_of_eight_operational_gates_can_self_approve(proposal, field):
    altered = copy.deepcopy(proposal)
    altered["operational"]["gates"][field] = "PASS"
    assert checker.assess(altered)["status"] == "INVALID_FAIL_CLOSED"


@pytest.mark.parametrize("field,approval", [
    ("src02", "AUTHORIZED"),
    ("pilot", "PILOT_READY"),
    ("dependencies", "APPROVED"),
])
def test_operational_status_cannot_be_promoted(proposal, field, approval):
    altered = copy.deepcopy(proposal)
    altered["operational"][field] = approval
    assert checker.assess(altered)["status"] == "INVALID_FAIL_CLOSED"


@pytest.mark.parametrize("key,value", [
    ("native_backend", "IMPLEMENTED"),
    ("root", "PROVISIONED"),
    ("witness", "PROVISIONED"),
    ("gpu_inference", "RUN"),
])
def test_native_assets_cannot_be_claimed_in_design_phase(proposal, key, value):
    altered = copy.deepcopy(proposal)
    altered["assets"][key] = value
    assert checker.assess(altered)["status"] == "INVALID_FAIL_CLOSED"


def test_forged_evidence_cannot_promote_readiness(proposal):
    altered = copy.deepcopy(proposal)
    altered["evidence"]["signed_bootstrap_receipt"] = "PASS"
    assert checker.assess(altered)["authorized"] is False
    assert checker.assess(altered)["status"] == "INVALID_FAIL_CLOSED"


def test_missing_or_extra_gate_fails_closed(proposal):
    altered = copy.deepcopy(proposal)
    altered["operational"]["gates"].pop("private_storage")
    assert checker.assess(altered)["status"] == "INVALID_FAIL_CLOSED"
    altered["operational"]["gates"]["private_storage"] = "PENDING"
    altered["operational"]["gates"]["other"] = "PENDING"
    assert checker.assess(altered)["status"] == "INVALID_FAIL_CLOSED"


def test_forged_baseline_or_unknown_key_fails_closed(proposal):
    altered = copy.deepcopy(proposal)
    altered["baseline"]["head_sha"] = "unknown"
    assert checker.assess(altered)["status"] == "INVALID_FAIL_CLOSED"
    altered = copy.deepcopy(proposal)
    altered["authorizing_issuer"] = "self"
    assert checker.assess(altered)["status"] == "INVALID_FAIL_CLOSED"


def test_duplicate_json_keys_rejected(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema":"v1","schema":"v2"}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        checker.load_manifest(path)


def test_valid_design_remains_non_authorizing(proposal):
    verdict = checker.assess(proposal)
    assert verdict["status"] == "DESIGN_ONLY_BLOCKED"
    assert not any((verdict["authorized"], verdict["native_execution"], verdict["pilot_execution"]))
