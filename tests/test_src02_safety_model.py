"""Synthetic contract tests for the abstract SRC-02 relation only."""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import pytest

MODEL_PATH = Path(__file__).parents[1] / "docs/security/src02-contract-remediation-v1/models/safety_model.py"
SPEC = importlib.util.spec_from_file_location("src02_safety_model", MODEL_PATH)
assert SPEC and SPEC.loader
model = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = model
SPEC.loader.exec_module(model)


def start_intent(witness_required=True):
    s = model.State(witness_required=witness_required)
    s = model.apply(s, "prepare_intent")
    return model.apply(s, "durable_intent")


def authorized_dispatch(s):
    s = model.apply(s, "authorize_dispatch", op=s.operation_id, run_id=s.run_id,
                    slot_id=s.slot_id, manifest_digest=s.manifest_digest,
                    config_digest=s.config_digest)
    return model.apply(s, "mark_dispatch", op=s.operation_id)


def observe(s, payload=b"synthetic generated continuation"):
    return model.apply(s, "response_observed", response=payload,
                       run_id=s.run_id, slot_id=s.slot_id, op=s.operation_id,
                       manifest_digest=s.manifest_digest, config_digest=s.config_digest)


def ready_for_publish(witness_required=True):
    s = authorized_dispatch(start_intent(witness_required))
    s = observe(s)
    for action in ("verify_response", "response_durable", "persist_object", "journal_durable"):
        s = model.apply(s, action)
    return s


def prepared_publish(s, writer=None):
    writer = writer or s.holder
    s = model.apply(s, "prepare_publish", writer=writer, lease_id=s.lease_id,
                    epoch=s.epoch, authority_id=s.authority_id)
    return s, s.prepared_publications[-1].token_id


def local_head(witness_required=True):
    s = ready_for_publish(witness_required)
    s, token = prepared_publish(s)
    s = model.apply(s, "publish", token_id=token)
    return model.apply(s, "head_durable")


def witness_proof(s, mode="next"):
    s = model.apply(s, "witness_query")
    s = model.apply(s, "witness_response", mode=mode)
    s = model.apply(s, "witness_authenticate")
    s = model.apply(s, "witness_verify")
    return model.apply(s, "witness_reconcile")


def test_pr36_pre_dispatch_response_less_commit_trace_is_rejected():
    s = model.apply(model.State(), "prepare_intent")
    s = model.apply(s, "durable_intent")
    with pytest.raises(model.Reject, match="durable observed response"):
        model.apply(s, "persist_object")
    assert not s.object_durable and s.sequence == 0 and not s.ack


@pytest.mark.parametrize("change", [
    {"dispatch_marker_durable": False},
    {"response_observed": False},
    {"response_verified": False},
    {"response_durable": False},
    {"object_durable": False},
    {"journal_durable": False},
    {"head_durable": False},
])
def test_no_committed_snapshot_without_each_provenance_or_durability_gate(change):
    committed = model.complete_history(True)[-1]
    with pytest.raises(model.Reject):
        model.classify(replace(committed, **change))


def test_response_is_bound_to_run_slot_operation_manifest_and_config():
    s = authorized_dispatch(start_intent(False))
    with pytest.raises(model.Reject, match="run/slot/config"):
        model.apply(s, "response_observed", response=b"r", run_id="other",
                    slot_id=s.slot_id, op=s.operation_id,
                    manifest_digest=s.manifest_digest, config_digest=s.config_digest)
    with pytest.raises(model.Reject, match="run/slot/config"):
        model.apply(s, "response_observed", response=b"r", run_id=s.run_id,
                    slot_id="other-slot", op=s.operation_id,
                    manifest_digest=s.manifest_digest, config_digest=s.config_digest)
    with pytest.raises(model.Reject, match="run/slot/config"):
        model.apply(s, "response_observed", response=b"r", run_id=s.run_id,
                    slot_id=s.slot_id, op=s.operation_id,
                    manifest_digest=s.manifest_digest, config_digest="other-config")
    with pytest.raises(model.Reject, match="run/slot/config"):
        model.apply(s, "response_observed", response=b"r", run_id=s.run_id,
                    slot_id=s.slot_id, op="other-operation",
                    manifest_digest=s.manifest_digest, config_digest=s.config_digest)
    with pytest.raises(model.Reject, match="run/slot/config"):
        model.apply(s, "response_observed", response=b"r", run_id=s.run_id,
                    slot_id=s.slot_id, op=s.operation_id,
                    manifest_digest="other-manifest", config_digest=s.config_digest)
    with pytest.raises(model.Reject, match="exact dispatched"):
        model.apply(s, "response_observed", response=b"", run_id=s.run_id,
                    slot_id=s.slot_id, op=s.operation_id,
                    manifest_digest=s.manifest_digest, config_digest=s.config_digest)


