"""Fail-closed consistency check for the SRC-02 design-only milestone.

This intentionally CANNOT authorize native operations or the pilot.
It only rejects a malformed or prematurely promoted design manifest.
No filesystem root is opened and no native syscall or witness call is made.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "docs/security/src02-native-readiness-v1/READINESS_MANIFEST.json"
)
REVIEW_SHA = "e7f15000b682b0cb7824c71fc55daf6f9a2129c9"
CANDIDATES = {
    "root_bootstrap": ("PROPOSED_NOT_APPROVED", "independent_signed_root_bootstrap_receipt_v1"),
    "freshness_witness": ("PROPOSED_NOT_APPROVED", "independent_linearizable_compare_and_advance_service"),
    "linux_native_profile": ("PROPOSED_NOT_APPROVED", "linux_x86_64_single_host_local_ext4"),
    "lease_commit_authority": ("PENDING", "single_serialized_epoch_and_head_authority"),
}
EVIDENCE = {
    "signed_bootstrap_receipt": "NOT_RUN",
    "independent_trust_anchor": "NOT_PROVISIONED",
    "revocation_service": "NOT_PROVISIONED",
    "witness_service": "NOT_PROVISIONED",
    "witness_fault_tests": "NOT_RUN",
    "linux_syscall_profile": "NOT_VALIDATED",
    "linux_power_loss_matrix": "NOT_RUN",
    "native_fencing_fault_tests": "NOT_RUN",
    "native_contract_review": "PENDING",
}
GATES = {
    "independent_inventory", "semantic_review", "rubric_review",
    "reviewer_assignment", "private_storage", "model_assets",
    "hardware_check", "execution_authorization",
}
OPERATIONAL = {
    "src02": "NOT_AUTHORIZED",
    "dependencies": "DEPENDENCY_APPROVAL_REQUIRED",
    "pilot": "PILOT_BLOCKED",
}
ASSETS = {
    "native_backend": "NOT_IMPLEMENTED", "root": "NOT_PROVISIONED",
    "witness": "NOT_PROVISIONED", "gpu_inference": "NOT_RUN",
}


def assess(data: object) -> dict[str, Any]:
    """Audit declared design state; never produce an authorization credential."""
    issues: list[str] = []
    if not isinstance(data, dict):
        data = {}
        issues.append("manifest must be an object")
    if data.get("schema") != "aethon.src02.native-readiness.v1":
        issues.append("unsupported schema")
    if data.get("baseline") != {
        "pr": 41, "head_sha": REVIEW_SHA, "scope": "DESIGN_ONLY"
    }:
        issues.append("baseline must bind the closed abstract review and design-only scope")

    decisions = data.get("decisions")
    if not isinstance(decisions, dict):
        decisions = {}
    if set(decisions) != set(CANDIDATES) | {"dependency_review", "independent_design_review"}:
        issues.append("decision inventory missing or contains unknown entries")
    for key, (status, candidate) in CANDIDATES.items():
        if decisions.get(key) != {"status": status, "candidate": candidate}:
            issues.append(f"{key} is not an unapproved design candidate")
    for key in ("dependency_review", "independent_design_review"):
        if decisions.get(key) != {"status": "PENDING"}:
            issues.append(f"{key} must stay PENDING")

    evidence = data.get("evidence")
    if evidence != EVIDENCE:
        issues.append("native and trust-service evidence must remain explicitly unvalidated")
    operational = data.get("operational")
    if not isinstance(operational, dict):
        operational = {}
    if set(operational) != set(OPERATIONAL) | {"gates"}:
        issues.append("unknown or missing operational controls")
    for key, expected in OPERATIONAL.items():
        if operational.get(key) != expected:
            issues.append(f"{key} cannot be promoted by a design manifest")
    gates = operational.get("gates")
    if not isinstance(gates, dict) or set(gates) != GATES:
        issues.append("the exact eight launch gates must be present")
    elif any(gates[k] != "PENDING" for k in GATES):
        issues.append("design artifacts may not mark launch gates approved")
    if data.get("assets") != ASSETS:
        issues.append("native assets/provisioning must remain absent")

    if set(data) != {"schema", "baseline", "decisions", "evidence", "operational", "assets"}:
        issues.append("unknown top-level keys are forbidden")

    return {
        "status": "INVALID_FAIL_CLOSED" if issues else "DESIGN_ONLY_BLOCKED",
        "authorized": False,
        "native_execution": False,
        "pilot_execution": False,
        "issues": issues,
    }


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_manifest(path: Path = MANIFEST) -> object:
    data = path.read_bytes()
    if len(data) > 128 * 1024:
        raise ValueError("oversized design manifest")
    return json.loads(data.decode("utf-8"), object_pairs_hook=_unique_pairs)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SRC-02 design gate without authorization")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()
    try:
        result = assess(load_manifest(args.manifest))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "status": "INVALID_FAIL_CLOSED", "authorized": False,
            "native_execution": False, "pilot_execution": False,
            "issues": [f"cannot parse manifest: {type(exc).__name__}"],
        }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "DESIGN_ONLY_BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
