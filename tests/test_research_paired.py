import pandas as pd
import pytest
from research_paired import align, compare


def test_pairing_preserves_duplicate_text_at_distinct_rows():
    first = pd.DataFrame({"dataset": ["a", "a"], "prompt_id": ["0", "1"],
                          "prompt_sha256": ["same", "same"], "true_label": [0, 1], "prediction": [0, 1]})
    assert len(align(first, first.iloc[::-1])) == 2
    assert compare(first, first, iterations=10)["accuracy"]["difference"] == 0
    with pytest.raises(ValueError): align(pd.concat([first, first]), first)
    with pytest.raises(ValueError): align(first, first.iloc[:1])
    wrong = first.copy(); wrong.loc[0, "true_label"] = 1
    with pytest.raises(ValueError): align(first, wrong)
