"""Protect the new publication guard without including real secret material."""
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
