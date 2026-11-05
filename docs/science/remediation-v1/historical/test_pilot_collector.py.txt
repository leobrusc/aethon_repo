"""Synthetic software fixtures only. No target inference, ASR or efficacy estimate."""
import base64
import copy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess

import pytest

from aethon.generation import GenerationResult
from aethon.pilot_collector import Collector, make_manifest, no_external_calls, validate_inventory
from aethon.pilot_governance import (Authorization, CLAIMS, KINDS, DISPOSITIONS, OpenSSLVerifier, key_identity,
                                    ReceiptAuthority, authorize, canonical, digest, verify_gates)
from aethon.pilot_storage import (CorruptCheckpoint, PrivateRunStore, immutable_write,
                                 probe_storage, safe_path)
from aethon.prospective import BASELINE, CONDITIONS, fingerprint

REV = "9213176726f574b556790deb65791e0c5aa438b6"
TEMPLATE = "5816fce10444e03c2e9ee1ef8a4a1ea61ae7e69e438613f3b17b69d0426223a4"


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*args, **kwargs): pytest.fail("UNAUTHORIZED NETWORK ATTEMPT")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)


def synthetic_rows():
    return [dict(namespace="SYNTHETIC-ONLY", source_id="fixture", source_row_id=f"{i}-{label}",
                 scenario_id=f"scenario-{i}-{label}", pair_id=f"pair-{i:02d}", family_id=f"family-{i%3}",
                 system_prompt=f"Authorized synthetic task {i}", prompt_text=f"PRIVATE_INPUT_CANARY {i} {label}",
                 label=label, fixture_only=True, task_rubric_id="synthetic-task-v1",
                 legitimate_objective="synthetic authorized task", attack_objective="synthetic override" if label else None,
                 attack_rubric_id="synthetic-objective-v1" if label else None)
            for i in range(12) for label in [0, 1]]


class SyntheticDriver:
    def __init__(self, mode=None):
        self.calls, self.prepares, self.mode, self.decode_calls = 0, 0, mode, []
        self.mutate_at = None

    def prepare(self, messages, config):
        self.prepares += 1
        rendered = messages[0]["content"]+"\n"+messages[1]["content"]+"\nASSISTANT:"
        if self.prepares == self.mutate_at: rendered += "DRIFT"
        return {"input_ids": [ord(c) for c in rendered], "rendered_prompt": rendered}

    def decode(self, ids, **kwargs):
        assert kwargs == {"skip_special_tokens": True, "clean_up_tokenization_spaces": False}
        self.decode_calls.append(list(ids))
        return "".join(chr(i) for i in ids if i != 128009)

    def generate(self, request, config):
        self.calls += 1
        if self.mode == "crash": raise KeyboardInterrupt("synthetic interruption")
        if self.mode == "exception": raise RuntimeError("PRIVATE_INPUT_CANARY")
        if self.mode == "external": socket.create_connection(("should-never-resolve.invalid", 443))
        if self.mode == "missing": return None
        ids = [ord(c) for c in "SYNTHETIC_ANSWER"] + [128009]
        stop = "eos"
        if self.mode == "empty": ids = [128009]
        if self.mode == "truncated": ids = [ord("X")]*256; stop = "length"
        decode = {"skip_special_tokens": True, "clean_up_tokenization_spaces": False}
        metadata = {"revision": config["revision"], "tokenizer_revision": config["tokenizer_revision"],
                    "chat_template_sha256": config["template_sha256"], "chat_template_applied": True,
                    "seed": config["generation"]["seed"], "rendered_prompt": request["rendered_prompt"],
                    "generation": {k: config["generation"][k] for k in ["max_new_tokens", "do_sample", "num_beams", "num_return_sequences", "pad_token_id"]},
                    "effective_eos_token_ids": config["generation"]["eos_token_ids"], "decode": decode,
                    "model_generation_config": {"fixture": "synthetic-generation-config"}}
        for name in ["precision_before", "precision_after"]:
            metadata[name] = {"contract": {"version": "aethon.precision.v1", "device": "cpu", "dtype": "float32"},
                              "floating_parameter_elements_by_dtype": {"torch.float32": 1}, "autocast_enabled": False}
        if self.mode == "revision": metadata["revision"] = "0"*40
        if self.mode == "template": metadata["chat_template_sha256"] = "0"*64
        if self.mode == "parameters": metadata["generation"]["max_new_tokens"] += 1
        if self.mode == "dtype": metadata["precision_after"]["contract"]["dtype"] = "bfloat16"
        continuation = self.decode(ids, **decode)
        full = self.decode(request["input_ids"]+ids, **decode)
        if self.mode == "echo": continuation = full
        result = GenerationResult(request["prompt"], request["input_ids"], ids, continuation, full, stop, metadata)
        if self.mode == "boundary": result = replace(result, input_ids=[0])
        return result


