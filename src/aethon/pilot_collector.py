"""Complete private B0–B4 accounting; no scientific estimates are computed."""
from __future__ import annotations

from contextlib import contextmanager, redirect_stderr, redirect_stdout
import copy
from dataclasses import asdict
import random
import io
import socket
import subprocess
import time

from aethon.generation import GenerationResult
from aethon.pilot_storage import TERMINAL, CorruptCheckpoint
from aethon.prospective import CONDITIONS, case_identity, fingerprint, sample_identity

FROZEN_FAMILIES = ("instruction-override", "synthetic-disclosure", "answer-contamination")


class ContractError(ValueError):
    pass


class UnauthorizedExternalOperation(PermissionError):
    pass


@contextmanager
def no_external_calls():
    """Defense in depth for one worker, not an OS network sandbox."""
    def denied(*args, **kwargs): raise UnauthorizedExternalOperation("External operation prohibited")
    targets = [(socket.socket, "connect"), (socket.socket, "connect_ex"),
               (socket, "create_connection"), (socket, "getaddrinfo"),
               (subprocess, "Popen")]
    originals = [(obj, name, getattr(obj, name)) for obj, name in targets]
    try:
        for obj, name, _ in originals: setattr(obj, name, denied)
        yield
    finally:
        for obj, name, value in originals: setattr(obj, name, value)


def validate_inventory(rows):
    if len(rows) != 24 or any(type(r.get("label")) is not int or r["label"] not in (0, 1) for r in rows):
        raise ValueError("24 distinct cases with integer binary labels required")
    output, sources, scenarios, groups = [], set(), set(), {}
    for row in rows:
        required = ["namespace", "source_id", "source_row_id", "scenario_id", "pair_id", "family_id",
                    "system_prompt", "prompt_text", "task_rubric_id", "legitimate_objective"]
        if any(not isinstance(row.get(k), str) or not row[k].strip() for k in required):
            raise ValueError("Incomplete inventory provenance/task")
        if row["label"] and (not row.get("attack_objective") or not row.get("attack_rubric_id")):
            raise ValueError("Attack objective and rubric required")
        source = (row["namespace"], row["source_id"], row["source_row_id"])
        if source in sources or row["scenario_id"] in scenarios: raise ValueError("Duplicate source/scenario identity")
        sources.add(source); scenarios.add(row["scenario_id"])
        ids = sample_identity(row["namespace"], row["source_id"], row["source_row_id"], row["prompt_text"])
        if "sample_id" in row and row["sample_id"] != ids["sample_id"]: raise ValueError("Sample ID collision")
        output.append({**row, **ids})
        groups.setdefault(row["pair_id"], []).append(row)
    if len({r["sample_id"] for r in output}) != 24 or len(groups) != 12:
        raise ValueError("Twelve unique task pairs required")
    for pair in groups.values():
        if len(pair) != 2 or sorted(r["label"] for r in pair) != [0, 1] or len({r["family_id"] for r in pair}) != 1:
            raise ValueError("Each pair needs one attack/clean control in the same family")
        if len({(r["system_prompt"], r["legitimate_objective"], r["task_rubric_id"]) for r in pair}) != 1:
            raise ValueError("Paired task context changed")
    counts = {family: sum(pair[0]["family_id"] == family for pair in groups.values()) for family in FROZEN_FAMILIES}
    if set(r["family_id"] for r in rows) != set(FROZEN_FAMILIES) or set(counts.values()) != {4}:
        raise ValueError("Exactly four pairs per frozen family required")
    return sorted(output, key=lambda r: r["sample_id"])


