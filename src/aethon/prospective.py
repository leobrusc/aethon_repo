"""Offline prospective identity, launch gates and continuation-only review.

No model loading, inference, provider calls or scientific campaign entry point.
"""
from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from aethon.generation import GenerationResult
from research_response import asr_bounds

BASELINE = "9ed55709add0fc45f63847a0394315863faa0876"
CONDITIONS = ("B0", "B1", "B2", "B3", "B4")
GATES = ("independent_inventory", "semantic_review", "rubric_review",
         "reviewer_assignment", "private_storage", "hardware_check",
         "model_assets", "execution_authorization")


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Nonempty string required")
    return value


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def sample_identity(namespace, source_id, source_row_id, prompt):
    """Length-safe structured identity; raw and normalized hashes stay distinct."""
    values = [_text(v) for v in (namespace, source_id, source_row_id, prompt)]
    normalized = " ".join(unicodedata.normalize("NFKC", prompt).split())
    return {"sample_id": fingerprint(["aethon.sample.v1", *values[:3],
                                     hashlib.sha256(prompt.encode()).hexdigest()]),
            "raw_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "normalized_sha256": hashlib.sha256(normalized.encode()).hexdigest()}


def case_identity(sample_id, target_revision, condition, replicate, protocol_sha256):
    for value in (sample_id, target_revision, protocol_sha256):
        _text(value)
    if condition not in CONDITIONS or type(replicate) is not int or replicate < 0:
        raise ValueError("Invalid condition or replicate")
    return fingerprint(["aethon.case.v1", sample_id, target_revision,
                        condition, replicate, protocol_sha256])


def validate_fixture(rows):
    identities = []
    for row in rows:
        if row.get("fixture_only") is not True or type(row.get("label")) is not int or row["label"] not in (0, 1):
            raise ValueError("Synthetic development fixture with integer truth required")
        for field in ("task_id", "family_id", "source_id", "source_row_id", "task_rubric_id"):
            _text(row[field])
        if row["label"] and not row.get("attack_objective"):
            raise ValueError("Attack objective required")
        ids = sample_identity("synthetic-fixture-v1", row["source_id"],
                              row["source_row_id"], row["prompt_text"])
        identities.append(ids["sample_id"])
    if not identities or len(set(identities)) != len(identities):
        raise ValueError("Empty or duplicate sample identity")
    return identities


def preflight(manifest, root):
    """Validate the plan and local gate receipts; never authorizes execution."""
    root = Path(root).resolve()
    if manifest.get("schema") != "aethon.prospective-pilot.v1" or manifest.get("baseline") != BASELINE:
        raise ValueError("Unsupported protocol or baseline")
    if manifest.get("conditions") != list(CONDITIONS) or manifest.get("fixture_is_evaluation_data") is not False:
        raise ValueError("All B0-B4 conditions and fixture exclusion required")
    design = manifest["design"]
    if (design["attack_scenarios"], design["legitimate_scenarios"], design["replicates"]) != (12, 12, 1):
        raise ValueError("Pilot design changed; issue a new protocol version")
    if type(manifest["generation"]["seed"]) is not int:
        raise ValueError("Seed must be an integer")
    if manifest["generation"]["temperature"] != 0 or manifest["generation"]["max_new_tokens"] != 256:
        raise ValueError("Unreviewed generation settings")
    blockers = []
    for name, digest in manifest["frozen_files"].items():
        path = (root / name).resolve()
        allowed = digest if isinstance(digest, list) else [digest]
        if root not in path.parents or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() not in allowed:
            blockers.append("frozen_file:" + name)
    for gate in GATES:
        record = manifest["gates"].get(gate, {})
        receipt = record.get("receipt_path")
        digest = record.get("receipt_sha256", "")
        if record.get("status") != "PASS" or not record.get("reviewer_id") or not receipt or not re.fullmatch(r"[0-9a-f]{64}", digest or ""):
            blockers.append(gate)
            continue
        path = Path(receipt)
        if not path.is_absolute() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            blockers.append(gate)
    storage = manifest["private_storage"]
    repository = root.parent.parent if root.parent.name == ".worktrees" else root
    path = Path(storage.get("path") or root).resolve()
    if path == repository or repository in path.parents or not storage.get("custodian"):
        blockers.append("private_destination")
    try:
        if date.fromisoformat(storage.get("delete_after") or "") <= date.today():
            blockers.append("retention")
    except ValueError:
        blockers.append("retention")
    return {"classification": "PILOT_BLOCKED" if blockers else "READY_FOR_PILOT",
            "blockers": sorted(set(blockers)), "campaign_executed": False,
            "manifest_sha256": fingerprint(manifest),
            "note": "Receipt hashes establish identity, not independent approval or permission to execute."}


def review_generated(result, judge, *, prompt, revision, template_sha256, objective, rubric_id):
    """Injected judge sees only decoded new tokens. Payload is private.

    Call only with a trusted generation.v1 driver result. This is not a tokenizer
    redecoder or independent proof that arbitrary serialized text matches IDs.
    """
    if not isinstance(result, GenerationResult) or result.original_prompt != prompt:
        raise ValueError("Structured generation provenance required")
    if not result.input_ids or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Input boundary and exact revision required")
    metadata = result.metadata
    if (metadata.get("revision") != revision or metadata.get("chat_template_sha256") != template_sha256
            or metadata.get("chat_template_applied") is not True):
        raise ValueError("Target revision or template drift")
    if not result.generated_ids or not result.continuation.strip():
        return {"status": "no_response", "requires_review": False}
    if result.stop_reason != "eos":
        return {"status": "indeterminate", "requires_review": True}
    _text(objective); _text(rubric_id)
    judgment = judge(continuation=result.continuation, objective=objective, rubric_id=rubric_id)
    if judgment.get("status") not in {"success", "failure", "indeterminate"}:
        raise ValueError("Invalid objective judgment")
    if judgment["status"] != "indeterminate" and not judgment.get("evidence_ref"):
        raise ValueError("Definitive judgment needs private evidence reference")
    return judgment


def complete_asr(inventory_ids, records):
    """One target/condition/replicate cell, complete frozen attack inventory."""
    if not inventory_ids or len(set(inventory_ids)) != len(inventory_ids):
        raise ValueError("Unique eligible inventory required")
    if set(inventory_ids) != {r["row_id"] for r in records} or len(records) != len(inventory_ids):
        raise ValueError("Missing, duplicate or foreign eligible attack")
    cells = {(r["target_revision"], r["condition"], r["replicate"]) for r in records}
    if len(cells) != 1:
        raise ValueError("Do not pool target/condition/replicate cells")
    return asr_bounds(records)
