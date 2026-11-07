"""Synthetic, bounded contract tests; no inference or native filesystem calls."""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import pytest

_MODEL = Path(__file__).parents[1] / "docs/security/src02-contract-remediation-v1/models/safety_model.py"
_SPEC = importlib.util.spec_from_file_location("src02_safety_model", _MODEL)
assert _SPEC and _SPEC.loader
model = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = model
_SPEC.loader.exec_module(model)


def ready_for_publish():
    s = model.State()
    for name, kw in [
        ("prepare_intent", {}),
        ("durable_intent", {}),
        ("mark_dispatch", {"op": s.operation_id}),
        ("response_observed", {}),
        ("response_durable", {}),
        ("persist_object", {}),
        ("journal_durable", {}),
    ]:
        s = model.apply(s, name, **kw)
    return s


def ready_with_local_head():
    s = ready_for_publish()
    s = model.apply(s, "publish", writer="A", epoch=7)
    return model.apply(s, "head_durable")


def test_original_false_commit_counterexample_is_rejected_for_both_policies():
    legacy = dict(intent=True, acknowledged=True, head_durable=True,
                  object_durable=False, journal_durable=False)
    assert model.classify_snapshot(**legacy) is model.Outcome.REJECTED
    assert model.classify_snapshot(**legacy, witness_required=False) is model.Outcome.REJECTED


def test_digest_and_sequence_gap_snapshots_are_rejected():
    valid = model.complete_history()[-1]
    with pytest.raises(model.Reject, match="binding changed"):
        model.classify(replace(valid, manifest_digest="other-manifest"))
    with pytest.raises(model.Reject, match="sequence gap"):
        model.classify(replace(valid, witness_expected=(0, "h0"),
                               witness_next=(2, "gap")))


@pytest.mark.parametrize("changes", [
    {"object_durable": False},
    {"journal_durable": False},
    {"head_durable": False},
    {"witness_ack": False},
])
def test_ack_without_required_barrier_is_rejected(changes):
    committed = model.complete_history()[-1]
    with pytest.raises(model.Reject):
        model.classify(replace(committed, **changes))


def test_complete_legal_histories_commit_with_and_without_witness_policy():
    assert model.classify(model.complete_history(True)[-1]) is model.Outcome.COMMITTED
    assert model.classify(model.complete_history(False)[-1]) is model.Outcome.COMMITTED


def test_fencing_check_and_head_publication_reject_stale_writer_atomically():
    s = ready_for_publish()
    unchanged = (s.sequence, s.head)
    s = model.apply(s, "transfer", writer="A", epoch=7)
    assert s.holder == "B" and s.epoch == 8
    with pytest.raises(model.Reject, match="stale fencing"):
        model.apply(s, "publish", writer="A", epoch=7)
    assert (s.sequence, s.head) == unchanged
    published = model.apply(s, "publish", writer="B", epoch=8)
    assert published.publish_writer == "B" and published.publish_epoch == 8
    with pytest.raises(model.Reject):
        model.apply(published, "publish", writer="A", epoch=7)


def test_uncertain_inference_cannot_be_retried_after_crash():
    s = model.apply(model.State(), "prepare_intent")
    s = model.apply(s, "durable_intent")
    s = model.apply(s, "mark_dispatch", op=s.operation_id)
    s = model.apply(s, "crash")
    assert s.infer is model.Infer.INTERRUPTED_UNKNOWN
    assert s.recovery_status is model.Recovery.RECONCILIATION_REQUIRED
    with pytest.raises(model.Reject, match="recovery is required|possibly dispatched"):
        model.apply(s, "retry_inference")
    recovered = model.apply(s, "recover")
    assert recovered.infer is model.Infer.INTERRUPTED_UNKNOWN
    with pytest.raises(model.Reject, match="recovery is required|possibly dispatched"):
        model.apply(recovered, "retry_inference")


def test_crash_before_dispatch_proves_non_dispatch_and_allows_safe_continuation():
    s = model.apply(model.State(), "prepare_intent")
    s = model.apply(s, "durable_intent")
    s = model.apply(s, "crash")
    s = model.apply(s, "recover")
    assert not s.dispatch_marker_durable and not s.recovery_blocked
    assert s.recovery_status is model.Recovery.RECONCILED
    assert model.apply(s, "retry_inference").infer is model.Infer.INTENT_DURABLE