class SyntheticDefenses:
    def __init__(self, blocked=False, divergent=False): self.blocked, self.divergent = blocked, divergent
    def decide(self, row, condition):
        blocked = self.blocked and condition != "B0"
        if self.divergent and condition == "B4": blocked = not blocked
        return {"blocked": blocked, "reason": "synthetic-defender", "noisy_audit_count": 1.25 if condition == "B4" else None}


def synthetic_judge(**kwargs):
    assert set(kwargs) == {"continuation", "objective", "rubric_id"}
    assert "PRIVATE_INPUT_CANARY" not in kwargs["continuation"]
    assert kwargs["continuation"] == "SYNTHETIC_ANSWER"
    return {"status": "indeterminate", "judge_id": "synthetic-test-only", "evidence_ref": None}


@pytest.fixture
def setup_run(tmp_path):
    private = tmp_path/"private"; private.mkdir()
    repo = tmp_path/"repository"; repo.mkdir()
    evidence = tmp_path/"proof.json"
    evidence.write_text(json.dumps({"synthetic_only": True, "schema": "aethon.retention-plan.v1",
                                   "policy_version": "synthetic-v1", "custodian": "SYNTHETIC-CUSTODIAN",
                                   "delete_after": "2099-01-01", "deletion_process": "synthetic-test-only"}))
    proof_sha = digest(evidence.read_bytes())
    config = {"baseline": BASELINE, "revision": REV, "tokenizer_revision": REV,
              "template_sha256": TEMPLATE, "asset_set_sha256": proof_sha,
              "generation": {"seed": 2026, "temperature": 0, "max_new_tokens": 256, "max_input_tokens": 1024,
                             "do_sample": False, "num_beams": 1, "num_return_sequences": 1, "pad_token_id": 128009,
                             "eos_token_ids": [128001, 128008, 128009]},
              "effective_model_generation_config_sha256": fingerprint({"fixture": "synthetic-generation-config"})}
    rows = synthetic_rows()
    subject = {"run_id": "synthetic-run", "baseline": BASELINE, "code_commit": "synthetic-test-only",
               "protocol_sha256": fingerprint(config), "inventory_sha256": fingerprint(rows),
               "storage_root_sha256": fingerprint(str(private.resolve())), "environment_sha256": proof_sha,
               "asset_set_sha256": proof_sha}
    observation = {"status": "PASS", "probe_fingerprint": proof_sha,
                   "observation": {"path_sha256": fingerprint(str(private.resolve())), "synthetic_only": True}}
    technical = {"private_storage": observation, "model_assets": {"status": "PASS", "asset_set_sha256": proof_sha},
                 "hardware_check": {"status": "PASS", "environment_sha256": proof_sha}}
    names = {"steward": "data_steward", "review-a": "scientific_reviewer", "review-b": "scientific_reviewer",
             "lead": "scientific_lead", "custodian": "storage_custodian", "asset": "asset_reviewer",
             "platform": "platform_reviewer", "ops": "operations_authority", "operator": "operator",
             "rater-a": "evaluator", "rater-b": "evaluator", "adjudicator": "evaluator"}
    keys, authorities = {}, {}
    for name, role in names.items():
        keys[name] = hashlib.sha256(("SYNTHETIC-KEY-"+name).encode()).digest()
        path = tmp_path/(name+".key"); path.write_bytes(keys[name])
        authorities[name] = {"roles": [role], "gates": list(KINDS), "public_key_path": str(path), "public_key_sha256": digest(keys[name])}
    policy = {"schema": "aethon.trust-policy.v1", "authorities": authorities}
    policy_path = tmp_path/"trust.json"; policy_path.write_text(json.dumps(policy))
    def fixture_verifier(key, payload, signature):
        return hmac.compare_digest(hmac.new(key, payload, hashlib.sha256).digest(), signature)
    authority = ReceiptAuthority(policy_path, digest(policy_path.read_bytes()), [repo], verifier=fixture_verifier)
    signers = {"independent_inventory": ["steward"], "semantic_review": ["review-a", "review-b"],
               "rubric_review": ["review-a", "review-b"], "reviewer_assignment": ["lead"],
               "private_storage": ["custodian"], "model_assets": ["asset"], "hardware_check": ["platform"],
               "execution_authorization": ["ops"], "launch_intent": ["operator"]}
    def receipt(gate, claims=None, disposition=None):
        claim = {key: proof_sha for key in CLAIMS[gate]}
        if gate == "independent_inventory": claim["inventory_sha256"] = subject["inventory_sha256"]
        if gate == "semantic_review": claim["screen_model_revision"] = "a"*40
        if gate == "reviewer_assignment": claim.update(reviewer_ids=["rater-a", "rater-b"], adjudicator_id="adjudicator")
        if gate == "private_storage": claim.update(probe_fingerprint=proof_sha, custodian="SYNTHETIC-CUSTODIAN", delete_after="2099-01-01")
        if gate == "model_assets": claim["snapshot_path"] = str(tmp_path)
        if gate in {"execution_authorization", "launch_intent"}: claim.update(purpose="bounded_pilot", max_slots=120, max_calls=96)
        if claims: claim.update(claims)
        now = datetime.now(timezone.utc)
        payload = {"schema": "aethon.gate-receipt.v1", "version": "1.0", "gate": gate, "kind": KINDS[gate][0],
                   "disposition": disposition or DISPOSITIONS[KINDS[gate][0]],
                   "subject_sha256": fingerprint(subject), "responsible": signers[gate][0],
                   "issued_at": (now-timedelta(minutes=1)).isoformat(), "expires_at": (now+timedelta(hours=1)).isoformat(),
                   "evidence": [{"path": str(evidence), "sha256": proof_sha}], "claims": claim}
        return {"payload": payload, "signatures": [{"authority_id": name,
                "signature_base64": base64.b64encode(hmac.new(keys[name], canonical(payload), hashlib.sha256).digest()).decode()} for name in signers[gate]]}
    envelopes = {gate: receipt(gate) for gate in CLAIMS if gate != "launch_intent"}
    launch = receipt("launch_intent")
    permission = authorize(authority, envelopes, subject, launch, technical)
    retention = {"custodian": "SYNTHETIC-CUSTODIAN", "delete_after": "2099-01-01"}
    manifest = make_manifest(rows, config, subject, retention)
    def store(): return PrivateRunStore(private, manifest, permission, [repo], observation)
    return dict(rows=rows, config=config, subject=subject, manifest=manifest, permission=permission, store=store,
                private=private, repo=repo, technical=technical, authority=authority, envelopes=envelopes,
                launch=launch, receipt=receipt, policy_path=policy_path, observation=observation)


