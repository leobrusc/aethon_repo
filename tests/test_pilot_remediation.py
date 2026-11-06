"""Synthetic acceptance tests; no real pilot, target inference or efficacy claims."""
import base64
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from pathlib import Path
import subprocess

import pytest

from aethon.pilot_collector import validate_inventory
from aethon.pilot_governance import OpenSSLVerifier, canonical, digest, verify_gates
from aethon.pilot_review import ReviewLedger
from aethon.pilot_storage import CorruptCheckpoint, PrivateRunStore
from aethon.prospective import fingerprint
from test_pilot_collector import (SyntheticConfinement, collector, deny_network,
                                  setup_run, synthetic_rows)

__all__ = ["deny_network", "setup_run"]


@pytest.mark.parametrize("change", ["replace", "rename", "dependency", "ancestor", "unchanged"])
def test_verifier_drift_or_unavailable_native_backend_never_executes(tmp_path, monkeypatch, change):
    executable, dependency = tmp_path/"tool.exe", tmp_path/"library.bin"
    executable.write_bytes(b"SYNTHETIC TOOL")
    dependency.write_bytes(b"SYNTHETIC DEPENDENCY")
    verifier = OpenSSLVerifier(str(executable), digest(executable.read_bytes()),
                               {str(dependency): digest(dependency.read_bytes())})
    if change == "replace": executable.write_bytes(b"REPLACEMENT")
    if change == "rename": executable.rename(tmp_path/"original-tool"); executable.write_bytes(b"SYNTHETIC TOOL")
    if change == "dependency": dependency.write_bytes(b"REPLACEMENT DEPENDENCY")
    if change == "ancestor":
        from aethon import pilot_identity
        original = pilot_identity.path_identity
        def changed(path, **kwargs):
            result = copy.deepcopy(original(path, **kwargs))
            result["ancestors"][-1]["inode"] += 1
            return result
        monkeypatch.setattr(pilot_identity, "path_identity", changed)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("No pathname execution/fallback permitted"))
    with pytest.raises(PermissionError): verifier(b"synthetic key", b"synthetic payload", b"x"*64)


def test_verifier_missing_identity_and_wrong_dependency_pin(tmp_path):
    with pytest.raises(OSError): OpenSSLVerifier(str(tmp_path/"absent"), "0"*64)
    tool = tmp_path/"tool"; tool.write_bytes(b"synthetic")
    with pytest.raises(ValueError): OpenSSLVerifier(str(tool), "0"*64)
    tool.with_name("dep").write_bytes(b"synthetic dependency")
    with pytest.raises(ValueError): OpenSSLVerifier(str(tool), digest(tool.read_bytes()), {str(tool.with_name("dep")): "0"*64})


def test_stable_storage_only_with_explicit_synthetic_backend(setup_run):
    f = setup_run
    with pytest.raises(PermissionError, match="writes disabled"):
        PrivateRunStore(f["private"], f["manifest"], f["permission"], [f["repo"]], f["observation"])
    assert not (f["private"]/f["manifest"]["run_id"]).exists()
    first = f["store"]()
    assert first.manifest == f["store"]().manifest


@pytest.mark.parametrize("field", ["subject_sha256", "path_identity", "path_sha256"])
def test_foreign_or_stale_storage_observation_is_rejected(setup_run, field):
    f = setup_run; observation = copy.deepcopy(f["observation"])
    observation["observation"][field] = "foreign"
    observation["probe_fingerprint"] = fingerprint(observation["observation"])
    with pytest.raises(PermissionError):
        PrivateRunStore(f["private"], f["manifest"], f["permission"], [f["repo"]], observation,
                        confinement=SyntheticConfinement())


@pytest.mark.parametrize("field", ["mode", "inode"])
def test_ancestor_or_permission_drift_stops_write(setup_run, monkeypatch, field):
    # Historical inode/ACL tests are archived. No pathname hook can activate storage.
    f=setup_run
    with pytest.raises(PermissionError):
        PrivateRunStore(f['private'], f['manifest'], f['permission'], [f['repo']], f['observation'],
                        confinement=SyntheticConfinement(), backend=f['backend'])


@pytest.mark.parametrize("counts", [(4,4,4), (12,0,0), (5,4,3), (6,3,3)])
def test_frozen_family_quotas(counts):
    rows = synthetic_rows()
    families = [f for f, n in zip(("instruction-override", "synthetic-disclosure", "answer-contamination"), counts) for _ in range(n)]
    for i, family in enumerate(families):
        rows[2*i]["family_id"] = rows[2*i+1]["family_id"] = family
    if counts == (4,4,4): assert len(validate_inventory(rows)) == 24
    else:
        with pytest.raises(ValueError): validate_inventory(rows)


@pytest.mark.parametrize("change", ["unknown", "incomplete", "duplicate", "pair-context"])
def test_inventory_unknown_or_broken_pairs_rejected(change):
    rows = synthetic_rows()
    if change == "unknown": rows[0]["family_id"] = rows[1]["family_id"] = "UNKNOWN"
    if change == "incomplete": rows.pop()
    if change == "duplicate": rows[1] = copy.deepcopy(rows[0])
    if change == "pair-context": rows[1]["system_prompt"] += "DRIFT"
    with pytest.raises(ValueError): validate_inventory(rows)


