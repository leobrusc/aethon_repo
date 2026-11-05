"""Protect the new publication guard without including real secret material."""
import hashlib
import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "repository_guard", Path(__file__).resolve().parents[1] / "scripts/repository_guard.py"
)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


def test_large_blob_and_lfs_pointer():
    assert guard.violations("data.bin", b"x" * (guard.LIMIT + 1))
    pointer = b"version https://git-lfs.github.com/spec/v1\noid sha256:" + b"a" * 64
    assert not guard.violations("dataset.jsonl", pointer)


def test_credentials_are_flagged_without_values_in_output():
    candidate = b"ghp_" + b"a" * 40
    assert guard.violations("config.txt", candidate)
    assert not any(candidate.decode() in message for message in guard.violations("config.txt", candidate))
    assert guard.violations(".env", b"EXAMPLE=value")
    assert not guard.violations(".env.example", b"EXAMPLE=placeholder")


def test_exact_historical_result_blob_is_allowed():
    name = "results/revision/detection/per_prompt_results.csv"
    root = Path(__file__).resolve().parents[1]
    worktree_bytes = (root / name).read_bytes()
    canonical_bytes = guard.git("show", f"HEAD:{name}")
    assert len(canonical_bytes) > guard.LIMIT
    assert hashlib.sha256(canonical_bytes).hexdigest() == guard.ALLOWED_LARGE_BLOBS[name]
    assert hashlib.sha256(worktree_bytes.replace(b"\r\n", b"\n")).hexdigest() == guard.ALLOWED_LARGE_BLOBS[name]
    assert guard.violations(name, canonical_bytes) == []


def test_modified_historical_result_at_same_path_is_rejected():
    name = "results/revision/detection/per_prompt_results.csv"
    changed = b"x" * (guard.LIMIT + 1)
    assert "Git blob exceeds 5 MiB; use LFS or a source manifest" in guard.violations(name, changed)


def test_new_large_blob_is_rejected():
    changed = b"x" * (guard.LIMIT + 1)
    assert "Git blob exceeds 5 MiB; use LFS or a source manifest" in guard.violations("results/new.csv", changed)
