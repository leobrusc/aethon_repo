import json
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
import torch
from baseline_detectors import TransformerDetector
import research_baseline


def test_label_mapping_fails_closed():
    detector = TransformerDetector.__new__(TransformerDetector)
    detector.malicious_labels = {"injection"}
    detector.model = SimpleNamespace(config=SimpleNamespace(id2label={0: "SAFE", 1: "INJECTION"}))
    assert detector._find_index() == 1
    detector.model.config.id2label = {0: "LABEL_0", 1: "LABEL_1"}
    with pytest.raises(ValueError): detector._find_index()


def test_single_and_batched_predictions_match_without_weights():
    class Tokenizer:
        def __call__(self, prompts, **kwargs):
            if isinstance(prompts, str): prompts = [prompts]
            tensor = torch.tensor([[len(p), 1] for p in prompts])
            return {"input_ids": tensor, "attention_mask": torch.ones_like(tensor)}
    class Model:
        def __call__(self, input_ids, attention_mask):
            score = input_ids[:, 0].float()-4
            return SimpleNamespace(logits=torch.stack([-score, score], dim=1))
    detector = TransformerDetector.__new__(TransformerDetector)
    detector.tokenizer, detector.model = Tokenizer(), Model()
    detector.device, detector.max_length, detector.malicious_index = torch.device("cpu"), 512, 1
    prompts = ["a", "longer text"]
    batch = detector.predict_batch(prompts)
    for prompt, batched in zip(prompts, batch):
        single = detector.predict(prompt)
        assert single.score == pytest.approx(batched[0])
        assert single.prediction == batched[1]


def test_offline_unavailable_model_records_not_run(tmp_path, monkeypatch):
    monkeypatch.setattr(research_baseline, "EVALUATION_DATASETS", ["notinject"])
    monkeypatch.setattr(research_baseline, "get_dataset_metadata", lambda n: {"name": n, "sha256": "test"})
    monkeypatch.setattr(research_baseline, "load_dataset", lambda n: pd.DataFrame({"prompt_id": ["0"], "prompt_text": ["ordinary"], "label": [0]}))
    monkeypatch.setattr(research_baseline.subprocess, "check_output", lambda *a, **k: "test")
    def unavailable(*args, **kwargs):
        assert kwargs["local_files_only"] is True
        raise FileNotFoundError("offline test")
    monkeypatch.setattr(research_baseline, "snapshot_download", unavailable)
    monkeypatch.setattr("sys.argv", ["research_baseline.py", "--revision", "a"*40, "--run-id", "test", "--output", str(tmp_path)])
    research_baseline.main()
    result = json.loads((tmp_path/"test"/"manifest.json").read_text())
    assert result["status"] == "NOT_RUN" and "unavailable" in result["reason"]
