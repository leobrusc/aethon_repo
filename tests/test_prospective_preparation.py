"""Software-only checks. No target loading, inference or scientific pilot."""
import copy
import json
from pathlib import Path

import pytest

from aethon.generation import GenerationResult
from aethon.prospective import (case_identity, complete_asr, preflight,
                               review_generated, sample_identity, validate_fixture)

ROOT = Path(__file__).resolve().parents[1]
REV = "9213176726f574b556790deb65791e0c5aa438b6"
TEMPLATE = "5816fce10444e03c2e9ee1ef8a4a1ea61ae7e69e438613f3b17b69d0426223a4"


def result(**kwargs):
    values = dict(original_prompt="prompt contains CANARY", input_ids=[1, 2],
                  generated_ids=[3, 4], continuation="Safe task answer",
                  legacy_full_text="prompt contains CANARY Safe task answer",
                  stop_reason="eos", metadata={"revision": REV,
                  "chat_template_sha256": TEMPLATE, "chat_template_applied": True})
    values.update(kwargs)
    return GenerationResult(**values)


def review(value, judge):
    return review_generated(value, judge, prompt="prompt contains CANARY", revision=REV,
                            template_sha256=TEMPLATE, objective="disclose canary", rubric_id="synthetic-disclosure-v1")


def test_only_new_continuation_reaches_judge():
    seen = []
    def judge(**kwargs):
        seen.append(kwargs)
        return {"status": "failure", "evidence_ref": "private:span:0-16"}
    assert review(result(), judge)["status"] == "failure"
    assert seen[0]["continuation"] == "Safe task answer"
    assert "CANARY" not in seen[0]["continuation"]
    assert "legacy_full_text" not in seen[0]


@pytest.mark.parametrize("reason", ["length", "unknown"])
def test_incomplete_output_requires_review_without_automatic_judgment(reason):
    assert review(result(stop_reason=reason), lambda **kw: pytest.fail("judge called"))["status"] == "indeterminate"


def test_empty_visible_continuation_is_not_mitigation():
    assert review(result(continuation=""), lambda **kw: pytest.fail("judge called"))["status"] == "no_response"


@pytest.mark.parametrize("value", ["prompt and response", result(original_prompt="foreign"),
    result(metadata={"revision": "wrong", "chat_template_sha256": TEMPLATE, "chat_template_applied": True}),
    result(metadata={"revision": REV, "chat_template_sha256": "wrong", "chat_template_applied": True}),
    result(metadata={"revision": REV, "chat_template_sha256": TEMPLATE, "chat_template_applied": False})])
def test_ambiguous_or_drifted_provenance_rejected(value):
    with pytest.raises(ValueError):
        review(value, lambda **kw: pytest.fail("judge called"))


def test_judgment_requires_private_evidence():
    with pytest.raises(ValueError):
        review(result(), lambda **kw: {"status": "success"})


def test_structured_identity_has_no_delimiter_collision_and_keeps_source_rows():
    first = sample_identity("pool", "a:b", "c", "hello")
    assert first != sample_identity("pool", "a", "b:c", "hello")
    assert first["sample_id"] != sample_identity("pool", "a:b", "d", "hello")["sample_id"]
    normalized = sample_identity("pool", "a:b", "c", "hello  world")
    other = sample_identity("pool", "a:b", "c", "hello world")
    assert normalized["normalized_sha256"] == other["normalized_sha256"]
    assert normalized["sample_id"] != other["sample_id"]


def test_case_identity_binds_condition_revision_and_replicate():
    assert case_identity("a", REV, "B0", 0, "p") != case_identity("a", REV, "B3", 0, "p")
    assert case_identity("a", REV, "B0", 0, "p") != case_identity("a", REV, "B0", 1, "p")
    with pytest.raises(ValueError): case_identity("a", REV, "B0", True, "p")


def test_synthetic_fixtures_unique_and_never_eligible():
    rows = json.loads((ROOT/"tests/fixtures/prospective_pilot_v1.json").read_text())
    assert len(validate_fixture(rows)) == 4
    with pytest.raises(ValueError): validate_fixture(rows + [rows[0]])
    rows[0]["fixture_only"] = False
    with pytest.raises(ValueError): validate_fixture(rows)


def annotations():
    return [dict(row_id="a", target_revision=REV, condition="B3", replicate=0,
                 attack_objective="objective", rubric_id="r", judge_id="human-a", evidence="",
                 status="no_response", blocked=False, submitted_to_llm=True, technical_error=True),
            dict(row_id="b", target_revision=REV, condition="B3", replicate=0,
                 attack_objective="objective", rubric_id="r", judge_id="human-a", evidence="",
                 status="prevented", blocked=True, submitted_to_llm=False, technical_error=False)]


def test_missing_response_remains_in_full_inventory_bounds():
    summary = complete_asr(["a", "b"], annotations())
    assert summary["all_eligible"]["denominator"] == 2
    assert summary["all_eligible"]["lower"] == 0
    assert summary["all_eligible"]["upper"] == .5
    with pytest.raises(ValueError): complete_asr(["a", "b"], annotations()[1:])


def test_mixed_condition_duplicate_and_string_flags_rejected():
    rows = annotations(); rows[1]["condition"] = "B0"
    with pytest.raises(ValueError): complete_asr(["a", "b"], rows)
    with pytest.raises(ValueError): complete_asr(["a", "a"], annotations())
    rows = annotations(); rows[0]["technical_error"] = "false"
    with pytest.raises(ValueError): complete_asr(["a", "b"], rows)


def test_checked_in_plan_is_blocked_without_inference():
    manifest = json.loads((ROOT/"configs/science/pilot_v1.json").read_text())
    status = preflight(manifest, ROOT)
    assert status["classification"] == "PILOT_BLOCKED"
    assert status["campaign_executed"] is False
    assert "semantic_review" in status["blockers"]
    assert not any(b.startswith("frozen_file:") for b in status["blockers"])
    drift = copy.deepcopy(manifest); drift["baseline"] = "wrong"
    with pytest.raises(ValueError): preflight(drift, ROOT)


def test_other_worktrees_are_not_private_destinations(tmp_path):
    root = tmp_path/"repo/.worktrees/science"; root.mkdir(parents=True)
    manifest = json.loads((ROOT/"configs/science/pilot_v1.json").read_text())
    manifest["private_storage"] = {"path": str(tmp_path/"repo/private"),
                                   "custodian": "operator", "delete_after": "2099-01-01"}
    assert "private_destination" in preflight(manifest, root)["blockers"]
