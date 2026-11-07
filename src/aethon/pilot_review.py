"""Private authenticated review ledger; no inference, judges or ASR calculations."""
import base64
from datetime import datetime, timezone
import json

from aethon.pilot_governance import canonical, digest, read_external, require_issued_authorization, utc
from aethon.prospective import fingerprint
from aethon.pilot_storage import CorruptCheckpoint

DECISIONS = {"success", "failure", "indeterminate"}


class ReviewLedger:
    """Two assigned signed votes, plus a distinct adjudicator on disagreement.

    Supply the original independently pinned authority and the approved private
    rubric bundle. No callback/boolean/receipt presence can complete a review.
    """
    def __init__(self, store, authority, rubric_bundle_path):
        self.store, self.authority = store, authority
        permission = store.authorization
        require_issued_authorization(permission, store.manifest["subject"])
        if authority.policy_sha256 != permission.policy_sha256:
            raise PermissionError("Foreign review trust policy")
        if not permission.review_assignment_sha256 or len(permission.reviewer_ids) != 2:
            raise PermissionError("Verified reviewer assignment required")
        raw = read_external(rubric_bundle_path, authority.forbidden)
        if digest(raw) != permission.rubric_bundle_sha256:
            raise PermissionError("Unapproved rubric bundle")
        bundle = json.loads(raw)
        if bundle.get("schema") != "aethon.rubric-bundle.v1":
            raise ValueError("Versioned rubric bundle required")
        self.rubrics = bundle["rubrics"]
        if not self.rubrics or any(not isinstance(k, str) or not isinstance(v, str) or len(v) != 64
                                   or any(c not in "0123456789abcdef" for c in v) for k, v in self.rubrics.items()):
            raise ValueError("Exact rubric hashes required")
        self._check_keys()

    def _check_keys(self):
        permission = self.store.authorization
        identities = list(permission.reviewer_ids) + [permission.adjudicator_id]
        actual = tuple((i, self.authority.evaluator_key(i)[1]) for i in identities)
        if actual != permission.evaluator_keys or len({key for _, key in actual}) != 3:
            raise PermissionError("Assigned evaluator keys changed or aliased")

    def _slot(self, key):
        slot = self.store.slots[key]
        if slot["state"] == "reused":
            source = self.store.slots[slot["reuse"]["source_slot"]]
            if slot["response_ref"] != source["response_ref"] or not slot["reuse"]["verified"]:
                raise CorruptCheckpoint("Unverified reused review")
            return source
        if not slot.get("response_ref") or slot["state"] not in {"evaluation_pending", "evaluation_error", "evaluation_interrupted", "completed"}:
            raise ValueError("Complete generated continuation required for review")
        return slot

    def binding(self, key, rubric_id):
        slot = self._slot(key)
        if rubric_id not in self.rubrics: raise ValueError("Unknown rubric")
        # Bind task/attack rubric to the request's immutable sample provenance.
        request = self.store.pointer(slot["sample_id"]+".request")
        if not request: raise CorruptCheckpoint("Missing effective input")
        expected = self.store.manifest.get("review_rubrics", {}).get(slot["sample_id"])
        if not expected or rubric_id != expected:
            raise ValueError("Slot rubric differs from immutable inventory")
        return {"subject_sha256": fingerprint(self.store.manifest["subject"]),
                "run_fingerprint": self.store.manifest["run_fingerprint"],
                "assignment_sha256": self.store.authorization.review_assignment_sha256,
                "slot_id": slot["slot_id"], "case_id": slot["slot_id"], "sample_id": slot["sample_id"],
                "response_sha256": slot["response_ref"], "rubric_id": rubric_id,
                "rubric_sha256": self.rubrics[rubric_id]}

    def _verify(self, envelope, key, phase, *, historical=False, recorded_utc=None):
        require_issued_authorization(self.store.authorization, self.store.manifest["subject"])
        self._check_keys()
        payload = envelope["payload"]
        expected = self.binding(key, payload["rubric_id"])
        if (payload.get("schema") != "aethon.review-vote.v1" or payload.get("phase") != phase
                or any(payload.get(k) != v for k, v in expected.items())
                or payload.get("decision") not in DECISIONS):
            raise ValueError("Foreign or incompatible review binding")
        permission = self.store.authorization
        identity = payload["reviewer_id"]
        assigned = permission.reviewer_ids if phase == "vote" else (permission.adjudicator_id,)
        if identity not in assigned: raise ValueError("Evaluator not assigned to this phase")
        issued, expires = utc(payload["issued_at"]), utc(payload["expires_at"])
        now = utc(recorded_utc) if historical else datetime.now(timezone.utc)
        if not issued <= now < expires or (expires-issued).total_seconds() > 86400:
            raise ValueError("Expired or invalid vote time")
        public, _ = self.authority.evaluator_key(identity)
        signature = envelope["signature"]
        if signature["authority_id"] != identity or not self.authority.verifier(
                public, canonical(payload), base64.b64decode(signature["signature_base64"], validate=True)):
            raise ValueError("Invalid evaluator signature")
        # Authenticate the author before following a supplied private evidence path.
        evidence = payload["evidence"]
        raw = read_external(evidence["path"], self.authority.forbidden)
        if digest(raw) != evidence["sha256"]: raise ValueError("Review evidence changed")
        span = json.loads(raw)
        if span.get("schema") != "aethon.review-span.v1" or any(span.get(k) != v for k, v in expected.items()):
            raise ValueError("Foreign review evidence")
        continuation = self.store.get(expected["response_sha256"])["generation_result"]["continuation"]
        start, end = span["start"], span["end"]
        if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(continuation)
                or digest(continuation[start:end].encode()) != span["span_sha256"]):
            raise ValueError("Evidence span does not match generated continuation")
        return payload

    def _history(self, key):
        key = self._slot(key)["slot_id"]
        votes, adjudication = {}, None
        for event in self.store.review_events:
            if event["slot_id"] != key: continue
            item = self.store.get(event["reference"])
            phase = item["envelope"]["payload"]["phase"]
            payload = self._verify(item["envelope"], key, phase, historical=True, recorded_utc=event["recorded_utc"])
            if phase == "vote":
                if payload["reviewer_id"] in votes or adjudication: raise CorruptCheckpoint("Duplicate or late vote")
                votes[payload["reviewer_id"]] = (event["reference"], payload)
            elif phase == "adjudication":
                if len(votes) != 2 or adjudication or len({p["decision"] for _, p in votes.values()}) != 2:
                    raise CorruptCheckpoint("Unexpected adjudication")
                if payload.get("vote_refs") != sorted(ref for ref, _ in votes.values()):
                    raise CorruptCheckpoint("Adjudication does not bind both raw votes")
                adjudication = (event["reference"], payload)
            else: raise CorruptCheckpoint("Unknown review phase")
        return votes, adjudication

    def record(self, key, envelope):
        # Shared writer lock excludes collection/review races; re-read every journal.
        with self.store.writer():
            slot = self._slot(key)
            key = slot["slot_id"]
            phase = envelope["payload"]["phase"]
            if phase not in {"vote", "adjudication"}: raise ValueError("Unknown review phase")
            payload = self._verify(envelope, key, phase)
            votes, adjudication = self._history(key)
            if phase == "vote":
                if payload["reviewer_id"] in votes:
                    old = self.store.get(votes[payload["reviewer_id"]][0])["envelope"]
                    if old == envelope: return self.status(key)
                    raise ValueError("Refusing vote overwrite")
                if adjudication: raise ValueError("Review already adjudicated")
            elif (len(votes) != 2 or adjudication or len({p["decision"] for _, p in votes.values()}) != 2
                  or payload.get("vote_refs") != sorted(ref for ref, _ in votes.values())):
                raise ValueError("Adjudication requires both conflicting raw votes")
            reference = self.store.put({"envelope": envelope})
            self.store.append({"kind": "review", "slot_id": key, "reference": reference})
            return self.status(key)

    def status(self, key):
        votes, adjudication = self._history(key)
        if len(votes) < 2:
            return {"state": "VOTE_RECORDED" if votes else "REVIEW_PENDING", "vote_refs": sorted(r for r, _ in votes.values())}
        decisions = {p["decision"] for _, p in votes.values()}
        refs = sorted(r for r, _ in votes.values())
        if len(decisions) > 1 and not adjudication:
            return {"state": "ADJUDICATION_PENDING", "vote_refs": refs}
        decision = adjudication[1]["decision"] if adjudication else next(iter(decisions))
        # Deterministic final audit record binds both immutable vote references.
        audit = {"policy": "two-assigned-votes-adjudicate-disagreement-v1", "vote_refs": refs,
                 "adjudication_ref": adjudication[0] if adjudication else None, "decision": decision}
        return {"state": "SCIENTIFIC_REVIEW_COMPLETE", **audit, "audit_sha256": fingerprint(audit)}
