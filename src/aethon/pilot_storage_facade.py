"""Path-free collector persistence. Every I/O and lease is backend-owned."""
from collections import Counter
from contextlib import contextmanager
import copy
from dataclasses import asdict
from datetime import date
import json
import re

from aethon.pilot_governance import digest, require_issued_authorization, utc
from aethon.pilot_storage_backend import (CorruptCheckpoint, JournalHead, MissingObject,
    OperationId, ResourceBudget, ResourceLimit, StorageBackend, StorageKey, bounded_json, sealed, unseal)

TERMINAL = {"blocked", "completed", "reused", "no_response", "truncated", "inference_error",
            "evaluation_error", "contract_error", "interrupted_unknown", "evaluation_interrupted", "evaluation_pending"}
TRANSITIONS = {
    "pending": {"started", "blocked", "reused", "contract_error"},
    "started": {"generated", "no_response", "truncated", "inference_error", "contract_error", "interrupted_unknown"},
    "generated": {"evaluating", "completed", "evaluation_pending", "contract_error"},
    "evaluating": {"completed", "evaluation_error", "evaluation_interrupted", "contract_error"},
}
IMMUTABLE_SLOT = {"slot_id", "sample_id", "condition", "pair_id", "family_id", "scenario_id", "namespace",
                  "source_id", "source_row_id", "label", "replicate", "fingerprint", "state", "expected_generation_metadata"}


