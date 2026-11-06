"""Synthetic volatile backend, packaged ONLY with tests; no path/OS storage I/O.

No durability, anti-rollback freshness, interprocess isolation, ACL or encryption
claims. Fault methods are trusted test instrumentation, not a production API.
"""
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import json
import re
import threading

from aethon.pilot_governance import Authorization, canonical, digest
from aethon.prospective import CONDITIONS, case_identity, fingerprint
from aethon.pilot_storage_backend import (CorruptCheckpoint, InvalidCapability, InvalidIdentifier,
    JournalHead, MissingObject, OperationId, ResourceBudget, ResourceLimit, RunCapability,
    StaleHead, StorageCollision, StorageInterrupted, StorageKey, WriteReceipt, WriterBusy,
    bounded_json, sealed, unseal)


class MemoryBackend:
    def __init__(self):
        self._runs, self._handles, self._closed, self._faults = {}, {}, set(), {}
        self._mutex = threading.RLock()

    def open_run(self, authorization, manifest, budget=ResourceBudget()):
        if not isinstance(authorization, Authorization): raise InvalidCapability("Issued operational authorization required")
        if not isinstance(budget, ResourceBudget) or type(manifest) is not bytes:
            raise CorruptCheckpoint("Typed manifest/budget required")
        try: m = json.loads(manifest)
        except (ValueError,UnicodeError,RecursionError) as exc: raise CorruptCheckpoint("Invalid manifest JSON") from exc
        if (not isinstance(m,dict) or m.get('schema') != 'aethon.pilot-run.v1' or not isinstance(m.get('subject'),dict)
                or not isinstance(m.get('slots'),list) or not isinstance(m.get('config'),dict)
                or not isinstance(m.get('schedule'),list) or not isinstance(m.get('run_fingerprint'),str)):
            raise CorruptCheckpoint("Versioned structured manifest required")
        if bounded_json(m, budget.manifest_bytes) != manifest: raise CorruptCheckpoint("Noncanonical manifest")
        authorization.check(m["subject"])
        run_id = m["run_id"]
        if not isinstance(run_id, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", run_id) is None:
            raise InvalidIdentifier("Invalid run identity")
        if run_id != m["subject"]["run_id"] or re.fullmatch(r"[a-f0-9]{64}", m["run_fingerprint"]) is None:
            raise CorruptCheckpoint("Run subject/fingerprint mismatch")
        slots = m["slots"]
        if len(slots) != 120 or len({s["slot_id"] for s in slots}) != 120:
            raise CorruptCheckpoint("120 unique slots required")
        for s in slots:
            StorageKey("checkpoint", s["slot_id"], "response")
            StorageKey("checkpoint", s["sample_id"], "request")
            if (s['condition'] not in CONDITIONS or type(s['replicate']) is not int or s['replicate'] != 0 or s['state'] != 'pending'
                    or type(s['label']) is not int or s['label'] not in (0,1)
                    or s['slot_id'] != case_identity(s['sample_id'],m['config']['revision'],s['condition'],0,m['subject']['protocol_sha256'])
                    or s['fingerprint'] != fingerprint([m['subject'],s['sample_id'],s['condition']])):
                raise CorruptCheckpoint("Frozen slot identity mismatch")
        if (m['subject']['protocol_sha256'] != fingerprint(m['config'])
                or len({s['sample_id'] for s in slots}) != 24
                or any({s['condition'] for s in slots if s['sample_id']==sample} != set(CONDITIONS)
                       for sample in {s['sample_id'] for s in slots})):
            raise CorruptCheckpoint("Full configuration or B0-B4 matrix mismatch")
        if len(m["schedule"]) != 120 or set(m["schedule"]) != {s["slot_id"] for s in slots}:
            raise CorruptCheckpoint("Complete unique schedule required")
        binding = digest(canonical([m, asdict(budget)]))
        if len(manifest) > budget.total_bytes: raise ResourceLimit("Manifest total budget")
        with self._mutex:
            if len(self._handles) >= 64 or len(self._handles)+len(self._closed) >= 1024:
                raise ResourceLimit("Active/lifetime capability limit")
            if run_id not in self._runs:
                if len(self._runs) >= 16: raise ResourceLimit("Run count limit")
                self._runs[run_id] = {"manifest": manifest, "binding": binding, "budget": budget,
                    "manifest_sha256": digest(manifest), "subject": m["subject"], "fingerprint": m["run_fingerprint"],
                    "sample_ids": {s["sample_id"] for s in slots}, "slot_ids": {s["slot_id"] for s in slots},
                    "objects": {}, "journal": [], "ops": {}, "lease": None, "used": len(manifest)}
            state = self._runs[run_id]
            if state["manifest"] != manifest or state["binding"] != binding:
                raise StorageCollision("Immutable run, complete manifest, authorization or budget changed")
            cap = RunCapability(); self._handles[cap] = (state, authorization)
            try: self.read_head(cap)
            except BaseException:
                self._handles.pop(cap); raise
            return cap

    def _state(self, cap):
        if not isinstance(cap, RunCapability) or cap not in self._handles:
            raise InvalidCapability("Foreign, closed or unissued capability")
        s, auth = self._handles[cap]
        if digest(s["manifest"]) != s["manifest_sha256"]: raise CorruptCheckpoint("Manifest corruption")
        auth.check(s["subject"])
        return s

    def _key(self, s, key):
        if not isinstance(key, StorageKey): raise InvalidIdentifier("Typed key required")
        StorageKey(key.kind, key.identity, key.role)
        if key.kind == "checkpoint":
            ids = s["sample_ids"] if key.role == "request" else s["slot_ids"]
            if key.identity not in ids: raise InvalidIdentifier("Checkpoint outside immutable slot matrix")

    def _access(self, s, cap):
        if s["lease"] is not None and s["lease"] is not cap: raise WriterBusy("Other capability owns writer lease")

    def _retry(self, s, operation, intent):
        if not isinstance(operation, OperationId): raise InvalidIdentifier("Typed operation required")
        prior = s["ops"].get(operation)
        if prior:
            if prior[0] != intent: raise StorageCollision("Operation ID reused for different intent")
            return prior[1]
        if len(s["ops"]) >= s["budget"].operations: raise ResourceLimit("Operation count limit")

    def _fault(self, kind, phase):
        if self._faults.pop((kind, phase), False): raise StorageInterrupted("Synthetic commit interruption: "+phase)

    def put_if_absent(self, cap, key, raw, operation):
        with self._mutex:
            s = self._state(cap); self._key(s, key); self._access(s, cap)
            if type(raw) is not bytes or len(raw) > s["budget"].object_bytes: raise ResourceLimit("Object byte limit")
            payload = unseal(raw)
            if bounded_json(sealed(payload),s['budget'].object_bytes) != raw:
                raise CorruptCheckpoint("Noncanonical object bytes")
            if (payload.get("manifest_sha256") != s["manifest_sha256"] or payload.get("run_fingerprint") != s["fingerprint"]
                    or payload.get('binding_sha256') != s['binding']):
                raise CorruptCheckpoint("Foreign-run record")
            if key.kind == "object" and key.identity != digest(raw): raise CorruptCheckpoint("Object hash mismatch")
            if key.kind == "checkpoint" and payload.get("checkpoint") != asdict(key): raise CorruptCheckpoint("Checkpoint key mismatch")
            intent = digest(canonical(["put", asdict(key), digest(raw)]))
            retry = self._retry(s, operation, intent)
            if retry:
                self.get_verified(cap, key); return retry
            old = s["objects"].get(key)
            if old and old[0] != raw: raise StorageCollision("No overwrite permitted")
            if old: self.get_verified(cap, key)
            if not old and (len(s["objects"]) >= s["budget"].objects or s["used"]+len(raw) > s["budget"].total_bytes):
                raise ResourceLimit("Object/total resource limit")
            self._fault("put", "before_commit")
            receipt = WriteReceipt(s["binding"], operation, digest(raw))
            if not old: s["objects"][key] = (raw, digest(raw)); s["used"] += len(raw)
            s["ops"][operation] = (intent, receipt)
            self._fault("put", "after_commit")
            return receipt

    def get_verified(self, cap, key):
        with self._mutex:
            s = self._state(cap); self._key(s, key)
            stored = s["objects"].get(key)
            if stored is None: return None
            raw, expected = stored
            if type(raw) is not bytes or len(raw) > s["budget"].object_bytes or digest(raw) != expected:
                raise CorruptCheckpoint("Corrupted record")
            payload = unseal(raw)
            if (payload.get("manifest_sha256") != s["manifest_sha256"] or payload.get("run_fingerprint") != s["fingerprint"]
                    or payload.get('binding_sha256') != s['binding']):
                raise CorruptCheckpoint("Foreign record binding")
            if key.kind == "object" and digest(raw) != key.identity: raise CorruptCheckpoint("Object reference changed")
            if key.kind == "checkpoint" and payload.get("checkpoint") != asdict(key): raise CorruptCheckpoint("Foreign checkpoint")
            return raw

    def append_event(self, cap, sequence, previous, event, operation):
        with self._mutex:
            s = self._state(cap); self._access(s, cap)
            if type(event) is not bytes or len(event) > s["budget"].event_bytes: raise ResourceLimit("Event byte limit")
            payload = json.loads(event)
            if not isinstance(payload, dict): raise CorruptCheckpoint("Event object required")
            if bounded_json(payload, s["budget"].event_bytes) != event: raise CorruptCheckpoint("Noncanonical event")
            intent = digest(canonical(["event", sequence, previous, payload]))
            retry = self._retry(s, operation, intent)
            if retry:
                self.read_head(cap); return retry
            current = digest(s["journal"][-1]) if s["journal"] else None
            if type(sequence) is not int or sequence != len(s["journal"]) or previous != current:
                raise StaleHead("Compare-and-append head mismatch")
            if any(k in payload for k in ["sequence", "previous_sha256", "recorded_utc", "binding_sha256"]):
                raise CorruptCheckpoint("Reserved journal provenance")
            raw = bounded_json(sealed({**payload, "sequence": sequence+1, "previous_sha256": previous,
                                      "binding_sha256": s["binding"], "recorded_utc": datetime.now(timezone.utc).isoformat()}), s["budget"].event_bytes)
            if len(s["journal"]) >= s["budget"].events or s["used"]+len(raw) > s["budget"].total_bytes:
                raise ResourceLimit("Journal/total resource limit")
            self._fault("append", "before_commit")
            receipt = WriteReceipt(s["binding"], operation, digest(raw), sequence+1, digest(raw), event=raw)
            s["journal"].append(raw); s["used"] += len(raw); s["ops"][operation] = (intent, receipt)
            self._fault("append", "after_commit")
            return receipt

    def read_head(self, cap):
        with self._mutex:
            s = self._state(cap); previous = None
            if len(s["journal"]) > s["budget"].events: raise ResourceLimit("Journal limit")
            for sequence, raw in enumerate(s["journal"], 1):
                if type(raw) is not bytes or len(raw) > s["budget"].event_bytes: raise CorruptCheckpoint("Invalid journal bytes")
                event = unseal(raw)
                if event.get("sequence") != sequence or event.get("previous_sha256") != previous or event.get("binding_sha256") != s["binding"]:
                    raise CorruptCheckpoint("Journal gap, chain or run binding mismatch")
                previous = digest(raw)
            for key in s["objects"]: self.get_verified(cap, key)
            if len(s["objects"]) > s["budget"].objects or len(s["ops"]) > s["budget"].operations:
                raise ResourceLimit("Recovered metadata budget exceeded")
            actual_used = len(s["manifest"])+sum(len(v[0]) for v in s["objects"].values())+sum(map(len,s["journal"]))
            if actual_used != s["used"] or actual_used > s["budget"].total_bytes:
                raise CorruptCheckpoint("Partial persistence or resource accounting mismatch")
            for _, receipt in s["ops"].values():
                if receipt.binding_sha256 != s["binding"]: raise CorruptCheckpoint("Foreign receipt")
                if receipt.event is not None and (receipt.sequence > len(s["journal"]) or s["journal"][receipt.sequence-1] != receipt.event):
                    raise CorruptCheckpoint("Commit receipt without its event")
            return JournalHead(s["binding"], len(s["journal"]), previous, tuple(s["journal"]))

    @contextmanager
    def writer(self, cap):
        with self._mutex:
            s = self._state(cap)
            if s["lease"] is not None: raise WriterBusy("Writer already leased")
            s["lease"] = cap
        try: yield
        finally:
            with self._mutex:
                if s["lease"] is cap: s["lease"] = None

    def close(self, cap):
        with self._mutex:
            if not isinstance(cap, RunCapability): raise InvalidCapability("Unissued capability")
            if cap in self._closed: return
            # Expired authorization must never prevent owned handle/lease cleanup.
            if cap not in self._handles: raise InvalidCapability("Unissued capability")
            s, _ = self._handles[cap]
            if s["lease"] is cap: s["lease"] = None
            self._handles.pop(cap); self._closed.add(cap)

    # Trusted synthetic fault injection only; none of these are protocol methods.
    def fail_next(self, kind, phase): self._faults[(kind, phase)] = True
    def inspect(self, cap): return self._state(cap)
    def writer_owned(self, cap): return self._state(cap)["lease"] is cap
