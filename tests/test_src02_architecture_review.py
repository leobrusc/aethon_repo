"""Independent design-only audit: SRC-02 ADRs and atomic-fencing counterexample.

The intentionally unsafe two-step algorithm is a *synthetic illustration*, not
a runtime exploit or a test of Linux locks, renameat2 or filesystem durability.
Nothing in this module authorizes or provisions a native backend.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/security/src02-native-architecture-review-v1"
DESIGN = ROOT / "docs/security/src02-native-readiness-v1"

SCRIPT = ROOT / "scripts/check_src02_native_readiness.py"
SPEC = importlib.util.spec_from_file_location("src02_design_review_guard", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


@pytest.fixture
def findings():
    return json.loads((REVIEW / "ARCHITECTURE_FINDINGS.json").read_text(encoding="utf-8"))


def test_review_binds_exact_original_pr42_head(findings):
    assert findings["reviewed"]["pr"] == 42
    assert findings["reviewed"]["head"] == "bf28e2f93bf94f71dda995505813cdc0d0537fb7"
    assert findings["reviewed"]["scope"] == "ADVERSARIAL_TECHNICAL_REVIEW_NOT_ORGANIZATIONAL_SIGNOFF"


def test_review_does_not_self_authorize(findings):
    assert findings["disposition"] == "REVIEW_COMPLETE_WITH_BLOCKERS"
    assert findings["native_implementation"] == "NOT_AUTHORIZED"
    assert findings["linux_fixture_prototype"] == "NOT_AUTHORIZED"
    assert findings["human_independent_signoff"] == "PENDING"
    assert findings["preserved"]["eight_gates"] == "PENDING"


def test_all_critical_architecture_decisions_remain_open(findings):
    issues = {entry["id"]: entry for entry in findings["findings"]}
    assert set(issues) == {f"ARCH-REV-{i:02d}" for i in range(1, 7)}
    assert issues["ARCH-REV-03"]["severity"] == "CRITICAL"
    assert issues["ARCH-REV-03"]["status"] == "REMEDIATION_REQUIRED"
    for key in ("ARCH-REV-01", "ARCH-REV-02", "ARCH-REV-04", "ARCH-REV-05"):
        assert issues[key]["status"] == "OPEN_DECISION"
        assert issues[key]["required_evidence"]


@pytest.mark.parametrize(
    "field,attempt",
    [
        ("src02", "AUTHORIZED"),
        ("dependencies", "APPROVED"),
        ("pilot", "PILOT_READY"),
    ],
)
def test_design_linter_cannot_be_overridden_by_review_claim(field, attempt):
    proposal = checker.load_manifest()
    compromised = copy.deepcopy(proposal)
    compromised["operational"][field] = attempt
    assert checker.assess(compromised)["status"] == "INVALID_FAIL_CLOSED"
    assert checker.assess(compromised)["authorized"] is False


def test_review_findings_cannot_be_substituted_for_approval_evidence():
    proposal = checker.load_manifest()
    compromised = copy.deepcopy(proposal)
    compromised["evidence"]["native_contract_review"] = "PASS"
    assert checker.assess(compromised)["status"] == "INVALID_FAIL_CLOSED"


class UnsafeHead:
    """Toy check-then-publish: no atomically serialized transfer/publish."""

    def __init__(self):
        self.epoch = 7
        self.head = "h0"

    def check(self, epoch):
        return epoch == self.epoch

    def publish_without_recheck(self, head):
        self.head = head


class SerializedHead:
    """Toy single-authority transition; not a filesystem implementation."""

    def __init__(self):
        self.epoch = 7
        self.head = "h0"

    def transfer(self, expected_epoch, new_epoch):
        if self.epoch != expected_epoch or new_epoch <= expected_epoch:
            return False
        self.epoch = new_epoch
        return True

    def publish(self, expected_epoch, expected_head, new_head):
        if self.epoch != expected_epoch or self.head != expected_head:
            return False
        self.head = new_head
        return True


def test_split_check_then_publish_admits_stale_writer_counterexample():
    unsafe = UnsafeHead()
    writer_a_approved_before_pause = unsafe.check(7)
    assert writer_a_approved_before_pause
    unsafe.epoch = 8  # successor takes lease while A is paused
    unsafe.publish_without_recheck("unauthorized-old-writer")
    assert unsafe.head == "unauthorized-old-writer"


def test_single_authority_toy_rejects_stale_writer_without_head_change():
    safe = SerializedHead()
    assert safe.transfer(7, 8)
    assert not safe.publish(7, "h0", "unauthorized-old-writer")
    assert safe.head == "h0"
    assert safe.publish(8, "h0", "h1")
    assert safe.head == "h1"


def test_review_documents_are_separate_from_base_adr_files():
    expected = (
        "INDEPENDENT_ARCHITECTURE_REVIEW.md",
        "ROOT_BOOTSTRAP_REVIEW.md",
        "WITNESS_INDEPENDENCE_REVIEW.md",
        "LINUX_PROFILE_REVIEW.md",
        "COMMIT_FENCING_AUTHORITY_REVIEW.md",
        "IMPLEMENTATION_GATE_AND_FINAL_DISPOSITION.md",
    )
    for filename in expected:
        body = (REVIEW / filename).read_text(encoding="utf-8")
        assert len(body) > 100
        assert "NOT" in body or "PENDING" in body or "BLOCK" in body
    for filename in (
        "ADR-001_ROOT_BOOTSTRAP.md",
        "ADR-002_FRESHNESS_WITNESS.md",
        "ADR-003_LINUX_PROFILE.md",
    ):
        assert (DESIGN / filename).is_file()
