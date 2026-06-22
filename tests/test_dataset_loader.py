from dataset_loader import load_dataset


def test_notinject_is_normalized_as_benign():
    frame = load_dataset("notinject")

    assert list(frame.columns) == ["prompt_id", "prompt_text", "label", "source"]
    assert len(frame) == 339
    assert frame["label"].eq(0).all()


def test_jailbreakbench_contains_benign_and_adversarial_labels():
    frame = load_dataset("jailbreakbench_behaviors")

    assert frame["label"].value_counts().to_dict() == {1: 100, 0: 100}


def test_cyberseceval_is_normalized_as_adversarial():
    frame = load_dataset("cyberseceval_prompt_injection")

    assert len(frame) == 251
    assert frame["label"].eq(1).all()
    assert frame["prompt_text"].str.len().gt(0).all()
