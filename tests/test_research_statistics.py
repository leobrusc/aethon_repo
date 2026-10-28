import pytest
from analysis_utils import mcnemar_test
from analysis_utils import bootstrap_ci, paired_bootstrap_difference
from sklearn.metrics import accuracy_score


def test_mcnemar_counts_correctness_on_both_classes():
    # First classifier alone is correct on four benign and four attack rows.
    truth = [0] * 4 + [1] * 4
    assert mcnemar_test(truth, truth, [1] * 4 + [0] * 4) == pytest.approx(0.0078125)


def test_mcnemar_identical_and_invalid_pairs():
    assert mcnemar_test([0, 1], [0, 1], [0, 1]) == 1.0
    with pytest.raises(ValueError):
        mcnemar_test([0, 1], [0], [0, 1])
    with pytest.raises(ValueError):
        mcnemar_test([0], [2], [0])


def test_bootstrap_is_seeded_and_preserves_identical_pairs():
    assert bootstrap_ci([1, 2, 3], seed=4) == bootstrap_ci([1, 2, 3], seed=4)
    result = paired_bootstrap_difference([0, 1, 0, 1], [0, 1, 1, 0], [0, 1, 1, 0],
                                         accuracy_score, clusters=["a", "a", "b", "b"], n=30)
    assert result["ci_low"] == result["ci_high"] == result["difference"] == 0
    assert result["valid_resamples"] == 30
