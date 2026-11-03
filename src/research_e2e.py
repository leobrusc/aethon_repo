"""Pair B0/B3 inference from frozen detector decisions, with private responses.

No provider is contacted by importing this module. A driver is explicitly injected.
The private destination must be prepared with restrictive OS permissions by the
operator; this module refuses to write raw responses inside the repository.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from benchmark.asr import NON_RESPONSE_PREFIXES
from baseline_reliability import atomic_write

ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERN = re.compile(r"(?:sk-[A-Za-z0-9_-]{16,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")


def validate_private_destination(path, retention):
    destination = Path(path).resolve()
    if destination == ROOT or ROOT in destination.parents:
        raise ValueError("Full responses must be outside repository")
    from datetime import date
    if not retention.get("custodian") or date.fromisoformat(retention["delete_after"]) <= date.today():
        raise ValueError("Named custodian and future deletion date required")
    if retention.get("access_control_verified") is not True:
        raise ValueError("Operator must verify private directory access controls")
    return destination


def run_pairs(rows, driver, private_output, *, retention, temperature=0., max_tokens=256):
    """Rows carry source objective, frozen B3 decision and true label.

    Checkpoints live privately; returned rows carry no prompt or response text.
    Immutable content/config hashes prevent reuse across incompatible settings.
    Remaining response judgments require separate objective-based annotation.
    """
    destination = validate_private_destination(private_output, retention)
    if max_tokens < 1 or temperature != 0:
        raise ValueError("Current paired protocol requires temperature zero and positive token limit")
    if len({r["row_id"] for r in rows}) != len(rows): raise ValueError("Duplicate row identity")
    if not retention.get("target_revision") or not retention.get("detector_sha256"):
        raise ValueError("Pinned target revision and frozen detector hash required for safe resume")
    configuration = {"temperature": temperature, "max_tokens": max_tokens,
                     "driver": getattr(driver, "NAME", type(driver).__name__),
                     "retention": retention, "rows": rows}
    fp = hashlib.sha256(json.dumps(configuration, sort_keys=True).encode()).hexdigest()
    marker = destination/"private_manifest.json"
    if marker.exists() and json.loads(marker.read_text(encoding="utf-8"))["fingerprint"] != fp:
        raise ValueError("Private checkpoint configuration changed")
    atomic_write(marker, json.dumps({"fingerprint": fp, "retention": retention, "status": "PARTIAL"}, indent=2))
    public = []
    for row in rows:
        if type(row["b3_blocked"]) is not bool or row["label"] not in (0, 1):
            raise ValueError("Expected binary truth and boolean frozen decision")
        if row["label"] == 1 and not row.get("attack_objective"):
            raise ValueError("Eligible attack requires explicit source objective")
        if SECRET_PATTERN.search(row["prompt_text"]):
            raise ValueError("Potential secret detected in input; redact before inference")
        for condition in ("B0", "B3"):
            blocked = condition == "B3" and row["b3_blocked"]
            key = hashlib.sha256(f"{row['row_id']}:{condition}".encode()).hexdigest()
            checkpoint = destination/(key+".json")
            if checkpoint.exists():
                record = json.loads(checkpoint.read_text(encoding="utf-8"))
                if record["fingerprint"] != fp: raise ValueError("Foreign response checkpoint")
                public.append(record["public"]); continue
            response, technical_error = "", False
            if not blocked:
                try:
                    from aethon.generation import evaluation_response
                    response = evaluation_response(driver, row["prompt_text"], max_tokens=max_tokens, temperature=temperature)
                    technical_error = not isinstance(response, str) or not response or response.startswith(NON_RESPONSE_PREFIXES)
                except Exception:
                    response, technical_error = "", True
            if not isinstance(response, str): response = ""
            # Never persist common credentials even in private response storage.
            response = SECRET_PATTERN.sub("[REDACTED_SECRET]", response)
            result = {"row_id": row["row_id"], "condition": condition, "label": row["label"],
                      "blocked": blocked, "submitted_to_llm": not blocked,
                      "technical_error": technical_error,
                      "status": "prevented" if blocked else "no_response" if technical_error else "indeterminate",
                      "response_sha256": hashlib.sha256(response.encode()).hexdigest(),
                      "requires_objective_judgment": not blocked and not technical_error}
            atomic_write(checkpoint, json.dumps({"fingerprint": fp, "public": result, "response": response}, indent=2))
            public.append(result)
    atomic_write(marker, json.dumps({"fingerprint": fp, "retention": retention, "status": "DONE",
                                    "expected_records": len(rows)*2, "processed_records": len(public)}, indent=2))
    return public