def collector(fixture, driver=None, defenses=None, judge=synthetic_judge):
    return Collector(fixture["store"](), fixture["rows"], fixture["config"], driver or SyntheticDriver(), defenses or SyntheticDefenses(), judge)


def test_complete_120_slots_and_idempotence(setup_run):
    driver = SyntheticDriver(); first = collector(setup_run, driver)
    assert len(first.store.slots) == 120 and set(s["state"] for s in first.store.slots.values()) == {"pending"}
    summary = first.run()
    assert summary["accounting_complete"] and summary["represented_slots"] == 120 and driver.calls == 96
    assert summary["states"] == {"completed": 96, "reused": 24}
    assert summary["scientific_estimates_computed"] is False
    before = driver.calls
    assert collector(setup_run, driver).run() == summary
    assert driver.calls == before
    assert all(s["decision"] is not None for s in first.store.slots.values())


def test_order_independent_inventory_and_deterministic_schedule(setup_run):
    manifest = make_manifest(list(reversed(setup_run["rows"])), setup_run["config"], setup_run["subject"], setup_run["manifest"]["retention"])
    assert manifest == setup_run["manifest"]
    assert len(set(manifest["schedule"])) == 120


def test_private_events_retain_utc_and_monotonic_timing_provenance(setup_run):
    from aethon.pilot_governance import utc
    from aethon.pilot_storage import unseal
    run = collector(setup_run); run.run(max_slots=1)
    events = [unseal(p.read_bytes()) for p in run.store.events.glob('*.json')]
    assert all(utc(e['recorded_utc']).tzinfo is not None for e in events)
    slot = next(s for s in run.store.slots.values() if s['state'] == 'completed')
    assert slot['generation_elapsed_ns'] >= 0 and slot['evaluation_elapsed_ns'] >= 0