def test_digest_tampering_and_operation_identity_change_are_rejected():
    s = ready_for_publish(False)
    with pytest.raises(model.Reject, match="response digest mismatch"):
        model.validate(replace(s, response_digest="0" * 64))
    with pytest.raises(model.Reject, match="response digest mismatch"):
        model.validate(replace(s, response_bytes=b"altered continuation"))
    with pytest.raises(model.Reject, match="binding changed"):
        model.validate(replace(s, slot_id="different-slot"))
    with pytest.raises(model.Reject, match="binding changed"):
        model.validate(replace(s, config_digest="different-config"))


def test_durable_inference_commit_is_accepted_with_and_without_witness_profile():
    assert model.classify(model.complete_history(True)[-1]) is model.Outcome.COMMITTED
    assert model.classify(model.complete_history(False)[-1]) is model.Outcome.COMMITTED


def test_ack_is_rejected_without_authenticated_current_witness_proof():
    committed = model.complete_history(True)[-1]
    for change in ({"witness_ack": False}, {"witness_response_valid": False},
                   {"witness_policy_epoch": 0}, {"witness_revocation_epoch": 9}):
        with pytest.raises(model.Reject):
            model.classify(replace(committed, **change))


def test_persistence_retry_is_idempotent_and_does_not_repeat_dispatch():
    s = ready_for_publish(False)
    dispatches = s.dispatch_count
    retried = model.apply(s, "persist_retry")
    assert retried.persisted == s.persisted
    assert retried.response_digest == s.response_digest
    assert retried.dispatch_count == dispatches == 1
    with pytest.raises(model.Reject, match="different response bytes"):
        model.apply(retried, "persist_conflicting_bytes")


def test_crash_after_dispatch_without_durable_response_is_unknown_and_not_retried():
    s = authorized_dispatch(start_intent(False))
    crashed = model.apply(s, "crash")
    assert crashed.infer is model.Infer.INTERRUPTED_UNKNOWN
    assert crashed.recovery_blocked
    recovered = model.apply(crashed, "recover")
    assert recovered.infer is model.Infer.INTERRUPTED_UNKNOWN
    assert recovered.recovery_status is model.Recovery.BLOCKED
    with pytest.raises(model.Reject, match="recovery is required"):
        model.apply(recovered, "retry_inference")
    with pytest.raises(model.Reject, match="recovery is required"):
        model.apply(recovered, "mark_dispatch", op=recovered.operation_id)


def test_crash_before_dispatch_allows_only_same_bound_safe_retry():
    s = model.apply(start_intent(False), "crash")
    s = model.apply(s, "recover")
    assert not s.dispatch_marker_durable and s.dispatch_count == 0
    s = model.apply(s, "retry_inference")
    s = authorized_dispatch(s)
    assert s.dispatch_marker_durable and s.dispatch_count == 1


def test_administrative_operation_cannot_be_reinterpreted_as_inference():
    admin = model.State(operation=model.Operation.ADMINISTRATIVE)
    recorded = model.apply(admin, "admin_record")
    assert recorded.infer is model.Infer.NONE
    with pytest.raises(model.Reject, match="only an active inference"):
        model.apply(admin, "prepare_intent")
    with pytest.raises(model.Reject, match="dispatch authorization"):
        model.apply(admin, "authorize_dispatch", op=admin.operation_id,
                    run_id=admin.run_id, slot_id=admin.slot_id,
                    manifest_digest=admin.manifest_digest,
                    config_digest=admin.config_digest)
    with pytest.raises(model.Reject, match="administrative"):
        model.validate(replace(admin, response_bytes=b"pretend response"))


def test_persistence_operation_is_typed_and_requires_existing_durable_receipt():
    persistence = model.State(operation=model.Operation.PERSISTENCE,
                              source_operation_id="source-op",
                              source_response_digest="a" * 64,
                              source_response_durable=True)
    stored = model.apply(persistence, "persist_source")
    retried = model.apply(stored, "persist_retry")
    assert stored.object_durable and retried.persisted == stored.persisted
    assert stored.infer is model.Infer.NONE and not stored.dispatch_marker_durable
    invalid = replace(persistence, source_response_durable=False)
    with pytest.raises(model.Reject, match="existing durable source"):
        model.apply(invalid, "persist_source")


def test_witness_unavailable_query_cannot_reconcile_ack_or_resume():
    s = model.apply(local_head(True), "witness_prepare", op="op-fixture")
    s = model.apply(s, "witness_diverge", op="unavailable")
    queried = model.apply(s, "witness_query")
    assert queried.witness_query is model.WitnessQuery.UNAVAILABLE
    assert queried.recovery_blocked and queried.recovery_status is model.Recovery.BLOCKED
    assert not queried.witness_ack and not queried.ack
    with pytest.raises(model.Reject, match="no available authenticated"):
        model.apply(queried, "witness_response", mode="next")
    with pytest.raises(model.Reject, match="recovery is required"):
        model.apply(queried, "prepare_intent")
    with pytest.raises(model.Reject):
        model.apply(replace(queried, recovery_blocked=False,
                            recovery_status=model.Recovery.RECONCILED), "ack")


