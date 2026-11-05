"""Independent reproductions: passing assertions document defects, not remediation.

Synthetic scaffolding is reused; no target inference or external service is used.
"""
import copy
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from aethon.pilot_collector import no_external_calls, validate_inventory
from aethon.pilot_governance import OpenSSLVerifier, ReceiptAuthority, digest
from test_pilot_collector import collector, deny_network, setup_run, synthetic_rows

# Imported fixtures register the existing synthetic-only setup and network denial.
__all__ = ["deny_network", "setup_run"]


def test_src01_replaced_verifier_is_used_without_revalidating_pin(tmp_path, monkeypatch):
    executable = tmp_path / "synthetic-verifier.exe"
    executable.write_bytes(b"trusted synthetic tool")
    pinned = digest(executable.read_bytes())
    verifier = OpenSSLVerifier(str(executable), pinned)
    executable.write_bytes(b"replacement synthetic tool")
    calls = []

    def controlled_launcher(argv, **kwargs):
        calls.append(argv)
        assert Path(argv[0]).read_bytes() != b"trusted synthetic tool"
        return SimpleNamespace(returncode=0, stdout=bytes.fromhex("302a300506032b6570032100") + b"x" * 32)

    monkeypatch.setattr("aethon.pilot_governance.subprocess.run", controlled_launcher)
    assert digest(executable.read_bytes()) != pinned
    assert verifier(b"synthetic public key", b"synthetic payload", b"x" * 64)
    assert len(calls) == 2  # Launcher simulation; no malicious executable is run.


def test_src02_replaced_storage_root_accepts_stale_observation(setup_run):
    f = setup_run
    root = f["private"]
    old = (root.stat().st_dev, root.stat().st_ino)
    f["observation"]["observation"].update(device=old[0], inode=old[1])
    root.rename(root.with_name("original-private"))
    root.mkdir()
    assert (root.stat().st_dev, root.stat().st_ino) != old
    store = f["store"]()
    assert store.identities[root] != old
    assert (store.path / "manifest.json").is_file()


def test_sci01_family_allocation_is_not_enforced():
    rows = synthetic_rows()
    for row in rows:
        row["family_id"] = "only-one-family"
    validate_inventory(rows)
    assert len({r["family_id"] for r in rows}) == 1
    assert len({r["pair_id"] for r in rows}) == 12


def test_sci02_unassigned_judge_is_persisted_as_completed(setup_run):
    def unassigned(**kwargs):
        assert "PRIVATE_INPUT_CANARY" not in kwargs["continuation"]
        return {"status": "success", "judge_id": "NOT-ASSIGNED", "evidence_ref": "unchecked-reference"}

    run = collector(setup_run, judge=unassigned)
    run.run(max_slots=1)
    slot = next(s for s in run.store.slots.values() if s["state"] == "completed")
    judgment = run.store.get(slot["evaluation_ref"])["judgment"]
    assert judgment["judge_id"] not in setup_run["authority"].policy["authorities"]
    assert judgment["status"] == "success"


def test_control_foreign_subject_receipt_replay_rejected(setup_run):
    f = setup_run
    subject = dict(f["subject"], run_id="foreign-run")
    with pytest.raises(ValueError):
        f["authority"].verify(f["envelopes"]["execution_authorization"], "execution_authorization", subject)


def test_control_attacker_policy_rejected_by_independent_pin(setup_run):
    f = setup_run
    legitimate_pin = digest(f["policy_path"].read_bytes())
    f["policy_path"].write_text('{"schema":"aethon.trust-policy.v1","authorities":{}}')
    with pytest.raises(ValueError, match="Trust-anchor mismatch"):
        ReceiptAuthority(f["policy_path"], legitimate_pin, [f["repo"]])


def test_control_role_substitution_rejected(setup_run):
    f = setup_run
    envelope = copy.deepcopy(f["envelopes"]["execution_authorization"])
    with pytest.raises(ValueError):
        f["authority"].verify(envelope, "rubric_review", f["subject"])


def test_limitation_system_dispatch_is_not_an_os_sandbox():
    # Local shell exits immediately; no connection, target inference or service.
    with no_external_calls():
        assert os.system("exit 0") == 0


def test_limitation_complete_empty_journal_rollback_has_no_anchor(setup_run):
    f = setup_run
    run = collector(f)
    run.run(max_slots=1)
    # Move owned synthetic artifacts aside, preserving them as evidence.
    for directory in [run.store.events, run.store.objects]:
        archive = directory.with_name(directory.name + "-synthetic-archive")
        directory.rename(archive)
        directory.mkdir()
    for pointer in run.store.path.glob("*.json"):
        if pointer.name != "manifest.json":
            pointer.rename(pointer.with_suffix(".archived"))
    restored = f["store"]()
    assert restored.sequence == 0
    assert restored.summary()["attempted_calls"] == 0