def test_partial_resume_does_not_repeat_completed_calls(setup_run):
    driver = SyntheticDriver()
    first = collector(setup_run, driver); first.run(max_slots=13)
    calls = driver.calls
    assert 0 < calls < 96
    summary = collector(setup_run, driver).run()
    assert driver.calls == 96 and summary["accounting_complete"]


def test_interruption_inference_not_retried_and_all_slots_retained(setup_run):
    driver = SyntheticDriver("crash")
    first = collector(setup_run, driver)
    with pytest.raises(KeyboardInterrupt): first.run()
    assert driver.calls == 1
    driver.mode = None
    second = collector(setup_run, driver); second.run(max_slots=1)
    assert driver.calls == 1
    assert second.store.summary()["states"]["interrupted_unknown"] == 1
    assert len(second.store.slots) == 120


def test_durable_response_reconciles_without_duplicate_inference(setup_run, monkeypatch):
    driver = SyntheticDriver(); first = collector(setup_run, driver)
    original = first.store.transition
    def interrupt(slot, state, **kw):
        if state == "generated": raise KeyboardInterrupt()
        return original(slot, state, **kw)
    monkeypatch.setattr(first.store, "transition", interrupt)
    with pytest.raises(KeyboardInterrupt): first.run()
    assert driver.calls == 1
    second = collector(setup_run, driver); second.run(max_slots=1)
    assert driver.calls == 1
    assert sum(s["state"] == "completed" for s in second.store.slots.values()) == 1


@pytest.mark.parametrize("mode,state", [("missing", "no_response"), ("empty", "no_response"),
    ("truncated", "truncated"), ("exception", "inference_error")])
def test_noncompleted_outputs_are_not_dropped(setup_run, mode, state):
    run = collector(setup_run, SyntheticDriver(mode)); summary = run.run(max_slots=1)
    assert summary["states"][state] == 1 and summary["represented_slots"] == 120
    assert not summary["accounting_complete"]


@pytest.mark.parametrize("mode", ["echo", "boundary", "template", "revision", "parameters", "dtype"])
def test_fail_closed_generation_contracts_and_no_prompt_to_judge(setup_run, mode):
    seen = []
    run = collector(setup_run, SyntheticDriver(mode), judge=lambda **kw: seen.append(kw))
    summary = run.run()
    assert summary["suspended"] and summary["states"]["contract_error"] == 1
    assert not seen and summary["represented_slots"] == 120


def test_every_judged_continuation_is_exact_generated_token_interval(setup_run):
    driver = SyntheticDriver(); seen = []
    def judge(**kw): seen.append(kw["continuation"]); return synthetic_judge(**kw)
    run = collector(setup_run, driver, judge=judge); run.run(max_slots=3)
    assert seen and set(seen) == {"SYNTHETIC_ANSWER"}
    assert [ord(c) for c in "SYNTHETIC_ANSWER"]+[128009] in driver.decode_calls


def test_b3_b4_decision_divergence_refuses_reuse(setup_run):
    run = collector(setup_run, defenses=SyntheticDefenses(divergent=True)); result = run.run()
    assert result["suspended"] == "b3_b4_decision_mismatch"
    failed = next(s for s in run.store.slots.values() if s["state"] == "contract_error")
    assert failed["condition"] == "B4" and failed["reuse"]["verified"] is False


def test_b3_b4_context_divergence_is_not_reused(setup_run):
    by_id = {s["slot_id"]: s for s in setup_run["manifest"]["slots"]}
    index = next(i for i,k in enumerate(setup_run["manifest"]["schedule"]) if by_id[k]["condition"] == "B4")
    driver = SyntheticDriver(); driver.mutate_at = index+1
    run = collector(setup_run, driver); result = run.run()
    assert result["suspended"] == "effective_context_drift"
    assert any(s.get("reuse", {}).get("refused") == "effective_context_drift" for s in run.store.slots.values() if isinstance(s.get("reuse"), dict))


def test_blocked_slots_have_reasons_and_no_inference(setup_run):
    driver = SyntheticDriver(); run = collector(setup_run, driver, SyntheticDefenses(blocked=True)); result = run.run()
    assert result["accounting_complete"] and result["states"]["blocked"] == 96 and driver.calls == 24
    assert all(s["reason"] for s in run.store.slots.values())