class PrivateRunStore:
    """Explicit backend injection only; no native backend or path fallback."""
    def __init__(self, root=None, manifest=None, authorization=None, forbidden=None, storage_observation=None,
                 *, confinement=None, backend=None, budget=None):
        if not isinstance(backend, StorageBackend):
            raise PermissionError("Native capability storage unavailable; production writes disabled")
        if root is not None or forbidden is not None or storage_observation is not None or confinement is not None:
            raise PermissionError("Path/observation/confinement bootstrap cannot issue a storage capability")
        if type(manifest) is not dict or not isinstance(manifest.get("subject"), dict):
            raise PermissionError("Structured manifest subject required")
        require_issued_authorization(authorization, manifest["subject"])
        manifest = copy.deepcopy(manifest)
        manifest["authorization_provenance"] = {
            "policy_sha256": authorization.policy_sha256, "receipts_sha256": authorization.receipts_sha256,
            "launch_sha256": authorization.launch_sha256, "expires_at": authorization.expires_at,
            "storage_custodian": authorization.storage_custodian,
            "retention_delete_after": authorization.retention_delete_after,
            "retention_plan_sha256": authorization.retention_plan_sha256}
        if (manifest["retention"].get("custodian") != authorization.storage_custodian
                or manifest["retention"].get("delete_after") != authorization.retention_delete_after
                or not authorization.retention_plan_sha256):
            raise PermissionError("Manifest retention differs from signed private-storage approval")
        if not manifest["retention"]["custodian"] or date.fromisoformat(manifest["retention"]["delete_after"]) <= date.today():
            raise PermissionError("Concrete unexpired retention policy required")
        self.authorization, self.backend = authorization, backend
        self.budget = ResourceBudget() if budget is None else budget
        if not isinstance(self.budget, ResourceBudget): raise ResourceLimit("Typed resource budget required")
        self._manifest_raw = bounded_json(manifest, self.budget.manifest_bytes)
        self._manifest_sha256 = digest(self._manifest_raw)
        self.run_capability = backend.open_run(authorization, self._manifest_raw, self.budget)
        self._closed = False
        self._failed = False
        try: self.load()
        except BaseException:
            backend.close(self.run_capability); raise

    @property
    def manifest(self): return json.loads(self._manifest_raw)

    def guard(self):
        if self._closed: raise PermissionError("Closed storage facade")
        if self._failed: raise CorruptCheckpoint("Failed recovery; close and independently inspect before retry")
        require_issued_authorization(self.authorization, self.manifest["subject"])
        if date.fromisoformat(self.manifest["retention"]["delete_after"]) <= date.today(): raise PermissionError("Retention expired")

    @contextmanager
    def writer(self):
        self.guard()
        with self.backend.writer(self.run_capability):
            self.load(); yield

    def close(self):
        if not self._closed:
            self.backend.close(self.run_capability); self._closed = True

    def __enter__(self): self.guard(); return self
    def __exit__(self, *args): self.close()

    def _scope(self, payload, key=None):
        data = {"run_fingerprint": self.manifest["run_fingerprint"], "manifest_sha256": self._manifest_sha256,
                "binding_sha256": self.binding_sha256, "data": payload}
        if key is not None: data["checkpoint"] = asdict(key)
        raw = bounded_json(data, self.budget.object_bytes)
        return bounded_json({"payload":data, "sha256":digest(raw)}, self.budget.object_bytes)

    def put(self, payload):
        self.guard(); raw = self._scope(payload); key = StorageKey("object", digest(raw))
        op = OperationId(digest(b"object:"+raw))
        receipt = self.backend.put_if_absent(self.run_capability, key, raw, op)
        if receipt.operation_id != op or receipt.data_sha256 != key.identity or receipt.binding_sha256 != self.binding_sha256:
            raise CorruptCheckpoint("Incompatible object receipt")
        return key.identity

    def _data(self, raw):
        if type(raw) is not bytes or len(raw) > self.budget.object_bytes: raise CorruptCheckpoint("Invalid record bytes")
        scoped = unseal(raw)
        if (scoped.get("manifest_sha256") != self._manifest_sha256
                or scoped.get("binding_sha256") != self.binding_sha256
                or scoped.get("run_fingerprint") != self.manifest["run_fingerprint"]):
            raise CorruptCheckpoint("Foreign complete run binding")
        return scoped["data"]

    def get(self, key):
        self.guard(); reference = StorageKey("object", key)
        raw = self.backend.get_verified(self.run_capability, reference)
        if raw is None: raise MissingObject("Referenced object absent; recovery blocked")
        if digest(raw) != key: raise CorruptCheckpoint("Object digest changed")
        return self._data(raw)

    def pointer(self, name, payload=None):
        self.guard()
        if not isinstance(name, str) or re.fullmatch(r"[a-f0-9]{64}\.(request|response|evaluation)", name) is None:
            raise CorruptCheckpoint("Structured checkpoint required")
        identity, role = name.split("."); key = StorageKey("checkpoint", identity, role)
        if payload is not None:
            raw = self._scope(payload, key)
            op = OperationId(digest(b"checkpoint:"+bounded_json(asdict(key),1024)))
            receipt = self.backend.put_if_absent(self.run_capability, key, raw, op)
            if receipt.operation_id != op or receipt.data_sha256 != digest(raw) or receipt.binding_sha256 != self.binding_sha256:
                raise CorruptCheckpoint("Incompatible checkpoint receipt")
        raw = self.backend.get_verified(self.run_capability, key)
        if raw is None: return None
        if unseal(raw).get("checkpoint") != asdict(key): raise CorruptCheckpoint("Foreign checkpoint identity")
        return self._data(raw)

    def _apply(self, event):
        kind = event["kind"]
        if kind == "slot":
            slot = self.slots[event["slot_id"]]; update = event["update"]
            if (not isinstance(update, dict) or IMMUTABLE_SLOT.intersection(update)
                    or event["from_state"] != slot["state"] or event["to_state"] not in TRANSITIONS.get(slot["state"],set())):
                raise CorruptCheckpoint("Illegal state or immutable identity update")
            for field in ["response_ref", "evaluation_ref"]:
                reference = update.get(field,slot.get(field))
                if reference: self.get(reference)
            slot.update(copy.deepcopy(update)); slot["state"] = event["to_state"]
        elif kind == "suspend":
            if not isinstance(event["reason"],str) or not event["reason"]: raise CorruptCheckpoint("Reason required")
            self.suspended = event["reason"]
        elif kind == "defenses":
            if self.defenses is not None: raise CorruptCheckpoint("Duplicate defense matrix")
            matrix = self.get(event["reference"])
            if not isinstance(matrix,dict) or set(matrix) != set(self.slots): raise CorruptCheckpoint("Incomplete defense matrix")
            self.defenses = matrix
        elif kind == "review":
            if event["slot_id"] not in self.slots: raise CorruptCheckpoint("Foreign review slot")
            self.get(event["reference"]); self.review_events.append(event)
        else: raise CorruptCheckpoint("Unknown event kind")

    def load(self):
        self.guard()
        try: self._load()
        except BaseException:
            self._failed = True
            raise

    def _load(self):
        self.guard(); head = self.backend.read_head(self.run_capability)
        if not isinstance(head,JournalHead) or len(head.events) != head.sequence or head.sequence > self.budget.events:
            raise CorruptCheckpoint("Invalid bounded journal snapshot")
        if getattr(self,'binding_sha256',head.binding_sha256) != head.binding_sha256:
            raise CorruptCheckpoint("Backend root/run/budget binding changed")
        self.binding_sha256 = head.binding_sha256
        rebuilt = {s["slot_id"]: copy.deepcopy(s) for s in self.manifest["slots"]}
        if len(rebuilt) != 120 or any(s["state"] != "pending" for s in rebuilt.values()): raise CorruptCheckpoint("120 initial pending slots required")
        existing = getattr(self,"slots",{})
        for key,slot in rebuilt.items():
            if key in existing: existing[key].clear(); existing[key].update(slot); rebuilt[key] = existing[key]
        self.slots = rebuilt
        self.sequence, self.previous, self.suspended, self.defenses = 0, None, None, None
        self.review_events = []
        for raw in head.events:
            event = unseal(raw)
            try:
                utc(event["recorded_utc"])
                if (event["sequence"] != self.sequence+1 or event["previous_sha256"] != self.previous
                        or event["binding_sha256"] != head.binding_sha256): raise CorruptCheckpoint("Journal chain/run mismatch")
                self._apply(event)
            except (KeyError,TypeError,ValueError) as exc: raise CorruptCheckpoint("Invalid persisted event; recovery blocked") from exc
            self.sequence += 1; self.previous = digest(raw)
        if (self.sequence,self.previous) != (head.sequence,head.head_sha256): raise CorruptCheckpoint("Head mismatch")
        self.binding_sha256 = head.binding_sha256

    def append(self, event):
        self.guard()
        if not isinstance(event, dict): raise CorruptCheckpoint("Event object required")
        intent = copy.deepcopy(event); raw = bounded_json(intent,self.budget.event_bytes)
        saved = (copy.deepcopy(self.slots), self.suspended, copy.deepcopy(self.defenses), list(self.review_events))
        try: self._apply(intent)
        finally:
            for key,value in saved[0].items(): self.slots[key].clear(); self.slots[key].update(value)
            self.suspended,self.defenses,self.review_events = saved[1:]
        op = OperationId(digest(bounded_json([self._manifest_sha256,self.sequence+1,intent],self.budget.event_bytes)))
        receipt = self.backend.append_event(self.run_capability,self.sequence,self.previous,raw,op)
        if receipt.event is None: raise CorruptCheckpoint("Committed event receipt required")
        actual = unseal(receipt.event)
        if (receipt.operation_id != op or receipt.binding_sha256 != self.binding_sha256 or receipt.sequence != self.sequence+1
                or receipt.data_sha256 != digest(receipt.event) or receipt.head_sha256 != receipt.data_sha256
                or actual.get("binding_sha256") != self.binding_sha256
                or actual.get("previous_sha256") != self.previous or actual.get("sequence") != receipt.sequence
                or any(actual.get(k) != v for k,v in intent.items())): raise CorruptCheckpoint("Incompatible backend receipt")
        utc(actual["recorded_utc"]); self._apply(actual)
        self.sequence,self.previous = receipt.sequence,receipt.head_sha256

    def transition(self, slot_id, state, **update):
        if slot_id not in self.slots: raise CorruptCheckpoint("Foreign slot")
        before = self.slots[slot_id]["state"]
        if state not in TRANSITIONS.get(before,set()) or IMMUTABLE_SLOT.intersection(update): raise CorruptCheckpoint("Invalid transition or immutable slot change")
        self.append({"kind":"slot","slot_id":slot_id,"from_state":before,"to_state":state,"update":update})

    def suspend(self, reason): self.append({"kind":"suspend","reason":reason})

    def summary(self):
        self.guard()
        return {"schema":"aethon.pilot-accounting.v1","expected_slots":120,"represented_slots":len(self.slots),
                "states":dict(Counter(s["state"] for s in self.slots.values())),"suspended":self.suspended,
                "accounting_complete":all(s["state"] in TERMINAL for s in self.slots.values()),
                "attempted_calls":sum(s.get("attempted",False) for s in self.slots.values()),
                "collection_status":"COLLECTION_COMPLETE" if all(s["state"] in TERMINAL for s in self.slots.values()) else "COLLECTION_IN_PROGRESS",
                "scientific_review_status":"REVIEW_PENDING","scientific_estimates_computed":False}
