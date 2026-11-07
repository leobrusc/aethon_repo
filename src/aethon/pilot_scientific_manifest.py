"""Shared, backend-independent validation for the frozen prospective run schema.

This module validates the full authenticated inventory bytes before any storage
backend is allowed to mint a RunCapability. It contains no filesystem or model I/O.
"""
from __future__ import annotations

import base64
import binascii
from datetime import date
import json
import random
import re
from typing import Any

from aethon.pilot_governance import canonical, digest
from aethon.prospective import BASELINE, CONDITIONS, case_identity, fingerprint, sample_identity

FROZEN_FAMILIES = ("instruction-override", "synthetic-disclosure", "answer-contamination")
RUN_SCHEMA = "aethon.pilot-run.v2"
RUN_IDENTITY_ALGORITHM = "fingerprint-v1:[subject,config,validated_rows,retention,order]"
SCHEDULE_POLICY = "seeded_pairs_arms_b4_after_b3"

_ROW_REQUIRED = {"namespace", "source_id", "source_row_id", "scenario_id", "pair_id", "family_id",
                 "system_prompt", "prompt_text", "label", "task_rubric_id", "legitimate_objective"}
_ROW_OPTIONAL = {"fixture_only", "attack_objective", "attack_rubric_id", "sample_id", "raw_sha256",
                 "normalized_sha256"}
_SLOT_FIELDS = {"slot_id", "sample_id", "scenario_id", "namespace", "source_id", "source_row_id",
                "pair_id", "family_id", "label", "condition", "replicate", "state", "fingerprint",
                "expected_generation_metadata", "generation_metadata", "response_ref", "evaluation_ref",
                "decision", "reason", "attempted"}
_MANIFEST_FIELDS = {"schema", "run_identity_algorithm", "run_id", "subject", "config", "retention",
                    "inventory_sha256", "inventory_source_b64", "review_rubrics", "slots", "schedule",
                    "schedule_policy", "provenance", "run_fingerprint", "authorization_provenance"}


class ScientificManifestError(ValueError):
    """A manifest does not encode the exact frozen prospective design."""


def _reject_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ScientificManifestError("Duplicate JSON key")
        result[key] = value
    return result


def _parse_json(raw: bytes):
    try:
        return json.loads(raw, object_pairs_hook=_reject_duplicate_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(ScientificManifestError("Nonfinite JSON")))
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, ScientificManifestError):
            raise
        raise ScientificManifestError("Invalid inventory JSON") from exc


def validate_inventory(rows):
    """Validate, derive and canonically order the 24 frozen cases."""
    if not isinstance(rows, list) or len(rows) != 24:
        raise ScientificManifestError("Exactly 24 cases required")
    output, sources, scenarios, groups = [], set(), set(), {}
    for row in rows:
        if not isinstance(row, dict) or not _ROW_REQUIRED <= row.keys() or row.keys() - (_ROW_REQUIRED | _ROW_OPTIONAL):
            raise ScientificManifestError("Unknown or missing inventory fields")
        if type(row["label"]) is not int or row["label"] not in (0, 1):
            raise ScientificManifestError("Integer binary label required")
        for field in _ROW_REQUIRED - {"label"}:
            if not isinstance(row[field], str) or not row[field].strip():
                raise ScientificManifestError("Nonempty string required: " + field)
        if row["label"] == 1:
            if any(not isinstance(row.get(k), str) or not row[k].strip() for k in ("attack_objective", "attack_rubric_id")):
                raise ScientificManifestError("Attack objective and rubric required")
        elif any(row.get(k) is not None for k in ("attack_objective", "attack_rubric_id")):
            raise ScientificManifestError("Control row cannot carry attack-only objective/rubric")
        if "fixture_only" in row and type(row["fixture_only"]) is not bool:
            raise ScientificManifestError("fixture_only must be boolean")
        source = (row["namespace"], row["source_id"], row["source_row_id"])
        if source in sources or row["scenario_id"] in scenarios:
            raise ScientificManifestError("Duplicate source or scenario identity")
        sources.add(source)
        scenarios.add(row["scenario_id"])
        ids = sample_identity(row["namespace"], row["source_id"], row["source_row_id"], row["prompt_text"])
        for field, value in ids.items():
            if field in row and row[field] != value:
                raise ScientificManifestError("Supplied sample identity disagrees with source fields")
        output.append({**row, **ids})
        groups.setdefault(row["pair_id"], []).append(row)
    if len({r["sample_id"] for r in output}) != 24 or len(groups) != 12:
        raise ScientificManifestError("Exactly 24 unique samples and 12 pairs required")
    family_pair_counts = {family: 0 for family in FROZEN_FAMILIES}
    for pair in groups.values():
        if len(pair) != 2 or sorted(r["label"] for r in pair) != [0, 1]:
            raise ScientificManifestError("Each pair needs exactly one attack and one control")
        if pair[0]["family_id"] != pair[1]["family_id"]:
            raise ScientificManifestError("Pair family mismatch")
        family = pair[0]["family_id"]
        if family not in family_pair_counts:
            raise ScientificManifestError("Unknown frozen family")
        family_pair_counts[family] += 1
        if len({(r["system_prompt"], r["legitimate_objective"], r["task_rubric_id"]) for r in pair}) != 1:
            raise ScientificManifestError("Paired scientific task context differs")
    if set(family_pair_counts) != set(r["family_id"] for r in rows) or set(family_pair_counts.values()) != {4}:
        raise ScientificManifestError("Exactly four pairs in each frozen family required")
    return sorted(output, key=lambda row: row["sample_id"])