def test_evaluation_error_keeps_generation_and_no_private_exception_export(setup_run, capsys):
    def judge(**kwargs): raise RuntimeError("PRIVATE_INPUT_CANARY")
    run = collector(setup_run, judge=judge); result = run.run(max_slots=1)
    assert result["states"]["evaluation_error"] == 1
    slot = next(s for s in run.store.slots.values() if s["state"] == "evaluation_error")
    assert slot["response_ref"] and slot["evaluation_ref"] is None
    assert "PRIVATE_INPUT_CANARY" not in json.dumps(result)+capsys.readouterr().out


def test_no_judge_creates_pending_human_review_not_fake_success(setup_run):
    run = collector(setup_run, judge=None); result = run.run()
    assert result["states"] == {"evaluation_pending": 96, "reused": 24}


def test_unauthorized_network_and_process_calls_are_blocked(setup_run):
    run = collector(setup_run, SyntheticDriver("external")); result = run.run()
    assert result["suspended"] == "unauthorized_external_operation"
    with no_external_calls(), pytest.raises(PermissionError): subprocess.run(["NEVER_EXECUTE"])


def test_atomic_write_collision_and_failure_leave_no_partial_target(tmp_path, monkeypatch):
    path = tmp_path/"object.json"
    def failed(*args): raise OSError("synthetic disk interruption")
    monkeypatch.setattr(os, "link", failed)
    with pytest.raises(OSError): immutable_write(path, b"synthetic")
    assert not path.exists() and not list(tmp_path.glob("*.tmp"))
    monkeypatch.undo()
    immutable_write(path, b"first")
    immutable_write(path, b"first")
    with pytest.raises(CorruptCheckpoint): immutable_write(path, b"replacement")
    assert path.read_bytes() == b"first"


def test_checkpoint_corruption_and_journal_gap_are_rejected(setup_run):
    run = collector(setup_run); run.run(max_slots=1)
    path = next(run.store.objects.glob("*.json")); path.write_bytes(b"corruption")
    with pytest.raises((CorruptCheckpoint, ValueError)): setup_run["store"]()


def test_journal_deletion_in_middle_rejected(setup_run):
    run = collector(setup_run); run.run(max_slots=2)
    (run.store.events/"000002.json").unlink()
    with pytest.raises(CorruptCheckpoint): setup_run["store"]()


def test_fingerprint_change_and_duplicate_identifiers_rejected(setup_run):
    first = setup_run["store"]()
    changed = copy.deepcopy(setup_run["manifest"]); changed["config"]["generation"]["seed"] += 1
    with pytest.raises(CorruptCheckpoint):
        PrivateRunStore(setup_run["private"], changed, setup_run["permission"], [setup_run["repo"]], setup_run["observation"])
    assert first.manifest["config"] == setup_run["manifest"]["config"]
    rows = synthetic_rows(); rows[1] = rows[0]
    with pytest.raises(ValueError): validate_inventory(rows)


def test_valid_checkpoint_copied_from_another_run_is_rejected(setup_run):
    f = setup_run; first = f["store"]()
    reference = first.put({"synthetic_only": True})
    name = "a"*64+".response"
    first.pointer(name, {"reference": reference})
    f["subject"]["run_id"] = "another-synthetic-run"
    envelopes = {gate: f["receipt"](gate) for gate in f["envelopes"]}
    permission = authorize(f["authority"], envelopes, f["subject"], f["receipt"]("launch_intent"), f["technical"])
    manifest = make_manifest(f["rows"], f["config"], f["subject"], f["manifest"]["retention"])
    second = PrivateRunStore(f["private"], manifest, permission, [f["repo"]], f["observation"])
    shutil.copyfile(first.objects/(reference+".json"), second.objects/(reference+".json"))
    shutil.copyfile(first.path/(name+".json"), second.path/(name+".json"))
    with pytest.raises(CorruptCheckpoint): second.get(reference)
    with pytest.raises(CorruptCheckpoint): second.pointer(name)


def test_storage_inside_any_repository_or_worktree_rejected(setup_run):
    other = setup_run["repo"]/"linked"; other.mkdir()
    with pytest.raises(ValueError): safe_path(other, [setup_run["repo"]])
    with pytest.raises(ValueError): safe_path(Path("relative"), [])
    observation = probe_storage(setup_run["private"], [setup_run["repo"]])
    assert observation["status"] in {"PENDING", "PASS"}  # Never enables encryption/ACL.
    bad = copy.deepcopy(setup_run["observation"]); bad["status"] = "PENDING"
    with pytest.raises(PermissionError):
        PrivateRunStore(setup_run["private"], setup_run["manifest"], setup_run["permission"], [setup_run["repo"]], bad)


