"""Independent audit tests for history-excluding State equality."""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import pytest

MODEL_PATH = Path(__file__).parents[1] / "docs/security/src02-contract-remediation-v1/models/safety_model.py"
SPEC = importlib.util.spec_from_file_location("src02_dedup_audit_model", MODEL_PATH)
assert SPEC and SPEC.loader
model = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = model
SPEC.loader.exec_module(model)


def object_persisted_state():
    state = model.State()
    for action, kwargs in (
        ("prepare_intent", {}),
        ("durable_intent", {}),
        ("mark_dispatch", {"op": state.operation_id}),
        ("response_observed", {}),
        ("response_durable", {}),
        ("persist_object", {}),
    ):
        state = model.apply(state, action, **kwargs)
    return state


def acceptance_frontier(state):
    frontier = {}
    for name, kwargs in model.actions(state):
        try:
            successor = model.apply(state, name, **kwargs)
            model.validate(successor)
        except model.Reject:
            frontier[name, tuple(sorted(kwargs.items()))] = "REJECT"
        else:
            frontier[name, tuple(sorted(kwargs.items()))] = "ACCEPT"
    return frontier


def test_distinct_reachable_histories_are_deduplicated_and_have_same_frontier():
    original = object_persisted_state()
    retried = model.apply(original, "persist_retry")

    assert original.history != retried.history
    assert original == retried  # history is compare=False/hash=False
    model.validate(original)
    model.validate(retried)
    assert acceptance_frontier(original) == acceptance_frontier(retried)

    # explore() keys `seen` by State equality, so this exact pair is one node.
    assert len({original, retried}) == 1


def test_invalid_history_alias_is_rejected_before_explore_deduplication():
    valid = object_persisted_state()
    invalid = replace(valid, history=valid.history[:-1])

    # Same equality key does not make an impossible snapshot valid.
    assert valid == invalid
    model.validate(valid)
    with pytest.raises(model.Reject, match="durability and history disagree"):
        model.validate(invalid)

    # The explorer validates each successor before membership in `seen`.
    # Its transition-generated queue therefore cannot be seeded by this alias.
    counts = model.explore(max_depth=12, max_states=100_000)
    assert counts["states"] == 16_642


def test_legal_history_alias_preserves_validation_and_all_declared_successors():
    first = object_persisted_state()
    second = model.apply(first, "persist_retry")
    third = model.apply(second, "persist_retry")

    assert len({first, second, third}) == 1
    assert len({first.history, second.history, third.history}) == 3
    for candidate in (first, second, third):
        model.validate(candidate)
    assert acceptance_frontier(first) == acceptance_frontier(second)
    assert acceptance_frontier(second) == acceptance_frontier(third)


def test_every_bounded_reachable_dedup_alias_is_frontier_equivalent():
    from collections import deque

    queue = deque([(model.State(), 0)])
    representatives = {model.State(): model.State()}
    histories = {model.State(): {model.State().history}}
    alias_pairs = 0
    depth_limit = 12

    while queue:
        state, depth = queue.popleft()
        model.validate(state)
        if depth >= depth_limit:
            continue
        for name, kwargs in model.actions(state):
            try:
                successor = model.apply(state, name, **kwargs)
            except model.Reject:
                continue
            model.validate(successor)
            representative = representatives.get(successor)
            if representative is None:
                representatives[successor] = successor
                histories[successor] = {successor.history}
                queue.append((successor, depth + 1))
                continue
            if successor.history in histories[successor]:
                continue
            histories[successor].add(successor.history)
            if representative.history == successor.history:
                continue
            alias_pairs += 1
            assert model.validate(representative) is None
            assert model.validate(successor) is None
            assert acceptance_frontier(representative) == acceptance_frontier(successor)

    assert len(representatives) == 16_642
    assert alias_pairs > 0
    print({"quotient_states": len(representatives), "reachable_history_aliases": alias_pairs,
           "depth_bound": depth_limit, "frontier_mismatches": 0})


def test_commit_without_dispatch_or_observed_response_is_currently_accepted():
    """Historical counterexample: this assertion records the defect, not approval."""
    state = model.State()
    for action in ("prepare_intent", "durable_intent", "persist_object",
                   "journal_durable", "publish", "head_durable",
                   "witness_prepare", "witness_advance", "ack"):
        kwargs = {"writer": "A", "epoch": 7} if action == "publish" else {}
        state = model.apply(state, action, **kwargs)
    assert state.infer is model.Infer.INTENT_DURABLE
    assert not state.dispatch_marker_durable
    assert "response_observed" not in state.history
    assert model.classify(state) is model.Outcome.COMMITTED


def test_unavailable_witness_query_currently_clears_recovery_block():
    """Historical counterexample: NOT a safe witness reconciliation result."""
    state = model.State()
    for action, kwargs in (
        ("prepare_intent", {}), ("durable_intent", {}),
        ("mark_dispatch", {"op": "op-fixture"}), ("response_observed", {}),
        ("response_durable", {}), ("persist_object", {}),
        ("journal_durable", {}), ("publish", {"writer": "A", "epoch": 7}),
        ("head_durable", {}), ("witness_prepare", {"op": "op-fixture"}),
        ("witness_diverge", {"op": "unavailable"}),
    ):
        state = model.apply(state, action, **kwargs)
    assert not state.witness_available and state.recovery_blocked
    queried = model.apply(state, "witness_query")
    assert queried.recovery_status is model.Recovery.RECONCILED
    assert not queried.recovery_blocked
    assert not queried.witness_ack
