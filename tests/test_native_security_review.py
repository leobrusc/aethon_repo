"""Independent contract checks; shared synthetic scaffolding, no native prototype."""
from collections import Counter

import pytest

from aethon.pilot_collector import FROZEN_FAMILIES
from aethon.pilot_review import ReviewLedger
from test_pilot_collector import SyntheticDefenses, collector, deny_network, setup_run
from test_pilot_remediation import review_fixture

__all__ = ["deny_network", "setup_run", "review_fixture"]


def test_independent_identity_quota_and_full_matrix(setup_run):
    f = setup_run
    cases, slots = f["rows"], f["manifest"]["slots"]
    assert len(cases) == 24 and len(slots) == 120
    pairs = {row["pair_id"] for row in cases}
    assert len(pairs) == 12
    assert Counter(row["family_id"] for row in cases) == {family: 8 for family in FROZEN_FAMILIES}
    for pair in pairs:
        assert sorted(row["label"] for row in cases if row["pair_id"] == pair) == [0, 1]
    assert len({slot["slot_id"] for slot in slots}) == 120
    for sample in {slot["sample_id"] for slot in slots}:
        assert {slot["condition"] for slot in slots if slot["sample_id"] == sample} == {"B0", "B1", "B2", "B3", "B4"}


def test_independent_collection_completion_is_not_scientific_completion(setup_run):
    run = collector(setup_run, defenses=SyntheticDefenses(blocked=True), judge=None)
    result = run.run()
    assert result["collection_status"] == "COLLECTION_COMPLETE"
    assert result["scientific_review_status"] == "REVIEW_PENDING"
    assert result["states"] == {"blocked": 96, "evaluation_pending": 24}
    assert result["represented_slots"] == 120 and not result["scientific_estimates_computed"]


def test_independent_two_votes_conflict_and_assigned_adjudication(review_fixture):
    _, _, ledger, key, signed = review_fixture
    first = ledger.record(key, signed(decision="failure"))
    assert first["state"] == "VOTE_RECORDED" and len(first["vote_refs"]) == 1
    second = ledger.record(key, signed(identity="rater-b", decision="success"))
    assert second["state"] == "ADJUDICATION_PENDING" and len(second["vote_refs"]) == 2
    with pytest.raises(ValueError):
        ledger.record(key, signed(identity="operator", phase="adjudication", vote_refs=second["vote_refs"]))
    final = ledger.record(key, signed(identity="adjudicator", phase="adjudication", vote_refs=second["vote_refs"]))
    assert final["state"] == "SCIENTIFIC_REVIEW_COMPLETE"
    assert final["vote_refs"] == second["vote_refs"]
    assert final["adjudication_ref"] not in final["vote_refs"] and final["audit_sha256"]


def test_independent_b4_review_reuses_source_not_independent_vote(setup_run):
    f = setup_run
    run = collector(f, judge=None); run.run(max_slots=10)
    reused = [slot for slot in run.store.slots.values() if slot["state"] == "reused"]
    assert len(reused) == 2
    ledger = ReviewLedger(run.store, f["authority"], f["rubric_path"])
    for slot in reused:
        source = run.store.slots[slot["reuse"]["source_slot"]]
        rubric = run.store.manifest["review_rubrics"][source["sample_id"]]
        assert source["condition"] == "B3" and slot["condition"] == "B4"
        assert source["response_ref"] == slot["response_ref"]
        binding = ledger.binding(slot["slot_id"], rubric)
        assert binding["case_id"] == source["slot_id"]
        assert ledger.status(slot["slot_id"]) == ledger.status(source["slot_id"])