def test_symlink_storage_rejected_if_platform_supports_it(setup_run, tmp_path, monkeypatch):
    link = tmp_path/"linked-private"
    try: link.symlink_to(setup_run["private"], target_is_directory=True)
    except OSError:
        import stat
        from types import SimpleNamespace
        link.mkdir()
        original = Path.lstat
        monkeypatch.setattr(Path, "lstat", lambda p: SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0) if p == link else original(p))
    with pytest.raises(ValueError): safe_path(link, [])


def test_evaluation_interruption_is_accounted_without_rerating(setup_run):
    calls = []
    def judge(**kwargs): calls.append(True); raise KeyboardInterrupt()
    run = collector(setup_run, judge=judge)
    with pytest.raises(KeyboardInterrupt): run.run()
    resumed = collector(setup_run, judge=lambda **kwargs: pytest.fail("must not repeat uncertain evaluation"))
    result = resumed.run(max_slots=1)
    assert len(calls) == 1 and result["states"]["evaluation_interrupted"] == 1


def test_defense_score_drift_is_refused_even_if_block_decisions_match(setup_run):
    class Scores(SyntheticDefenses):
        def decide(self, row, condition):
            return {**super().decide(row, condition), "ml_score": .2 if condition == "B3" else .3}
    result = collector(setup_run, defenses=Scores()).run()
    assert result["suspended"] == "b3_b4_decision_mismatch"


def test_cli_cannot_load_a_model_without_authorization(monkeypatch, capsys):
    import importlib.util
    script = Path(__file__).resolve().parents[1]/"scripts/prospective_collector.py"
    spec = importlib.util.spec_from_file_location("collector_cli_test", script)
    cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
    monkeypatch.setattr("sys.argv", ["prospective_collector.py", "collect"])
    assert cli.main() == 2
    assert json.loads(capsys.readouterr().out)["classification"] == "PILOT_BLOCKED"


def test_pending_config_preflight_has_all_eight_gates_and_no_execution():
    from aethon.pilot_runtime import inspect_runtime
    root = Path(__file__).resolve().parents[1]
    report, context = inspect_runtime(root)
    assert report["classification"] == "PILOT_BLOCKED" and report["executed"] is False
    assert len(report["gates"]) == 8 and context is None


def test_incomplete_flags_wrong_subject_roles_and_unsigned_receipts_do_not_authorize(setup_run):
    f = setup_run
    for gate in f["envelopes"]:
        missing = dict(f["envelopes"]); missing[gate] = {"approved": True}
        assert verify_gates(f["authority"], missing, f["subject"], f["technical"])["classification"] == "PILOT_BLOCKED"
        with pytest.raises(PermissionError): authorize(f["authority"], missing, f["subject"], f["launch"], f["technical"])
    unsigned = copy.deepcopy(f["envelopes"]); unsigned["semantic_review"]["signatures"] = []
    assert verify_gates(f["authority"], unsigned, f["subject"], f["technical"])["classification"] == "PILOT_BLOCKED"
    subject = dict(f["subject"], run_id="foreign-run")
    assert verify_gates(f["authority"], f["envelopes"], subject, f["technical"])["classification"] == "PILOT_BLOCKED"
    wrong = copy.deepcopy(f["envelopes"]); wrong["rubric_review"] = f["envelopes"]["execution_authorization"]
    assert verify_gates(f["authority"], wrong, f["subject"], f["technical"])["classification"] == "PILOT_BLOCKED"


def test_receipt_presence_does_not_launch_and_capability_cannot_be_constructed_from_flags(setup_run):
    f = setup_run
    report = verify_gates(f["authority"], f["envelopes"], f["subject"], f["technical"])
    assert report["classification"] == "READY_FOR_PILOT_REVIEW" and not report["executed"]
    assert not (f["private"]/"synthetic-run").exists()
    fake = Authorization(fingerprint(f["subject"]), "false", "false", "2099-01-01T00:00:00Z", "false")
    with pytest.raises(PermissionError): fake.check(f["subject"])
    with pytest.raises((ValueError, KeyError)): authorize(f["authority"], f["envelopes"], f["subject"], {"approved": True}, f["technical"])


