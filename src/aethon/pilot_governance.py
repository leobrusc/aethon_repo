"""Authenticated, run-bound evidence. A receipt is not a launch command."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import weakref

from aethon.prospective import GATES, fingerprint

def _authorization_snapshot(value):
    """Bind every issued field, not just object identity, for this process lifetime."""
    return fingerprint({name: getattr(value, name) for name in Authorization.__dataclass_fields__})


def require_issued_authorization(value, subject):
    """Nonvirtual trust-boundary check; subclasses and duck types never authorize."""
    if type(value) is not Authorization:
        raise PermissionError("Exact issued operational Authorization required")
    Authorization.check(value, subject)


KINDS = {
    "independent_inventory": ("technical_review", "data_steward", 1),
    "semantic_review": ("human_review", "scientific_reviewer", 2),
    "rubric_review": ("scientific_approval", "scientific_reviewer", 2),
    "reviewer_assignment": ("scientific_approval", "scientific_lead", 1),
    "private_storage": ("technical_review", "storage_custodian", 1),
    "model_assets": ("technical_review", "asset_reviewer", 1),
    "hardware_check": ("technical_review", "platform_reviewer", 1),
    "execution_authorization": ("operational_authorization", "operations_authority", 1),
    "launch_intent": ("operator_request", "operator", 1),
}
DISPOSITIONS = {"technical_review": "verified", "human_review": "approved_for_pilot",
                "scientific_approval": "approved_for_pilot", "operational_authorization": "authorized_for_this_run",
                "operator_request": "execute_this_run"}
CLAIMS = {
    "independent_inventory": {"inventory_sha256", "licensed_source_ledger_sha256"},
    "semantic_review": {"review_ledger_sha256", "screen_model_revision", "prior_inventory_sha256"},
    "rubric_review": {"rubric_bundle_sha256", "scenario_oracles_sha256"},
    "reviewer_assignment": {"reviewer_ids", "adjudicator_id", "blinding_plan_sha256"},
    "private_storage": {"probe_fingerprint", "retention_plan_sha256", "custodian", "delete_after"},
    "model_assets": {"asset_set_sha256", "snapshot_path"},
    "hardware_check": {"environment_sha256", "network_isolation_evidence_sha256"},
    "execution_authorization": {"purpose", "max_slots", "max_calls"},
    "launch_intent": {"purpose", "max_slots", "max_calls"},
}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def key_identity(public):
    """Count actual Ed25519 keys, not alternate PEM whitespace encodings."""
    if b"-----BEGIN PUBLIC KEY-----" in public:
        match = re.fullmatch(rb"\s*-----BEGIN PUBLIC KEY-----\s+([A-Za-z0-9+/=\s]+)-----END PUBLIC KEY-----\s*", public)
        if not match: raise ValueError("Invalid public-key encoding")
        der = base64.b64decode(b"".join(match[1].split()), validate=True)
        if len(der) != 44 or not der.startswith(bytes.fromhex("302a300506032b6570032100")):
            raise ValueError("Ed25519 public key required")
        return digest(der)
    # Non-PEM keys are usable only by an explicitly injected test verifier;
    # the production OpenSSL verifier rejects them.
    return digest(public)


def utc(value):
    if not isinstance(value, str): raise ValueError("Explicit UTC timestamp required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timezone required")
    return parsed.astimezone(timezone.utc)


def read_external(path, forbidden):
    original = Path(path)
    if not original.is_absolute():
        raise ValueError("Absolute external path required")
    for component in [original, *original.parents]:
        if component.is_symlink() or (getattr(component.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError("Symlink/reparse point rejected")
    resolved = original.resolve(strict=True)
    if any(resolved == p or p in resolved.parents for p in map(Path.resolve, forbidden)):
        raise ValueError("Evidence must be outside repositories/worktrees")
    if not resolved.is_file() or resolved.stat().st_nlink != 1:
        raise ValueError("Regular single-link evidence required")
    if resolved.stat().st_size > 10*1024*1024:
        raise ValueError("Receipt/inventory evidence exceeds bounded input limit")
    return resolved.read_bytes()


class OpenSSLVerifier:
    """Fail closed: pathname invocation cannot bind executable AND loader closure.

    Identity checks diagnose drift; they DO NOT close the check/use window.
    There is no approved native execution backend on Windows or Linux yet.
    """
    def __init__(self, executable, expected_sha256, dependencies=None):
        from aethon.pilot_identity import path_identity
        self.executable = Path(executable)
        self.identities = {self.executable: path_identity(self.executable, file=True)}
        if self.identities[self.executable]["sha256"] != expected_sha256:
            raise ValueError("Unpinned signature verifier")
        for name, expected in (dependencies or {}).items():
            dependency = Path(name)
            if dependency in self.identities: raise ValueError("Duplicate tool dependency")
            identity = path_identity(dependency, file=True)
            if identity["sha256"] != expected: raise ValueError("Unpinned verifier dependency")
            self.identities[dependency] = identity

    def __call__(self, public_key, payload, signature):
        from aethon.pilot_identity import path_identity
        for path, identity in self.identities.items():
            if path_identity(path, file=True) != identity:
                raise PermissionError("Verifier or dependency identity changed")
        if len(signature) != 64:
            return False
        raise PermissionError("Native object-bound verifier/loader deployment NOT_AUDITED; execution disabled")


class ReceiptAuthority:
    """Trust policy digest MUST be obtained independently by the operator.

    Injected verifiers are trusted application code; tests use synthetic keys.
    This does not protect a compromised Python process or operator trust anchor.
    """
    def __init__(self, policy_path, policy_sha256, forbidden, verifier=None, now=None):
        self.forbidden = [Path(p).resolve() for p in forbidden]
        raw = read_external(policy_path, self.forbidden)
        if digest(raw) != policy_sha256:
            raise ValueError("Trust-anchor mismatch")
        self.policy = json.loads(raw)
        if self.policy.get("schema") != "aethon.trust-policy.v1":
            raise ValueError("Unsupported trust policy")
        self.policy_sha256 = policy_sha256
        self.verifier = verifier or OpenSSLVerifier(**self.policy["verifier"])
        self.now = now or (lambda: datetime.now(timezone.utc))

    def verify(self, envelope, gate, subject):
        if not isinstance(envelope, dict) or not isinstance(envelope.get("payload"), dict):
            raise ValueError("Structured receipt required")
        payload = envelope["payload"]
        kind, role, quorum = KINDS[gate]
        now = self.now()
        issued, expires = utc(payload["issued_at"]), utc(payload["expires_at"])
        if (payload.get("schema") != "aethon.gate-receipt.v1" or payload.get("version") != "1.0"
                or payload.get("gate") != gate or payload.get("kind") != kind
                or payload.get("disposition") != DISPOSITIONS[kind]
                or payload.get("subject_sha256") != fingerprint(subject)
                or not issued <= now < expires
                or (expires-issued).total_seconds() > self.policy.get("max_receipt_validity_seconds", 86400)):
            raise ValueError("Stale, foreign or incompatible receipt")
        claims = payload.get("claims", {})
        if not CLAIMS[gate] <= claims.keys() or any(claims[k] in (None, "", [], {}) for k in CLAIMS[gate]):
            raise ValueError("Incomplete receipt claims")
        evidence = payload.get("evidence", [])
        if not evidence:
            raise ValueError("Independent evidence references required")
        signers, key_fingerprints = set(), set()
        for signature in envelope.get("signatures", []):
            identity = signature["authority_id"]
            key = self.policy["authorities"].get(identity)
            if not key or role not in key["roles"] or gate not in key["gates"]:
                continue
            public = read_external(key["public_key_path"], self.forbidden)
            if digest(public) != key["public_key_sha256"]:
                raise ValueError("Authority key drift")
            value = base64.b64decode(signature["signature_base64"], validate=True)
            if self.verifier(public, canonical(payload), value):
                signers.add(identity)
                key_fingerprints.add(key_identity(public))
        if len(signers) < quorum or len(key_fingerprints) < quorum or payload.get("responsible") not in signers:
            raise ValueError("Independent signature quorum/role missing")
        # Authenticate before following paths in a potentially hostile receipt.
        hashes, evidence_bytes = set(), {}
        for item in evidence:
            raw = read_external(item["path"], self.forbidden)
            value = digest(raw)
            if value != item["sha256"]: raise ValueError("Evidence hash mismatch")
            hashes.add(value); evidence_bytes[value] = raw
        for key, value in claims.items():
            if key.endswith("_sha256") and value not in hashes and value not in subject.values():
                raise ValueError("Unreferenced evidence claim")
        if gate == "independent_inventory" and claims["inventory_sha256"] != subject["inventory_sha256"]:
            raise ValueError("Inventory drift")
        if gate == "semantic_review" and not re.fullmatch(r"[0-9a-f]{40}", claims["screen_model_revision"]):
            raise ValueError("Exact semantic-screen revision required")
        if gate in {"execution_authorization", "launch_intent"}:
            if claims["purpose"] != "bounded_pilot" or claims["max_slots"] != 120 or claims["max_calls"] != 96:
                raise ValueError("Wrong operational scope")
        if gate == "reviewer_assignment":
            reviewers = claims["reviewer_ids"]
            if len(reviewers) != 2 or len(set(reviewers + [claims["adjudicator_id"]])) != 3:
                raise ValueError("Independent reviewers and adjudicator required")
            if not all("evaluator" in self.policy["authorities"].get(i, {}).get("roles", []) for i in reviewers + [claims["adjudicator_id"]]):
                raise ValueError("Unrecognized evaluator assignment")
            assigned_keys = [self.evaluator_key(i)[1] for i in reviewers + [claims["adjudicator_id"]]]
            if len(set(assigned_keys)) != 3: raise ValueError("Evaluator key aliases are not independent")
        if gate == "private_storage":
            plan = json.loads(evidence_bytes[claims["retention_plan_sha256"]])
            if (plan.get("schema") != "aethon.retention-plan.v1" or not plan.get("policy_version")
                    or not isinstance(plan.get("deletion_process"), str) or not plan["deletion_process"].strip()
                    or not isinstance(claims["custodian"], str) or not claims["custodian"].strip()
                    or plan.get("custodian") != claims["custodian"]
                    or plan.get("delete_after") != claims["delete_after"]):
                raise ValueError("Concrete retention plan does not match receipt")
        return {"status": "VERIFIED", "kind": kind, "signers": sorted(signers), "key_fingerprints": sorted(key_fingerprints),
                "receipt_sha256": digest(canonical(envelope)), "expires_at": payload["expires_at"], "claims": claims}

    def evaluator_key(self, identity):
        key = self.policy["authorities"].get(identity, {})
        if "evaluator" not in key.get("roles", []): raise ValueError("Unassigned evaluator role")
        public = read_external(key["public_key_path"], self.forbidden)
        if digest(public) != key["public_key_sha256"]: raise ValueError("Evaluator key drift")
        return public, key_identity(public)


@dataclass(frozen=True)
class Authorization:
    subject_sha256: str
    policy_sha256: str
    receipts_sha256: str
    expires_at: str
    launch_sha256: str
    review_assignment_sha256: str = ""
    rubric_bundle_sha256: str = ""
    reviewer_ids: tuple = ()
    adjudicator_id: str = ""
    evaluator_keys: tuple = ()
    storage_probe_fingerprint: str = ""
    storage_custodian: str = ""
    retention_delete_after: str = ""
    retention_plan_sha256: str = ""

    def check(self, subject):
        _CHECK_ISSUED_AUTHORIZATION(self, subject)


def verify_gates(authority, envelopes, subject, technical):
    """Technical checks are independent live results, never receipt booleans."""
    results = {}
    for gate in GATES:
        try:
            if authority is None:
                raise ValueError("No independent trust anchor")
            item = authority.verify(envelopes[gate], gate, subject)
            if gate in {"private_storage", "model_assets", "hardware_check"}:
                actual = technical.get(gate, {})
                if actual.get("status") != "PASS":
                    raise ValueError("Live technical verification pending")
                binding = {"private_storage": "probe_fingerprint", "model_assets": "asset_set_sha256", "hardware_check": "environment_sha256"}[gate]
                if item["claims"][binding] != actual[binding]:
                    raise ValueError("Receipt/live-observation mismatch")
            results[gate] = item
        except (ValueError, KeyError, OSError, TypeError):
            results[gate] = {"status": "PENDING", "reason": "missing_invalid_or_unverified_evidence"}
    return {"classification": "READY_FOR_PILOT_REVIEW" if all(v["status"] == "VERIFIED" for v in results.values()) else "PILOT_BLOCKED",
            "gates": results, "subject_sha256": fingerprint(subject), "executed": False}


def _make_authorization_api():
    """Create the application issuer and its read-only identity checker.

    The issuance registry is captured by closures rather than exposed as a
    writable module global. This is API encapsulation only: Python introspection,
    monkey-patching, or arbitrary code in this interpreter is outside the model.
    """
    issued_authorizations = {}

    def check_issued(value, subject):
        issued = issued_authorizations.get(id(value)) if type(value) is Authorization else None
        if (issued is None or issued[0]() is not value
                or issued[1] != _authorization_snapshot(value)
                or value.subject_sha256 != fingerprint(subject)
                or datetime.now(timezone.utc) >= utc(value.expires_at)):
            raise PermissionError("Expired or foreign operational authorization")

    def issue(authority, envelopes, subject, launch, technical):
        """Explicit operator action after every gate and launch-intent check."""
        report = verify_gates(authority, envelopes, subject, technical)
        if report["classification"] != "READY_FOR_PILOT_REVIEW" or report["subject_sha256"] != fingerprint(subject):
            raise PermissionError("Pilot gates incomplete")
        intent = authority.verify(launch, "launch_intent", subject)
        operators = set(intent["signers"] + report["gates"]["execution_authorization"]["signers"])
        reviewers = set(report["gates"]["semantic_review"]["signers"] + report["gates"]["rubric_review"]["signers"])
        if operators & reviewers:
            raise PermissionError("Operator must be independent of scientific reviewers")
        operator_keys = set(intent["key_fingerprints"] + report["gates"]["execution_authorization"]["key_fingerprints"])
        reviewer_keys = set(report["gates"]["semantic_review"]["key_fingerprints"] + report["gates"]["rubric_review"]["key_fingerprints"])
        if operator_keys & reviewer_keys: raise PermissionError("Operational/scientific key aliases are not independent")
        expires = min([v["expires_at"] for v in report["gates"].values()] + [intent["expires_at"]], key=utc)
        assignment = report["gates"]["reviewer_assignment"]
        claims = assignment["claims"]
        identities = claims["reviewer_ids"] + [claims["adjudicator_id"]]
        permission = Authorization(fingerprint(subject), authority.policy_sha256, fingerprint(report["gates"]), expires, intent["receipt_sha256"],
                                   assignment["receipt_sha256"], report["gates"]["rubric_review"]["claims"]["rubric_bundle_sha256"],
                                   tuple(claims["reviewer_ids"]), claims["adjudicator_id"],
                                   tuple((i, authority.evaluator_key(i)[1]) for i in identities),
                                   report["gates"]["private_storage"]["claims"]["probe_fingerprint"],
                                   report["gates"]["private_storage"]["claims"]["custodian"],
                                   report["gates"]["private_storage"]["claims"]["delete_after"],
                                   report["gates"]["private_storage"]["claims"]["retention_plan_sha256"])
        # Sole registry write: nested in the gate-checked issuance flow.
        for identity, reference in tuple(issued_authorizations.items()):
            if reference[0]() is None:
                issued_authorizations.pop(identity, None)
        issued_authorizations[id(permission)] = (
            weakref.ref(permission), _authorization_snapshot(permission)
        )
        return permission

    return issue, check_issued


authorize, _CHECK_ISSUED_AUTHORIZATION = _make_authorization_api()
del _make_authorization_api
