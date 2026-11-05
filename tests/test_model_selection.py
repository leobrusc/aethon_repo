import numpy as np
import pandas as pd
import copy

from model_selection import (
    FINAL_DATASETS,
    REPRESENTATIONS,
    build_pipeline,
    choose_threshold,
    load_training_only,
    metric,
)
from aethon_heuristic import PATTERNS


def test_selection_training_source_is_single_locked_dataset(monkeypatch):
    seen = []
    import model_selection
    original = model_selection.load_dataset
    monkeypatch.setattr(model_selection, "load_dataset", lambda name: (seen.append(name) or original(name)))
    frame = load_training_only()
    assert len(frame) == 546
    assert seen == ["prompt_injections_train"]
    assert set(FINAL_DATASETS).isdisjoint(seen)


def test_threshold_selection_uses_requested_grid_and_fpr_constraint():
    labels = np.array([0, 0, 1, 1])
    scores = np.array([0.1, 0.3, 0.7, 0.9])
    threshold, values = choose_threshold(labels, scores, 0.10)
    assert threshold >= 0.31
    assert values["fpr"] <= 0.10


def test_candidate_representations_and_classifiers_are_deterministic():
    assert len(REPRESENTATIONS) == 5
    assert set(REPRESENTATIONS) == {"word_unigram", "word_bigram", "char_3_5", "char_3_6", "word_char_union"}
    first = build_pipeline("word_unigram", "logistic_regression").get_params(deep=False)
    second = build_pipeline("word_unigram", "logistic_regression").get_params(deep=False)
    assert first.keys() == second.keys()
    assert build_pipeline("word_unigram", "linear_svm").named_steps["classifier"].random_state == 42


def test_metric_confusions_are_correct_without_evaluation_data():
    result = metric(np.array([0, 0, 1, 1]), np.array([0, 1, 1, 0]), np.array([.1, .6, .8, .2]))
    assert result["tp"] == result["tn"] == result["fp"] == result["fn"] == 1
    assert result["f1"] == 0.5


def test_final_evaluation_does_not_mutate_frozen_model(monkeypatch):
    import model_selection
    model = build_pipeline("word_unigram", "logistic_regression")
    training = load_training_only()
    model.fit(training.prompt_text, training.label)
    before = copy.deepcopy(model.named_steps["classifier"].coef_)
    monkeypatch.setattr(model_selection, "FINAL_DATASETS", ("prompt_injections_test",))
    model_selection.final_evaluation(model, 0.5)
    assert np.array_equal(before, model.named_steps["classifier"].coef_)


def test_heuristic_rules_are_unchanged():
    assert PATTERNS == [
        r"ignore previous instructions",
        r"ignore (the )?previous",
        r"system override",
        r"as an? jailbroken",
        r"reset your instructions",
        r"do not follow previous",
        r"disregard previous",
        r"follow the instructions below",
    ]