def test_expiry_evidence_drift_and_trust_anchor_mismatch(setup_run):
    f = setup_run
    altered = copy.deepcopy(f["envelopes"]); altered["model_assets"]["payload"]["expires_at"] = "2000-01-01T00:00:00Z"
    assert verify_gates(f["authority"], altered, f["subject"], f["technical"])["classification"] == "PILOT_BLOCKED"
    with pytest.raises(ValueError): ReceiptAuthority(f["policy_path"], "0"*64, [])
    live = copy.deepcopy(f["technical"]); live["private_storage"]["probe_fingerprint"] = "0"*64
    assert verify_gates(f["authority"], f["envelopes"], f["subject"], live)["classification"] == "PILOT_BLOCKED"


def test_concurrent_writer_lock_not_removed_automatically(setup_run):
    store = setup_run["store"]()
    path = store.path/"writer.lock"; path.write_bytes(b"foreign writer")
    with pytest.raises(FileExistsError):
        with store.writer(): pass
    assert path.read_bytes() == b"foreign writer"


def test_signed_rejection_does_not_become_scientific_approval(setup_run):
    f = setup_run; envelopes = dict(f["envelopes"])
    envelopes["rubric_review"] = f["receipt"]("rubric_review", disposition="rejected")
    assert verify_gates(f["authority"], envelopes, f["subject"], f["technical"])["classification"] == "PILOT_BLOCKED"


def test_two_aliases_of_one_signing_key_are_not_independent_reviewers(setup_run):
    f = setup_run; envelopes = copy.deepcopy(f["envelopes"])
    f["authority"].policy["authorities"]["review-b"] = dict(f["authority"].policy["authorities"]["review-a"])
    envelopes["semantic_review"]["signatures"][1]["signature_base64"] = envelopes["semantic_review"]["signatures"][0]["signature_base64"]
    assert verify_gates(f["authority"], envelopes, f["subject"], f["technical"])["classification"] == "PILOT_BLOCKED"


@pytest.mark.parametrize("mutate_config", [False, True])
def test_request_and_config_mutation_cannot_change_frozen_contract(setup_run, mutate_config):
    class Mutating(SyntheticDriver):
        def generate(self, request, config):
            if mutate_config: config["generation"]["seed"] += 1
            else: request["input_ids"].append(999)
            return super().generate(request, config)
    run = collector(setup_run, Mutating()); result = run.run()
    assert result["suspended"] in {"collector_configuration_changed", "request_fingerprint_changed"}


def test_model_factory_is_locked_and_initialization_failure_keeps_120_slots(setup_run):
    store = setup_run["store"]()
    def factory():
        assert (store.path/"writer.lock").exists()
        raise RuntimeError("synthetic model initialization failure")
    result = Collector(store, setup_run["rows"], setup_run["config"], None, None, factory=factory).run()
    assert result["represented_slots"] == 120 and result["attempted_calls"] == 0
    assert result["suspended"] == "local_adapter_initialization_failed"


def test_production_ed25519_verifier_with_ephemeral_synthetic_key(tmp_path):
    executable = shutil.which("openssl")
    if not executable and Path("C:/Program Files/Git/usr/bin/openssl.exe").exists(): executable = "C:/Program Files/Git/usr/bin/openssl.exe"
    if not executable: pytest.skip("No pinned local OpenSSL executable available")
    key, public, message, signature = [tmp_path/n for n in ["private.pem", "public.pem", "payload.json", "signature.bin"]]
    subprocess.run([executable, "genpkey", "-algorithm", "ED25519", "-out", str(key)], check=True, capture_output=True)
    subprocess.run([executable, "pkey", "-in", str(key), "-pubout", "-out", str(public)], check=True, capture_output=True)
    message.write_bytes(b'{"synthetic_only":true}')
    subprocess.run([executable, "pkeyutl", "-sign", "-rawin", "-inkey", str(key), "-in", str(message), "-out", str(signature)], check=True, capture_output=True)
    verifier = OpenSSLVerifier(str(Path(executable).resolve()), digest(Path(executable).read_bytes()))
    assert verifier(public.read_bytes(), message.read_bytes(), signature.read_bytes())
    assert not verifier(public.read_bytes(), b"tampered", signature.read_bytes())
    assert key_identity(public.read_bytes()) == key_identity(public.read_bytes()+b"\n")
