"""Independent negative audit of the frozen witness-policy boundary.

This file intentionally asserts secure behavior against the unchanged PR #38
model. Expected failures are forensic findings, not fixed-code regressions.
No external I/O or native backend is exercised.
"""
from __future__ import annotations

from dataclasses import replace
import importlib.util
from pathlib import Path
import sys

import pytest

MODEL_PATH = Path(__file__).parents[1] / "docs/security/src02-contract-remediation-v1/models/safety_model.py"
SPEC = importlib.util.spec_from_file_location("src02_witness_policy_audit_model", MODEL_PATH)
assert SPEC is not None and SPEC.loader is not None
model = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = model
SPEC.loader.exec_module(model)


def test_witness_requirement_is_immutable_after_no_witness_commit():
    """A completed operation must not gain or lose witness policy silently."""
    finished = model.complete_history(witness_required=False)[-1]
    assert model.classify(finished) is model.Outcome.COMMITTED
    with pytest.raises(model.Reject, match="witness|policy"):
        model.classify(replace(finished, witness_required=True))


def test_committed_witness_protected_operation_cannot_downgrade_policy():
    """A signed witness claim cannot be discarded by changing the policy flag."""
    finished = model.complete_history(witness_required=True)[-1]
    assert model.classify(finished) is model.Outcome.COMMITTED
    downgraded = replace(
        finished,
        witness_required=False,
        witness_query=model.WitnessQuery.NONE,
        witness_ack=False,
        witness_response_valid=False,
        witness_verified_binding=None,
    )
    with pytest.raises(model.Reject, match="witness|policy"):
        model.classify(downgraded)


def test_legitimate_witness_policy_remains_valid_without_mutations():
    assert model.classify(model.complete_history(True)[-1]) is model.Outcome.COMMITTED
    assert model.classify(model.complete_history(False)[-1]) is model.Outcome.COMMITTED