def _schedule(rows, config):
    generation = config.get("generation")
    if not isinstance(generation, dict) or type(generation.get("seed")) is not int:
        raise ScientificManifestError("Integer frozen generation seed required")
    by_key = {}
    for row in rows:
        for condition in CONDITIONS:
            by_key[(row["sample_id"], condition)] = case_identity(
                row["sample_id"], config["revision"], condition, 0, fingerprint(config))
    rng = random.Random(generation["seed"])
    pairs = sorted({row["pair_id"] for row in rows})
    rng.shuffle(pairs)
    order = []
    for pair in pairs:
        for row in sorted((r for r in rows if r["pair_id"] == pair), key=lambda r: r["sample_id"]):
            arms = list(CONDITIONS)
            rng.shuffle(arms)
            arms.remove("B4")
            arms.insert(arms.index("B3") + 1, "B4")
            order.extend(by_key[(row["sample_id"], arm)] for arm in arms)
    return order


def _slots(rows, subject, config):
    result = []
    for row in rows:
        for condition in CONDITIONS:
            result.append({"slot_id": case_identity(row["sample_id"], config["revision"], condition, 0,
                                                      subject["protocol_sha256"]),
                           "sample_id": row["sample_id"], "scenario_id": row["scenario_id"],
                           "namespace": row["namespace"], "source_id": row["source_id"],
                           "source_row_id": row["source_row_id"], "pair_id": row["pair_id"],
                           "family_id": row["family_id"], "label": row["label"],
                           "condition": condition, "replicate": 0, "state": "pending",
                           "fingerprint": fingerprint([subject, row["sample_id"], condition]),
                           "expected_generation_metadata": config["generation"], "generation_metadata": None,
                           "response_ref": None, "evaluation_ref": None, "decision": None,
                           "reason": "not_attempted", "attempted": False})
    if any(set(slot) != _SLOT_FIELDS for slot in result):
        raise ScientificManifestError("Internal frozen slot schema mismatch")
    return result


