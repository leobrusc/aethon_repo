"""SRC2-REV-04 synthetic proof-binding regression.

Reconstructed tests from the unpublished independent review's reported
counterexample. These are not copies of the inaccessible Windows worktree.
No native I/O, external witness service, or inference is performed.
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import pytest

MODEL = Path(__file__).parents[1] / "docs/security/src02-contract-remediation-v1/models/safety_model.py"
SPEC = importlib.util.spec_from_file_location("src02_witness_proof_model", MODEL)
assert SPEC is not None and SPEC.loader is not None
model = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = model
SPEC.loader.exec_module(model)


def checkpoints():
    history = model.complete_history(witness_required=True)
    verified = next(s for s in history if s.witness_query is model.WitnessQuery.VALIDATED)
    reconciled = next(
        s for s in history if s.witness_query is model.WitnessQuery.RECONCILED
        and "witness_reconcile" in s.history
    )
    committed = history[-1]
    assert model.classify(committed) is model.Outcome.COMMITTED
    return verified, reconciled, committed


@pytest.mark.parametrize(("field", "value"), [
    ("witness_response_signature_valid", False),
    ("witness_response_fresh", False),
    ("witness_response_revocation_valid", False),
    ("witness_response_signer", "forged-signer"),
    ("witness_identity", "forged-witness"),
    ("witness_response_run_id", "foreign-run"),
    ("witness_response_operation_id", "foreign-operation"),
    ("witness_response_policy_epoch", 99),
    ("witness_response_revocation_epoch", 99),
    ("witness_response_sequence", 99),
    ("witness_response_head", "foreign-head"),
    ("witness_response_committed_op", "foreign-operation"),
    ("witness_query_run_id", "foreign-request-run"),
    ("witness_query_operation_id", "foreign-request-operation"),
    ("witness_query_policy_epoch", 99),
    ("witness_query_revocation_epoch", 99),
])
@pytest.mark.parametrize("checkpoint", [0, 1, 2])
def test_tampered_evidence_rejected_after_verification_reconciliation_and_ack(
    field, value, checkpoint
):
    original = checkpoints()[checkpoint]
    corrupted = replace(original, **{field: value})
    with pytest.raises(model.Reject, match="witness"):
        model.classify(corrupted)
    if checkpoint == 0:
        with pytest.raises(model.Reject, match="witness"):
            model.apply(corrupted, "witness_reconcile")


def test_tampering_after_authentication_cannot_pass_verification():
    s = next(
        x for x in model.complete_history()
        if x.witness_query is model.WitnessQuery.AUTHENTICATED
    )
    with pytest.raises(model.Reject, match="witness"):
        model.apply(replace(s, witness_response_signature_valid=False), "witness_verify")
    with pytest.raises(model.Reject, match="witness"):
        model.apply(replace(s, witness_response_fresh=False), "witness_verify")


def test_a_valid_verified_response_reconciles_and_commits():
    verified, reconciled, committed = checkpoints()
    assert verified.witness_verified_binding is not None
    assert reconciled.witness_verified_binding == verified.witness_verified_binding
    assert committed.witness_verified_binding == verified.witness_verified_binding
    assert model.classify(committed) is model.Outcome.COMMITTED


def test_verified_binding_cannot_be_replayed_across_different_proof():
    _, reconciled, committed = checkpoints()
    with pytest.raises(model.Reject, match="witness"):
        model.classify(replace(committed, witness_verified_binding=None))
    with pytest.raises(model.Reject, match="witness"):
        model.classify(replace(reconciled, witness_verified_binding=("stale",)))


def test_subsequent_witness_unavailability_does_not_retroactively_erase_commit():
    committed = checkpoints()[-1]
    historical = replace(committed, witness_available=False)
    assert model.classify(historical) is model.Outcome.COMMITTED


def test_non_witness_policy_keeps_legitimate_commit():
    final = model.complete_history(witness_required=False)[-1]
    assert final.witness_verified_binding is None
    assert model.classify(final) is model.Outcome.COMMITTED