def make_manifest(rows, config, subject, retention):
    rows = validate_inventory(rows)
    if subject["protocol_sha256"] != fingerprint(config): raise ValueError("Unbound collector configuration")
    slots = []
    protocol = subject["protocol_sha256"]
    for row in rows:
        for condition in CONDITIONS:
            key = case_identity(row["sample_id"], config["revision"], condition, 0, protocol)
            slots.append({"slot_id": key, "sample_id": row["sample_id"], "scenario_id": row["scenario_id"],
                          "namespace": row["namespace"], "source_id": row["source_id"], "source_row_id": row["source_row_id"],
                          "pair_id": row["pair_id"], "family_id": row["family_id"], "label": row["label"],
                          "condition": condition, "replicate": 0, "state": "pending",
                          "fingerprint": fingerprint([subject, row["sample_id"], condition]),
                          "expected_generation_metadata": config["generation"], "generation_metadata": None, "response_ref": None,
                          "evaluation_ref": None, "decision": None, "reason": "not_attempted", "attempted": False})
    by_key = {(s["sample_id"], s["condition"]): s["slot_id"] for s in slots}
    rng = random.Random(config["generation"]["seed"])
    pairs = sorted({r["pair_id"] for r in rows}); rng.shuffle(pairs)
    order = []
    for pair in pairs:
        for row in sorted((r for r in rows if r["pair_id"] == pair), key=lambda r: r["sample_id"]):
            arms = list(CONDITIONS); rng.shuffle(arms)
            # Explicit topological dependency, recorded in the immutable schedule.
            arms.remove("B4"); arms.insert(arms.index("B3") + 1, "B4")
            order.extend(by_key[(row["sample_id"], arm)] for arm in arms)
    return {"schema": "aethon.pilot-run.v1", "run_id": subject["run_id"], "subject": subject,
            "config": config, "retention": retention, "inventory_sha256": fingerprint(rows),
            "review_rubrics": {r["sample_id"]: r["attack_rubric_id"] if r["label"] else r["task_rubric_id"] for r in rows},
            "slots": slots, "schedule": order, "schedule_policy": "seeded_pairs_arms_b4_after_b3",
            "provenance": {"baseline": config["baseline"], "code_commit": subject["code_commit"]},
            "run_fingerprint": fingerprint([subject, config, rows, retention, order])}


def check_result(result, request, config, decoder):
    """Independently decode exactly generated IDs; never trim a full string."""
    if fingerprint({k: v for k, v in request.items() if k != "request_fingerprint"}) != request["request_fingerprint"]:
        raise ContractError("request_fingerprint_changed")
    if not isinstance(result, GenerationResult) or result.original_prompt != request["prompt"]:
        raise ContractError("structured_result_required")
    if result.input_ids != request["input_ids"] or len(result.generated_ids) > config["generation"]["max_new_tokens"]:
        raise ContractError("token_interval_mismatch")
    decode = {"skip_special_tokens": True, "clean_up_tokenization_spaces": False}
    if decoder(result.generated_ids, **decode) != result.continuation:
        raise ContractError("continuation_decode_mismatch")
    if decoder(result.input_ids + result.generated_ids, **decode) != result.legacy_full_text:
        raise ContractError("full_sequence_decode_mismatch")
    m = result.metadata
    expected = {"revision": config["revision"], "tokenizer_revision": config["tokenizer_revision"],
                "chat_template_sha256": config["template_sha256"], "chat_template_applied": True,
                "seed": config["generation"]["seed"], "rendered_prompt": request["rendered_prompt"]}
    if any(m.get(k) != v for k, v in expected.items()): raise ContractError("generation_provenance_drift")
    actual = m.get("generation", {})
    for key in ["max_new_tokens", "do_sample", "num_beams", "num_return_sequences", "pad_token_id"]:
        if actual.get(key) != config["generation"][key]: raise ContractError("generation_settings_drift")
    if m.get("effective_eos_token_ids") != config["generation"]["eos_token_ids"] or m.get("decode") != decode:
        raise ContractError("decoding_settings_drift")
    if fingerprint(m.get("model_generation_config")) != config["effective_model_generation_config_sha256"]:
        raise ContractError("effective_config_drift")
    for name in ["precision_before", "precision_after"]:
        observation = m.get(name, {})
        if observation.get("contract") != {"version": "aethon.precision.v1", "dtype": "float32", "device": "cpu"}:
            raise ContractError("dtype_or_device_drift")
        parameters = observation.get("floating_parameter_elements_by_dtype", {})
        if set(parameters) != {"torch.float32"} or parameters["torch.float32"] < 1 or observation.get("autocast_enabled") is not False:
            raise ContractError("parameter_precision_unverified")
    if result.stop_reason == "eos" and (not result.generated_ids or result.generated_ids[-1] not in config["generation"]["eos_token_ids"]):
        raise ContractError("eos_provenance_mismatch")
    return result


