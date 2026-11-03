"""Safety/identity guards for validation, not mocked model-inference evidence."""
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest


def script(name):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def snapshot(tmp_path):
    runner = script("validate_real_inference")
    path = tmp_path / "model/snapshots" / runner.REVIEWED["llama-3.2-1b-instruct"][1]
    path.mkdir(parents=True)
    (path / "config.json").write_text(json.dumps({"model_type": "llama"}))
    (path / "tokenizer_config.json").write_text("{}")
    (path / "model.safetensors").write_bytes(b"not loaded by these static guard tests")
    return runner, path


def test_remote_code_checkpoint_is_rejected(tmp_path):
    runner, path = snapshot(tmp_path)
    (path / "config.json").write_text(json.dumps({"model_type": "llama", "auto_map": {"AutoModel": "remote.Custom"}}))
    with pytest.raises(ValueError, match="Unreviewed/custom"):
        runner.review_snapshot(path, "llama-3.2-1b-instruct")


def test_checkpoint_shard_traversal_is_rejected(tmp_path):
    runner, path = snapshot(tmp_path)
    (path / "model.safetensors.index.json").write_text(json.dumps({"weight_map": {"weight": "../outside.safetensors"}}))
    with pytest.raises(ValueError, match="shard"):
        runner.review_snapshot(path, "llama-3.2-1b-instruct")


def test_legacy_pickle_weights_are_not_loaded(tmp_path):
    runner, path = snapshot(tmp_path)
    (path / "pytorch_model.bin").write_bytes(b"not executed")
    with pytest.raises(ValueError, match="pickle-like"):
        runner.review_snapshot(path, "llama-3.2-1b-instruct")


def test_historical_duplicate_ids_keep_compound_identity():
    runner = script("validate_deterministic_readiness")
    frame = pd.DataFrame({"prompt_id": ["0", "0"], "prompt_sha256": ["first", "second"], "label": [0, 1]})
    assert len(runner.identity_index(frame)) == 2
    with pytest.raises(ValueError, match="compound"):
        runner.identity_index(pd.concat([frame, frame]))


def test_frozen_smoke_cannot_expand_into_a_campaign():
    path = Path(__file__).parent / "fixtures/readiness_smoke.json"
    fixture = json.loads(path.read_text(encoding="utf-8"))
    assert fixture["max_new_tokens"] == 16 and len(fixture["inputs"]) == 3
    assert fixture["do_sample"] is False and fixture["seed"] == 2026