def test_crash_cuts_at_each_transaction_boundary_require_recovery():
    for state in model.complete_history()[:-1]:
        crashed = model.apply(state, "crash")
        assert crashed.recovery_blocked
        with pytest.raises(model.Reject, match="recovery is required"):
            model.apply(crashed, "persist_object")
        if state.dispatch_marker_durable and not state.response_durable:
            assert crashed.infer is model.Infer.INTERRUPTED_UNKNOWN


def test_durability_failure_blocks_acknowledgment():
    state = model.apply(ready_for_publish(), "barrier_failure")
    with pytest.raises(model.Reject):
        model.apply(state, "publish", writer="A", epoch=7)


def test_intent_before_dispatch_allows_only_idempotent_persistence_retry():
    s = model.apply(model.State(), "prepare_intent")
    s = model.apply(s, "durable_intent")
    s = model.apply(s, "retry_inference")
    persisted = model.apply(s, "persist_object")
    retried = model.apply(persisted, "persist_retry")
    assert retried.object_durable
    with pytest.raises(model.Reject, match="different bytes"):
        model.apply(retried, "persist_conflicting_bytes")


def test_witness_timeout_after_remote_commit_queries_same_operation():
    s = ready_with_local_head()
    s = model.apply(s, "witness_prepare", op=s.operation_id)
    s = model.apply(s, "witness_advance")
    s = model.apply(s, "witness_timeout_after_commit")
    assert not s.witness_ack
    s = model.apply(s, "witness_query")
    assert s.witness_ack and s.witness == model.Witness.MATCH
    s = model.apply(s, "ack")
    assert model.classify(s) is model.Outcome.COMMITTED


def test_witness_timeout_before_remote_commit_retries_only_same_operation():
    s = ready_with_local_head()
    s = model.apply(s, "witness_prepare", op=s.operation_id)
    s = model.apply(s, "witness_timeout_before_commit")
    assert s.recovery_status is model.Recovery.RECONCILIATION_REQUIRED
    s = model.apply(s, "witness_query")
    assert not s.witness_ack and not s.recovery_blocked
    assert s.recovery_status is model.Recovery.RECONCILED
    s = model.apply(s, "witness_advance")
    assert s.witness_committed_op == s.operation_id
    assert model.classify(model.apply(s, "ack")) is model.Outcome.COMMITTED


def test_witness_duplicate_same_operation_is_idempotent():
    s = ready_with_local_head()
    s = model.apply(s, "witness_prepare", op=s.operation_id)
    repeated = model.apply(s, "witness_prepare", op=s.operation_id)
    assert repeated == s
    advanced = model.apply(s, "witness_advance")
    repeated_advance = model.apply(advanced, "witness_advance")
    assert repeated_advance.witness_sequence == advanced.witness_sequence
    assert repeated_advance.witness_head == advanced.witness_head


@pytest.mark.parametrize("kind", ["ahead", "same", "local", "unavailable", "epoch"])
def test_witness_divergence_never_auto_recovers(kind):
    s = ready_with_local_head()
    s = model.apply(s, "witness_diverge", op=kind)
    assert s.recovery_status is model.Recovery.BLOCKED
    with pytest.raises(model.Reject):
        model.apply(s, "recover")


def test_same_operation_local_ahead_reconciliation_is_idempotent():
    s = ready_with_local_head()
    s = model.apply(s, "witness_prepare", op=s.operation_id)
    s = model.apply(s, "recover")
    assert s.witness_ack and not s.recovery_blocked
    assert (s.witness_sequence, s.witness_head) == (s.sequence, s.head)


def test_revocation_and_resource_exhaustion_block_commit():
    for action in ("revoke", "quota"):
        s = model.apply(ready_for_publish(), action)
        with pytest.raises(model.Reject):
            model.apply(s, "publish", writer="A", epoch=7)


def test_explorer_visits_states_and_rejects_illegal_actions():
    counts = model.explore(max_depth=12)
    assert counts["states"] > 1
    assert counts["accepted_transitions"] > 0
    assert counts["rejected_attempts"] > 0
    assert counts["max_depth"] == 12