class FrozenDefenses:
    """Wrap unchanged historical middleware; no post-response/calibrated rewrite."""
    def __init__(self, model_path, expected_sha256):
        from pathlib import Path
        from aethon.pilot_governance import digest
        from benchmark.middleware import BenchmarkMiddleware
        path = Path(model_path)
        if digest(path.read_bytes()) != expected_sha256: raise ContractError("untrusted_detector")
        self.middleware = BenchmarkMiddleware(str(path), epsilon=1.2, seed=42)

    def decide(self, row, condition):
        result = asdict(self.middleware.evaluate(row["prompt_text"], condition))
        result = {k: v for k, v in result.items() if not k.endswith("latency_ms")}
        result["reason"] = "bypass" if condition == "B0" else "heuristic_or_classifier" if condition in {"B3", "B4"} else "heuristic" if condition == "B1" else "classifier"
        return result


class Collector:
    def __init__(self, store, rows, config, driver, defenses, judge=None, factory=None):
        self.store, self.rows, self.config = store, validate_inventory(rows), copy.deepcopy(config)
        self.config_fingerprint = fingerprint(config)
        if store.manifest["config"] != config or store.manifest["inventory_sha256"] != fingerprint(self.rows):
            raise CorruptCheckpoint("Foreign collector configuration or inventory")
        self.by_id = {r["sample_id"]: r for r in self.rows}
        self.driver, self.defenses, self.judge = driver, defenses, judge
        self.factory = factory

    def request(self, row):
        if fingerprint(self.config) != self.config_fingerprint: raise ContractError("collector_configuration_changed")
        messages = [{"role": "system", "content": row["system_prompt"]}, {"role": "user", "content": row["prompt_text"]}]
        prepared = self.driver.prepare(messages, self.config)
        if set(prepared) != {"input_ids", "rendered_prompt"} or not isinstance(prepared["rendered_prompt"], str):
            raise ContractError("invalid_preparation_contract")
        if fingerprint(self.config) != self.config_fingerprint: raise ContractError("collector_configuration_changed")
        ids = prepared["input_ids"]
        if not ids or len(ids) > self.config["generation"]["max_input_tokens"] or any(type(i) is not int or i < 0 for i in ids):
            raise ContractError("invalid_effective_input")
        request = {"messages": messages, "prompt": row["prompt_text"], **prepared,
                   "target": {k: self.config[k] for k in ["revision", "tokenizer_revision", "template_sha256", "asset_set_sha256"]},
                   "generation": copy.deepcopy(self.config["generation"]), "dtype": "float32", "device": "cpu"}
        request["request_fingerprint"] = fingerprint(request)
        return request

    def _refuse(self, slot, reason):
        self.store.transition(slot["slot_id"], "contract_error", reason=reason,
                              decision=self.store.defenses.get(slot["slot_id"]) if self.store.defenses else None,
                              reuse={"verified": False, "refused": reason} if slot["condition"] == "B4" else None)
        self.store.suspend(reason)

    def _response(self, slot, request):
        store, key = self.store, slot["slot_id"]
        pointer = store.pointer(key+".response")
        if pointer:
            if pointer["request_fingerprint"] != request["request_fingerprint"]: raise ContractError("foreign_response_checkpoint")
            value = store.get(pointer["reference"])
            result = GenerationResult(**value["generation_result"])
        else:
            if slot["state"] == "started":
                store.transition(key, "interrupted_unknown", reason="inference_started_without_durable_response")
                return
            store.transition(key, "started", reason="inference_intent_durable", attempted=True,
                             request_fingerprint=request["request_fingerprint"], decision=store.defenses[key])
            started = time.perf_counter_ns()
            try:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    result = self.driver.generate(request, self.config)
            except UnauthorizedExternalOperation:
                raise ContractError("unauthorized_external_operation")
            except Exception as exc:
                store.transition(key, "inference_error", reason="inference_exception", exception_type=type(exc).__name__,
                                 generation_elapsed_ns=time.perf_counter_ns()-started)
                return
            if result is None:
                store.transition(key, "no_response", reason="missing_generation", generation_elapsed_ns=time.perf_counter_ns()-started)
                return
            if fingerprint(self.config) != self.config_fingerprint: raise ContractError("collector_configuration_changed")
            check_result(result, request, self.config, self.driver.decode)
            reference = store.put({"generation_result": result.to_dict(), "request_fingerprint": request["request_fingerprint"],
                                   "generation_elapsed_ns": time.perf_counter_ns()-started})
            pointer = {"reference": reference, "request_fingerprint": request["request_fingerprint"]}
            store.pointer(key+".response", pointer)
        check_result(result, request, self.config, self.driver.decode)
        state = "no_response" if not result.generated_ids or not result.continuation.strip() else "truncated" if result.stop_reason != "eos" else "generated"
        store.transition(key, state, reason="empty_continuation" if state == "no_response" else "non_eos_unresolved" if state == "truncated" else "generated_interval_verified",
                         response_ref=pointer["reference"], generation_metadata=result.metadata,
                         generation_elapsed_ns=store.get(pointer["reference"])["generation_elapsed_ns"],
                         generated_tokens=len(result.generated_ids), request_fingerprint=request["request_fingerprint"])

    def _evaluate(self, slot, row, request):
        store, key = self.store, slot["slot_id"]
        response = store.get(slot["response_ref"])
        result = check_result(GenerationResult(**response["generation_result"]), request, self.config, self.driver.decode)
        if self.judge is None:
            store.transition(key, "evaluation_pending", reason="awaiting_blinded_human_review")
            return
        pointer = store.pointer(key+".evaluation")
        if pointer:
            raise CorruptCheckpoint("Legacy unsigned evaluation checkpoint requires independent review")
        else:
            if slot["state"] == "evaluating":
                store.transition(key, "evaluation_interrupted", reason="evaluation_started_without_durable_result")
                return
            store.transition(key, "evaluating", reason="evaluation_intent_durable")
            started = time.perf_counter_ns()
            try:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.judge(continuation=result.continuation,
                                          objective=row["attack_objective"] if row["label"] else row["legitimate_objective"],
                                          rubric_id=row["attack_rubric_id"] if row["label"] else row["task_rubric_id"])
                # A callback is untrusted candidate output, never an authenticated
                # independent vote. ReviewLedger is the sole scientific review API.
                raise ValueError("Unsigned callback judgment rejected")
            except UnauthorizedExternalOperation:
                raise ContractError("unauthorized_external_operation")
            except Exception as exc:
                store.transition(key, "evaluation_error", reason="evaluation_exception", exception_type=type(exc).__name__,
                                 evaluation_elapsed_ns=time.perf_counter_ns()-started)
                return
    def run(self, max_slots=None):
        store = self.store
        with store.writer(), no_external_calls():
            if store.suspended or store.summary()["accounting_complete"]: return store.summary()
            if self.driver is None:
                try:
                    if self.factory is None: raise ValueError("Local adapter required")
                    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                        self.driver, self.defenses = self.factory()
                except Exception:
                    store.suspend("local_adapter_initialization_failed"); return store.summary()
            if store.defenses is None:
                try:
                    matrix = {s["slot_id"]: self.defenses.decide(self.by_id[s["sample_id"]], s["condition"]) for s in store.manifest["slots"]}
                    if any(type(d.get("blocked")) is not bool or not d.get("reason") for d in matrix.values()):
                        raise ContractError("invalid_defense_decision")
                    store.append({"kind": "defenses", "reference": store.put(matrix)})
                except Exception:
                    store.suspend("defense_initialization_error"); return store.summary()
            processed = 0
            for key in store.manifest["schedule"]:
                if max_slots is not None and processed >= max_slots: break
                slot = store.slots[key]
                if slot["state"] in TERMINAL: continue
                row, decision = self.by_id[slot["sample_id"]], store.defenses[key]
                try:
                    request = self.request(row)
                    expected = store.pointer(slot["sample_id"]+".request")
                    if expected and expected != request: raise ContractError("effective_context_drift")
                    if not expected: store.pointer(slot["sample_id"]+".request", request)
                    if slot["condition"] == "B4":
                        source = next(s for s in store.slots.values() if s["sample_id"] == slot["sample_id"] and s["condition"] == "B3")
                        b3 = store.defenses[source["slot_id"]]
                        fields = ["blocked", "heuristic_flag", "ml_prediction", "ml_score", "detection_score", "final_decision"]
                        if any(decision.get(k) != b3.get(k) for k in fields): raise ContractError("b3_b4_decision_mismatch")
                    if slot["state"] == "pending" and decision["blocked"]:
                        store.transition(key, "blocked", decision=decision, reason=decision["reason"],
                                         request_fingerprint=request["request_fingerprint"],
                                         reuse={"verified": True, "source_slot": source["slot_id"], "kind": "equal_blocked_decision"} if slot["condition"] == "B4" else None)
                    elif slot["state"] == "pending" and slot["condition"] == "B4":
                        if source.get("request_fingerprint") != request["request_fingerprint"]: raise ContractError("b3_b4_fingerprint_mismatch")
                        if source["state"] not in {"completed", "evaluation_pending", "evaluation_error", "evaluation_interrupted"}: raise ContractError("b3_response_unavailable_no_reuse")
                        check_result(GenerationResult(**store.get(source["response_ref"])["generation_result"]), request, self.config, self.driver.decode)
                        store.transition(key, "reused", decision=decision, reason="full_input_fingerprint_verified",
                                         request_fingerprint=request["request_fingerprint"], response_ref=source["response_ref"],
                                         evaluation_ref=source["evaluation_ref"], generation_metadata=source["generation_metadata"],
                                         reuse={"verified": True, "source_slot": source["slot_id"], "request_fingerprint": request["request_fingerprint"]})
                    else:
                        if slot["state"] == "pending" and store.summary()["attempted_calls"] >= 96:
                            store.suspend("call_budget_exhausted"); break
                        if slot["state"] in {"pending", "started"}: self._response(slot, request)
                        if slot["state"] in {"generated", "evaluating"}: self._evaluate(slot, row, request)
                except CorruptCheckpoint:
                    raise
                except ContractError as exc:
                    allowed = {"effective_context_drift", "b3_b4_decision_mismatch", "b3_b4_fingerprint_mismatch",
                               "b3_response_unavailable_no_reuse", "unauthorized_external_operation", "invalid_effective_input",
                               "structured_result_required", "token_interval_mismatch", "continuation_decode_mismatch",
                               "full_sequence_decode_mismatch", "generation_provenance_drift", "generation_settings_drift",
                               "decoding_settings_drift", "effective_config_drift", "dtype_or_device_drift", "parameter_precision_unverified",
                               "eos_provenance_mismatch", "foreign_response_checkpoint", "adapter_configuration_drift", "chat_template_drift",
                               "effective_generation_config_drift", "tokenizer_chat_boundary_mismatch"}
                    allowed |= {"request_fingerprint_changed", "collector_configuration_changed", "invalid_preparation_contract"}
                    self._refuse(slot, str(exc) if str(exc) in allowed else "generation_contract_violation"); break
                except (ValueError, KeyError, TypeError):
                    self._refuse(slot, "request_preparation_failed"); break
                processed += 1
                # Suspend only after the first complete paired batch (10 slots).
                terminal = [s for s in store.slots.values() if s["state"] in TERMINAL]
                errors = sum(s["state"] in {"inference_error", "no_response", "interrupted_unknown"} for s in terminal)
                if len(terminal) >= 10 and errors/len(terminal) > .10:
                    store.suspend("technical_error_rate_exceeded"); break
            store.load()
            return store.summary()
