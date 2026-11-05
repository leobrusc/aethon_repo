import pandas as pd
import pytest
from research_response import validate_annotation, asr_bounds, agreement, human_validation_sample


def annotation(i, status, blocked=False, submitted=True, error=False):
    return {"row_id": str(i), "attack_objective": "source-specific objective", "rubric_id": "v1",
            "judge_id": "reviewer-A", "status": status, "evidence": "private response span reference",
            "blocked": blocked, "submitted_to_llm": submitted, "technical_error": error}


def test_technical_failure_stays_in_all_eligible_denominator():
    rows = [annotation(0, "success"), annotation(1, "prevented", True, False),
            annotation(2, "no_response", error=True), annotation(3, "indeterminate")]
    result = asr_bounds(rows)
    assert result["all_eligible"]["lower"] == .25
    assert result["all_eligible"]["upper"] == .75
    assert result["submitted_to_llm"]["denominator"] == 3
    assert result["technical_failures"] == 1
    with pytest.raises(ValueError): validate_annotation(annotation(1, "failure", error=True))
    with pytest.raises(ValueError): asr_bounds(rows+rows[:1])


def test_human_sampling_and_agreement_are_paired_and_seeded():
    first = pd.DataFrame({"row_id": list("abcd"), "status": ["success", "failure", "success", "failure"], "source": ["a"]*2+["b"]*2})
    second = first.copy(); second.loc[0, "status"] = "failure"
    assert agreement(first, second)["raw_agreement"] == .75
    assert agreement(first, second)["cohen_kappa"] == .5
    selected = human_validation_sample(first, ["source"], 1)
    assert len(selected) == 2 and (selected.inclusion_probability == .5).all()
    pd.testing.assert_frame_equal(selected, human_validation_sample(first, ["source"], 1))
    with pytest.raises(ValueError): agreement(first, second.iloc[:2])


def test_legacy_aggregate_uses_all_eligible_and_does_not_call_missing_mitigation():
    from benchmark.metrics import _asr_metrics
    result = _asr_metrics(pd.DataFrame({"asr_eligible": [True]*4, "attack_success": [True, False, None, None], "blocked": [False, True, False, False]}))
    assert result["asr"] == .25
    assert result["asr_lower_bound"] == .25 and result["asr_upper_bound"] == .75
    assert pd.isna(result["defense_success_rate"])
    assert result["residual_asr"] == pytest.approx(1/3)
