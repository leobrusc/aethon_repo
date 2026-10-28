import pandas as pd
import pytest
from research_integrity import audit, normalize


def frame(texts, labels):
    return pd.DataFrame({"prompt_text": texts, "label": labels, "prompt_id": range(len(texts))})


def test_exact_overlap_conflicts_and_stable_identity():
    frames = {"prompt_injections_train": frame(["Ａ  test", "same", "same"], [0, 0, 0]),
              "prompt_injections_test": frame(["A test", "same"], [1, 0])}
    rows, exact, near, summary = audit(frames)
    assert rows.row_id.is_unique
    assert summary["cross_partition_exact_groups"] == 2
    assert exact.conflicting_labels.sum() == 1
    assert not summary["historical_pool_count_matches"]
    assert "prompt_text" not in rows
    assert normalize("Ａ\n test") == "A test"
    pd.testing.assert_frame_equal(rows, audit(frames)[0])


def test_near_overlap_is_only_lexical():
    frames = {"prompt_injections_train": frame(["long text about ordinary useful technical work " * 3], [0]),
              "prompt_injections_test": frame(["long text about ordinary useful technical work " * 3 + "!"], [0])}
    _, _, near, summary = audit(frames, .9)
    assert len(near) == 1 and near.cross_partition.all()
    assert summary["semantic_overlap_audit"] == "NOT_RUN"
    with pytest.raises(ValueError):
        audit(frames, 0)