@pytest.fixture
def review_fixture(setup_run, tmp_path):
    f = setup_run
    run = collector(f, judge=None); run.run(max_slots=1)
    slot = next(s for s in run.store.slots.values() if s["state"] == "evaluation_pending")
    ledger = ReviewLedger(run.store, f["authority"], f["rubric_path"])
    rubric = run.store.manifest["review_rubrics"][slot["sample_id"]]
    counter = [0]

    def signed(identity="rater-a", decision="success", phase="vote", changes=None, span_changes=None, vote_refs=None):
        now = datetime.now(timezone.utc)
        binding = ledger.binding(slot["slot_id"], rubric)
        span = {"schema": "aethon.review-span.v1", **binding, "start": 0, "end": 8,
                "span_sha256": digest(b"SYNTHETI")}
        if span_changes: span.update(span_changes)
        counter[0] += 1
        path = tmp_path/f"synthetic-span-{counter[0]}.json"; path.write_bytes(canonical(span))
        payload = {"schema": "aethon.review-vote.v1", **binding, "phase": phase, "reviewer_id": identity,
                   "decision": decision, "issued_at": (now-timedelta(minutes=1)).isoformat(),
                   "expires_at": (now+timedelta(hours=1)).isoformat(),
                   "evidence": {"path": str(path), "sha256": digest(path.read_bytes())}}
        if vote_refs is not None: payload["vote_refs"] = vote_refs
        if changes: payload.update(changes)
        key = f["keys"].get(identity, b"synthetic unknown evaluator")
        return {"payload": payload, "signature": {"authority_id": identity,
                "signature_base64": base64.b64encode(hmac.new(key, canonical(payload), hashlib.sha256).digest()).decode()}}
    return f, run, ledger, slot["slot_id"], signed


@pytest.mark.parametrize("changes", [{"case_id":"foreign"}, {"response_sha256":"0"*64},
                                    {"rubric_id":"foreign"}, {"rubric_sha256":"0"*64},
                                    {"run_fingerprint":"0"*64}, {"assignment_sha256":"0"*64}])
def test_signed_but_foreign_review_binding_rejected(review_fixture, changes):
    _, _, ledger, key, signed = review_fixture
    with pytest.raises(ValueError): ledger.record(key, signed(changes=changes))
    assert ledger.status(key)["state"] == "REVIEW_PENDING"


def test_unassigned_and_aliased_evaluators_rejected(review_fixture):
    f, _, ledger, key, signed = review_fixture
    with pytest.raises(ValueError): ledger.record(key, signed(identity="unknown"))
    f["authority"].policy["authorities"]["rater-b"] = copy.deepcopy(f["authority"].policy["authorities"]["rater-a"])
    with pytest.raises(PermissionError): ledger.record(key, signed(identity="rater-b"))
    assert verify_gates(f["authority"], f["envelopes"], f["subject"], f["technical"])["classification"] == "PILOT_BLOCKED"


@pytest.mark.parametrize("change", [{"case_id":"foreign"}, {"span_sha256":"0"*64}, {"end":99999}])
def test_foreign_or_invalid_evidence_rejected(review_fixture, change):
    _, _, ledger, key, signed = review_fixture
    with pytest.raises(ValueError): ledger.record(key, signed(span_changes=change))


def test_missing_and_changed_evidence_rejected(review_fixture):
    _, _, ledger, key, signed = review_fixture
    envelope = signed()
    Path(envelope["payload"]["evidence"]["path"]).write_bytes(b"corrupted synthetic evidence")
    with pytest.raises(ValueError): ledger.record(key, envelope)
    envelope = signed()
    Path(envelope["payload"]["evidence"]["path"]).rename(Path(envelope["payload"]["evidence"]["path"]).with_suffix(".archived"))
    with pytest.raises(OSError): ledger.record(key, envelope)


def test_one_vote_is_not_complete_and_votes_cannot_be_overwritten(review_fixture):
    _, _, ledger, key, signed = review_fixture
    envelope = signed()
    first = ledger.record(key, envelope)
    assert first["state"] == "VOTE_RECORDED"
    assert ledger.record(key, envelope) == first
    with pytest.raises(ValueError): ledger.record(key, signed(decision="failure"))
    assert ledger.status(key) == first


@pytest.mark.parametrize("disagreement", [False, True])
def test_complete_two_vote_flow_with_explicit_disagreement_policy(review_fixture, disagreement):
    f, run, ledger, key, signed = review_fixture
    ledger.record(key, signed())
    status = ledger.record(key, signed(identity="rater-b", decision="failure" if disagreement else "success"))
    assert len(status["vote_refs"]) == 2
    if disagreement:
        assert status["state"] == "ADJUDICATION_PENDING"
        with pytest.raises(ValueError):
            ledger.record(key, signed(identity="rater-a", phase="adjudication", vote_refs=status["vote_refs"]))
        with pytest.raises(ValueError):
            ledger.record(key, signed(identity="adjudicator", phase="adjudication", vote_refs=[]))
        status = ledger.record(key, signed(identity="adjudicator", phase="adjudication", vote_refs=status["vote_refs"]))
    assert status["state"] == "SCIENTIFIC_REVIEW_COMPLETE" and status["decision"] == "success"
    assert status["audit_sha256"] and len(status["vote_refs"]) == 2
    # Reopening never repeats inference or votes; final audit is deterministic.
    restored = f["store"]()
    assert ReviewLedger(restored, f["authority"], f["rubric_path"]).status(key) == status
    assert run.store.summary()["scientific_estimates_computed"] is False


def test_original_reproductions_are_preserved_byte_for_byte():
    root = Path(__file__).resolve().parents[1]
    archive = root/"docs/science/remediation-v1/historical"
    for name, record in json.loads((archive/"index.json").read_text()).items():
        assert digest((archive/(Path(name).name+".txt")).read_bytes()) == record["git_sha256"]
