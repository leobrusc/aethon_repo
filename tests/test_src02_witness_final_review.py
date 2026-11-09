"""Final read-only adversarial audit of the PR #40 abstract witness safety boundary.

Separate review branch. Positive assertions require rejection of altered inputs;
the historical intentionally-failing PR #39 remains untouched.
No native filesystem, provider call or remote witness is exercised.
"""
from __future__ import annotations

from dataclasses import replace
import importlib.util
from pathlib import Path
import sys

import pytest

PATH = Path(__file__).parents[1] / "docs/security/src02-contract-remediation-v1/models/safety_model.py"
SPEC = importlib.util.spec_from_file_location("src02_final_witness_review_model", PATH)
assert SPEC is not None and SPEC.loader is not None
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)


def _stages():
    history = m.complete_history(True)
    verified = next(x for x in history if x.witness_query is m.WitnessQuery.VALIDATED)
    reconciled = next(x for x in history if "witness_reconcile" in x.history)
    committed = history[-1]
    assert m.classify(committed) is m.Outcome.COMMITTED
    return verified, reconciled, committed


@pytest.mark.parametrize("required", [False, True])
def test_legitimate_terminal_outcomes_have_original_witness_policy(required):
    s = m.complete_history(required)[-1]
    assert s.witness_required is required
    assert s.bound_witness_required is required
    assert m.classify(s) is m.Outcome.COMMITTED


@pytest.mark.parametrize("stage", range(3))
def test_witness_downgrade_and_proof_removal_are_rejected_at_every_stage(stage):
    state = _stages()[stage]
    modified = replace(
        state, witness_required=False,
        witness_ack=False, witness_query=m.WitnessQuery.NONE,
        witness_response_valid=False, witness_verified_binding=None,
    )
    with pytest.raises(m.Reject, match="witness policy"):
        m.classify(modified)


@pytest.mark.parametrize("stage", range(3))
def test_witness_policy_frozen_even_when_witness_proof_untouched(stage):
    state = _stages()[stage]
    with pytest.raises(m.Reject, match="witness policy"):
        m.classify(replace(state, witness_required=False))


def test_no_witness_history_cannot_be_relabelled_as_witness_required():
    state = m.complete_history(False)[-1]
    with pytest.raises(m.Reject, match="witness policy"):
        m.classify(replace(state, witness_required=True))


@pytest.mark.parametrize("field,corruption", [
    ("witness_response_signature_valid", False),
    ("witness_response_fresh", False),
    ("witness_response_revocation_valid", False),
    ("witness_response_signer", "different-signer"),
    ("witness_identity", "different-witness"),
    ("witness_response_run_id", "different-run"),
    ("witness_response_operation_id", "different-operation"),
    ("witness_response_policy_epoch", -1),
    ("witness_response_revocation_epoch", -1),
    ("witness_response_sequence", 999),
    ("witness_response_head", "different-head"),
    ("witness_response_committed_op", "different-operation"),
    ("witness_query_run_id", "different-query-run"),
    ("witness_query_operation_id", "different-query-operation"),
    ("witness_query_policy_epoch", -1),
    ("witness_query_revocation_epoch", -1),
    ("policy_epoch", 999),
    ("revocation_epoch", 999),
])
@pytest.mark.parametrize("stage", range(3))
def test_single_claim_mutation_is_rejected_after_verification(field,corruption,stage):
    state = _stages()[stage]
    with pytest.raises(m.Reject):
        m.classify(replace(state, **{field: corruption}))


@pytest.mark.parametrize("stage", range(3))
def test_proof_binding_must_remain_present(stage):
    state = _stages()[stage]
    assert state.witness_verified_binding is not None
    with pytest.raises(m.Reject, match="witness"):
        m.classify(replace(state, witness_verified_binding=None))


def test_valid_historical_ack_survives_subsequent_witness_service_outage():
    state = _stages()[-1]
    assert m.classify(replace(state, witness_available=False)) is m.Outcome.COMMITTED


def test_forged_unavailable_witness_cannot_make_reconciliation_succeed():
    state = _stages()[0]
    with pytest.raises(m.Reject):
        m.apply(replace(state, witness_response_valid=False), "witness_reconcile")


def test_stale_lease_writer_and_pre_dispatch_inference_remain_blocked():
    s = m.State()
    s = m.apply(s, "prepare_intent")
    s = m.apply(s, "durable_intent")
    with pytest.raises(m.Reject):
        m.apply(s, "persist_object")
    assert m.classify_snapshot(intent=True, acknowledged=True,
                               head_durable=True, object_durable=False,
                               journal_durable=False) is m.Outcome.REJECTED
    s = m.complete_history(False)[-1]
    assert m.classify(s) is m.Outcome.COMMITTED


def test_explorer_retains_bounded_history_congruence():
    counts = m.explore(max_depth=6, max_states=100000)
    assert counts["frontier_mismatches"] == 0
    assert counts["max_depth"] == 6