def test_authenticated_fresh_witness_proof_is_required_to_reconcile_unavailability():
    s = model.apply(local_head(True), "witness_prepare", op="op-fixture")
    s = model.apply(s, "witness_diverge", op="unavailable")
    s = model.apply(s, "witness_restore")
    s = model.apply(s, "witness_query")
    s = model.apply(s, "witness_response", mode="expected")
    with pytest.raises(model.Reject, match="has not been authenticated"):
        model.apply(s, "witness_verify")
    with pytest.raises(model.Reject, match="signature/identity"):
        model.apply(replace(s, witness_response_signature_valid=False), "witness_authenticate")
    authenticated = model.apply(s, "witness_authenticate")
    verified = model.apply(authenticated, "witness_verify")
    reconciled = model.apply(verified, "witness_reconcile")
    assert reconciled.witness_query is model.WitnessQuery.RECONCILED
    assert reconciled.witness_response_valid and not reconciled.recovery_blocked
    reconciled = model.apply(reconciled, "witness_advance")
    committed = model.apply(reconciled, "ack")
    assert model.classify(committed) is model.Outcome.COMMITTED


@pytest.mark.parametrize("mode", ["stale", "wrong_op", "wrong_run", "wrong_policy",
                                   "wrong_revocation", "invalid_signature", "stale_freshness",
                                   "ahead", "conflict"])
def test_stale_misbound_or_conflicting_witness_evidence_never_reconciles(mode):
    s = model.apply(local_head(True), "witness_prepare", op="op-fixture")
    s = model.apply(s, "witness_timeout_before_commit")
    s = model.apply(s, "witness_query")
    s = model.apply(s, "witness_response", mode=mode)
    if mode == "invalid_signature":
        with pytest.raises(model.Reject):
            model.apply(s, "witness_authenticate")
    else:
        authenticated = model.apply(s, "witness_authenticate")
        with pytest.raises(model.Reject):
            model.apply(authenticated, "witness_verify")
    assert s.recovery_blocked and not s.witness_ack


def test_timeout_after_remote_commit_queries_same_operation_before_ack():
    s = model.apply(local_head(True), "witness_prepare", op="op-fixture")
    s = model.apply(s, "witness_advance")
    s = model.apply(s, "witness_timeout_after_commit")
    assert s.recovery_blocked and not s.witness_ack
    s = witness_proof(s, "next")
    assert s.witness_ack and not s.recovery_blocked
    assert model.classify(model.apply(s, "ack")) is model.Outcome.COMMITTED


def test_lease_transfer_invalidates_prepared_stale_writer_atomically():
    s = ready_for_publish(False)
    s, token_a = prepared_publish(s, "A")
    unchanged = (s.sequence, s.head)
    s = model.apply(s, "transfer", writer="A", lease_id="lease-A-7",
                    epoch=7, authority_id="lease-authority-fixture")
    assert (s.holder, s.epoch, s.lease_id, s.lease_transfer_id) == (
        "B", 8, "lease-B-8", "transfer-1")
    with pytest.raises(model.Reject, match="stale lease identity"):
        model.apply(s, "publish", token_id=token_a)
    assert (s.sequence, s.head) == unchanged
    s, token_b = prepared_publish(s, "B")
    s = model.apply(s, "publish", token_id=token_b)
    assert s.publish_writer == "B" and s.publish_lease_id == "lease-B-8"
    s = model.apply(s, "head_durable")
    assert model.classify(model.apply(s, "ack")) is model.Outcome.COMMITTED


def test_two_conflicting_publications_cannot_both_commit_same_head():
    s = ready_for_publish(False)
    s, token_a = prepared_publish(s, "A")
    s = model.apply(s, "transfer", writer="A", lease_id="lease-A-7",
                    epoch=7, authority_id=s.authority_id)
    s, token_b = prepared_publish(s, "B")
    first = model.apply(s, "publish", token_id=token_b)
    assert (first.sequence, first.head) == (1, "h1:" + (first.response_digest or ""))
    with pytest.raises(model.Reject):
        model.apply(first, "publish", token_id=token_a)


def test_revocation_expiration_authority_failure_and_resource_mismatch_block_publication():
    for action in ("revoke", "expire_lease", "authority_unavailable", "quota"):
        s, token = prepared_publish(ready_for_publish(False))
        s = model.apply(s, action)
        with pytest.raises(model.Reject):
            model.apply(s, "publish", token_id=token)
    s = ready_for_publish(False)
    with pytest.raises(model.Reject, match="current lease authority"):
        model.apply(s, "prepare_publish", writer="A", lease_id=s.lease_id,
                    epoch=s.epoch, authority_id="foreign-authority")


def test_explorer_recounts_bounded_states_and_alias_frontiers():
    counts = model.explore(max_depth=6, max_states=100_000)
    assert counts["states"] > 1
    assert counts["accepted_transitions"] > 0
    assert counts["rejected_attempts"] > 0
    assert counts["max_depth"] == 6
    assert counts["frontier_mismatches"] == 0
    print(counts)
