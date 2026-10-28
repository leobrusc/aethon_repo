import numpy as np
import pytest
from research_generalization import grouped_splits, threshold_under_cap, calibration_report, fit_model


def test_grouped_folds_never_split_duplicates():
    texts = np.array([f"topic {i}" for i in range(12)] * 2)
    labels = np.array([0, 1] * 6 * 2)
    for train, valid in grouped_splits(texts, labels, 3, 3):
        assert not set(texts[train]) & set(texts[valid])
    with pytest.raises(ValueError, match="Conflicting"):
        grouped_splits(np.array(["same", "same"]), np.array([0, 1]), 2, 3)


def test_fpr_constraint_applies_to_full_or_rule():
    labels = np.array([0, 0, 1, 1])
    scores = np.array([.1, .2, .7, .9])
    assert threshold_under_cap(labels, scores, np.array([True, False, False, False]), .1) is None
    selected = threshold_under_cap(labels, scores, np.zeros(4, bool), 0)
    assert selected["fpr"] == 0 and selected["recall"] == 1
    # A cap must remain feasible even when every benign score exceeds attacks.
    selected = threshold_under_cap(labels, scores[::-1], np.zeros(4, bool), 0)
    assert selected is not None and selected["fpr"] == 0


def test_calibration_rejects_margins_and_reports_perfect_probabilities():
    result, bins = calibration_report(np.array([0, 1]), np.array([0., 1.]))
    assert result["brier"] == result["ece"] == 0
    assert sum(x["count"] for x in bins) == 2
    with pytest.raises(ValueError):
        calibration_report(np.array([0, 1]), np.array([-1., 1.]))


def test_sigmoid_calibration_wraps_entire_text_pipeline():
    texts = np.array([f"ordinary useful topic {i}" for i in range(12)] +
                     [f"malicious harmful instruction {i}" for i in range(12)])
    labels = np.array([0]*12+[1]*12)
    model = fit_model(("char_3_5", "calibrated_linear_svm"), texts, labels, 4)
    assert "features" in model.estimator.named_steps
    assert model.predict_proba(["useful topic"]).shape == (1, 2)