def build_manifest(rows, config, subject, retention, inventory_raw: bytes):
    """Build schema v2 while retaining the exact historical run fingerprint formula."""
    if type(inventory_raw) is not bytes:
        raise ScientificManifestError("Exact authorized inventory bytes required")
    source = _parse_json(inventory_raw)
    if (not isinstance(source, dict) or set(source) != {"schema", "rows"}
            or source.get("schema") != "aethon.private-inventory.v1" or not isinstance(source.get("rows"), list)):
        raise ScientificManifestError("Versioned private inventory required")
    validated = validate_inventory(source["rows"])
    supplied = validate_inventory(rows)
    if validated != supplied:
        raise ScientificManifestError("Rows differ from exact source inventory")
    if digest(inventory_raw) != subject.get("inventory_sha256"):
        raise ScientificManifestError("Source inventory bytes are not the authorized inventory")
    if not isinstance(config, dict) or config.get("baseline") != BASELINE or subject.get("protocol_sha256") != fingerprint(config):
        raise ScientificManifestError("Configuration does not match frozen subject")
    if (not isinstance(retention, dict) or set(retention) != {"custodian", "delete_after"}
            or not isinstance(retention.get("custodian"), str) or not retention["custodian"].strip()):
        raise ScientificManifestError("Concrete retention schema required")
    try:
        if date.fromisoformat(retention["delete_after"]) <= date.today():
            raise ScientificManifestError("Retention already expired")
    except (TypeError, ValueError) as exc:
        raise ScientificManifestError("Valid retention date required") from exc
    if (not isinstance(subject.get("run_id"), str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", subject["run_id"]) is None
            or subject.get("baseline") != BASELINE or not isinstance(subject.get("code_commit"), str)
            or not subject["code_commit"]):
        raise ScientificManifestError("Run identity missing")
    slots = _slots(validated, subject, config)
    order = _schedule(validated, config)
    review_rubrics = {row["sample_id"]: row["attack_rubric_id"] if row["label"] else row["task_rubric_id"]
                      for row in validated}
    return {"schema": RUN_SCHEMA, "run_identity_algorithm": RUN_IDENTITY_ALGORITHM,
            "run_id": subject["run_id"], "subject": subject, "config": config, "retention": retention,
            "inventory_sha256": fingerprint(validated),
            "inventory_source_b64": base64.b64encode(inventory_raw).decode("ascii"),
            "review_rubrics": review_rubrics, "slots": slots, "schedule": order,
            "schedule_policy": SCHEDULE_POLICY,
            "provenance": {"baseline": config["baseline"], "code_commit": subject["code_commit"]},
            "run_fingerprint": fingerprint([subject, config, validated, retention, order])}


def validate_manifest_document(manifest: Any):
    """Validate exact schema, source inventory, complete identities and frozen schedule."""
    if not isinstance(manifest, dict) or set(manifest) != _MANIFEST_FIELDS:
        raise ScientificManifestError("Unknown or missing run manifest fields")
    if manifest["schema"] != RUN_SCHEMA or manifest["run_identity_algorithm"] != RUN_IDENTITY_ALGORITHM:
        raise ScientificManifestError("Unsupported run manifest identity version")
    try:
        raw = base64.b64decode(manifest["inventory_source_b64"], validate=True)
    except (TypeError, ValueError, binascii.Error) as exc:
        raise ScientificManifestError("Invalid source inventory encoding") from exc
    source = _parse_json(raw)
    if (not isinstance(source, dict) or set(source) != {"schema", "rows"}
            or source.get("schema") != "aethon.private-inventory.v1" or not isinstance(source.get("rows"), list)):
        raise ScientificManifestError("Invalid source inventory document")
    rows = validate_inventory(source["rows"])
    subject, config, retention = manifest["subject"], manifest["config"], manifest["retention"]
    if not isinstance(subject, dict) or digest(raw) != subject.get("inventory_sha256"):
        raise ScientificManifestError("Inventory bytes do not match authorized subject")
    if (not isinstance(subject.get("run_id"), str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", subject["run_id"]) is None
            or subject.get("baseline") != BASELINE or not isinstance(subject.get("code_commit"), str)
            or not subject["code_commit"]):
        raise ScientificManifestError("Invalid subject identity")
    if not isinstance(config, dict) or subject.get("protocol_sha256") != fingerprint(config) or config.get("baseline") != BASELINE:
        raise ScientificManifestError("Frozen config/subject binding mismatch")
    if manifest["run_id"] != subject.get("run_id"):
        raise ScientificManifestError("Run ID differs from subject")
    expected_retention = build_retention(retention)
    slots = _slots(rows, subject, config)
    order = _schedule(rows, config)
    if manifest["schedule_policy"] != SCHEDULE_POLICY or manifest["schedule"] != order:
        raise ScientificManifestError("Schedule differs from exact seeded frozen schedule")
    if manifest["slots"] != slots:
        raise ScientificManifestError("Slots differ from validated inventory projection")
    if len({s["slot_id"] for s in slots}) != 120 or len({s["sample_id"] for s in slots}) != 24:
        raise ScientificManifestError("Unique 24-case/120-slot matrix required")
    if manifest["inventory_sha256"] != fingerprint(rows):
        raise ScientificManifestError("Canonical inventory digest mismatch")
    rubrics = {row["sample_id"]: row["attack_rubric_id"] if row["label"] else row["task_rubric_id"] for row in rows}
    if manifest["review_rubrics"] != rubrics:
        raise ScientificManifestError("Review rubric projection mismatch")
    if manifest["provenance"] != {"baseline": config["baseline"], "code_commit": subject["code_commit"]}:
        raise ScientificManifestError("Run provenance projection mismatch")
    expected_fp = fingerprint([subject, config, rows, expected_retention, order])
    if manifest["run_fingerprint"] != expected_fp:
        raise ScientificManifestError("Run fingerprint does not match exact identity formula")
    return rows


def build_retention(retention):
    if (not isinstance(retention, dict) or set(retention) != {"custodian", "delete_after"}
            or not isinstance(retention.get("custodian"), str) or not retention["custodian"].strip()):
        raise ScientificManifestError("Concrete retention schema required")
    try:
        if date.fromisoformat(retention["delete_after"]) <= date.today():
            raise ScientificManifestError("Retention already expired")
    except (TypeError, ValueError) as exc:
        raise ScientificManifestError("Valid retention date required") from exc
    return retention
