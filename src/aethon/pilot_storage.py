"""Read-only storage observations and append-only private checkpoints."""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import uuid

from aethon.pilot_governance import canonical, digest, utc
from aethon.prospective import fingerprint


class CorruptCheckpoint(ValueError):
    pass


def safe_path(path, forbidden, directory=True):
    path = Path(path)
    if not path.is_absolute():
        raise ValueError("Absolute private path required")
    for component in [path, *path.parents]:
        info = component.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Symlink/reparse storage rejected")
    resolved = path.resolve(strict=True)
    if any(resolved == p or p in resolved.parents for p in map(Path.resolve, forbidden)):
        raise ValueError("Private destination is inside a repository/worktree")
    if directory and not resolved.is_dir():
        raise ValueError("Pre-provisioned private directory required")
    return resolved


def discover_repositories(root):
    """Includes externally located linked worktrees, not only .worktrees siblings."""
    common = os.fsdecode(subprocess.check_output(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=root)).rstrip("\r\n")
    entries = os.fsdecode(subprocess.check_output(["git", "worktree", "list", "--porcelain", "-z"], cwd=root))
    roots = [Path(common).parent, Path(common)]
    roots.extend(Path(line[9:]) for line in entries.split("\0") if line.startswith("worktree "))
    return sorted(set(p.resolve() for p in roots), key=str)


def probe_storage(path, forbidden):
    """Never sets ACL, enables encryption, schedules deletion or creates roots."""
    path = safe_path(path, forbidden)
    identity = {"path_sha256": fingerprint(str(path)), "device": path.stat().st_dev, "inode": path.stat().st_ino}
    if os.name == "nt":
        script = r'''
$ErrorActionPreference='Stop'
$p=$env:AETHON_STORAGE_PROBE_PATH
$a=Get-Acl -LiteralPath $p
$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$owner=$a.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
$rules=@($a.Access | ForEach-Object { @{sid=$_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value;type=$_.AccessControlType.ToString();rights=[int]$_.FileSystemRights} })
$v=Get-BitLockerVolume -MountPoint ([System.IO.Path]::GetPathRoot($p))
@{user=$sid;owner=$owner;protected=$a.AreAccessRulesProtected;rules=$rules;encryption=@{protection=$v.ProtectionStatus.ToString();status=$v.VolumeStatus.ToString();percent=$v.EncryptionPercentage}} | ConvertTo-Json -Depth 6 -Compress
'''
        try:
            shell = str(Path(os.environ.get("SystemRoot", "C:/Windows"))/"System32/WindowsPowerShell/v1.0/powershell.exe")
            p = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-Command", script],
                               env={**os.environ, "AETHON_STORAGE_PROBE_PATH": str(path)}, capture_output=True, timeout=30)
            if p.returncode:
                raise ValueError("Observation unavailable")
            observation = json.loads(p.stdout)
            allowed = {observation["user"], "S-1-5-18", "S-1-5-32-544"}
            acl = (observation["owner"] == observation["user"] and observation["protected"] is True
                   and any(rule["type"] == "Allow" and rule["sid"] == observation["user"] and rule["rights"] & 7 == 7 for rule in observation["rules"])
                   and all(rule["sid"] in allowed for rule in observation["rules"] if rule["type"] == "Allow"))
            encrypted = observation["encryption"] == {"protection": "On", "status": "FullyEncrypted", "percent": 100}
            identity.update(acl="PASS" if acl else "PENDING", encryption="PASS" if encrypted else "PENDING", observation=observation)
        except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
            identity.update(acl="PENDING", encryption="PENDING", reason="native_observation_unavailable")
    else:
        info = path.stat()
        identity.update(acl="PASS" if info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700 else "PENDING",
                        encryption="PENDING", reason="volume_encryption_not_independently_observed")
    return {"status": "PASS" if identity["acl"] == identity["encryption"] == "PASS" else "PENDING",
            "probe_fingerprint": fingerprint(identity), "observation": identity,
            "future_deletion": "NOT_AUDITED"}


def sealed(payload):
    return {"payload": payload, "sha256": digest(canonical(payload))}


def unseal(raw):
    try:
        record = json.loads(raw)
        if set(record) != {"payload", "sha256"} or record["sha256"] != digest(canonical(record["payload"])):
            raise ValueError("Hash mismatch")
        return record["payload"]
    except (ValueError, KeyError, TypeError) as exc:
        raise CorruptCheckpoint("Invalid checkpoint envelope") from exc


def immutable_write(path, raw):
    """Atomic no-clobber publication; a duplicate is allowed only byte-for-byte."""
    if path.exists():
        if path.is_symlink() or path.stat().st_nlink != 1 or path.read_bytes() != raw:
            raise CorruptCheckpoint("Refusing existing-object replacement")
        return
    temp = path.with_name("." + uuid.uuid4().hex + ".tmp")
    try:
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        # Unlike replace(), hard-link publication cannot overwrite a collision.
        try:
            os.link(temp, path)
        except FileExistsError:
            if path.is_symlink() or path.stat().st_nlink != 1 or path.read_bytes() != raw:
                raise CorruptCheckpoint("Concurrent object collision")
        if os.name != "nt":
            descriptor = os.open(path.parent, os.O_RDONLY)
            try: os.fsync(descriptor)
            finally: os.close(descriptor)
    finally:
        if temp.exists(): temp.unlink()  # Only this writer's owned temporary file.


TERMINAL = {"blocked", "completed", "reused", "no_response", "truncated", "inference_error",
            "evaluation_error", "contract_error", "interrupted_unknown", "evaluation_interrupted", "evaluation_pending"}
TRANSITIONS = {
    "pending": {"started", "blocked", "reused", "contract_error"},
    "started": {"generated", "no_response", "truncated", "inference_error", "contract_error", "interrupted_unknown"},
    "generated": {"evaluating", "completed", "evaluation_pending", "contract_error"},
    "evaluating": {"completed", "evaluation_error", "evaluation_interrupted", "contract_error"},
}


class PrivateRunStore:
    def __init__(self, root, manifest, authorization, forbidden, storage_observation):
        authorization.check(manifest["subject"])
        manifest = {**manifest, "authorization_provenance": {
            "policy_sha256": authorization.policy_sha256, "receipts_sha256": authorization.receipts_sha256,
            "launch_sha256": authorization.launch_sha256, "expires_at": authorization.expires_at}}
        self.authorization = authorization
        self.root = safe_path(root, forbidden)
        if manifest["subject"]["storage_root_sha256"] != fingerprint(str(self.root)):
            raise PermissionError("Authorization destination differs from storage root")
        self.forbidden = forbidden
        if storage_observation.get("status") != "PASS":
            raise PermissionError("Storage ACL/encryption observation pending")
        if storage_observation["observation"]["path_sha256"] != fingerprint(str(self.root)):
            raise PermissionError("Storage receipt belongs to a different directory")
        self.custodian = manifest["retention"]["custodian"]
        self.delete_after = manifest["retention"]["delete_after"]
        if not self.custodian or date.fromisoformat(self.delete_after) <= date.today():
            raise PermissionError("Concrete unexpired retention policy required")
        self.run_id = manifest["run_id"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", self.run_id):
            raise ValueError("Unsafe run ID")
        self.path = self.root/self.run_id
        if not self.path.exists(): self.path.mkdir(mode=0o700)
        safe_path(self.path, forbidden)
        self.events = self.path/"events"
        self.objects = self.path/"objects"
        for folder in [self.events, self.objects]:
            if not folder.exists(): folder.mkdir(mode=0o700)
            safe_path(folder, forbidden)
        self.identities = {p: (p.stat().st_dev, p.stat().st_ino) for p in [self.root, self.path, self.events, self.objects]}
        immutable_write(self.path/"manifest.json", canonical(sealed(manifest)))
        self.manifest = unseal((self.path/"manifest.json").read_bytes())
        if self.manifest != manifest: raise CorruptCheckpoint("Run fingerprint or inventory changed")
        self.load()

    def guard(self):
        self.authorization.check(self.manifest["subject"])
        if date.fromisoformat(self.delete_after) <= date.today(): raise PermissionError("Retention expired")
        safe_path(self.path, self.forbidden)
        safe_path(self.events, self.forbidden)
        safe_path(self.objects, self.forbidden)
        if any((p.stat().st_dev, p.stat().st_ino) != identity for p, identity in self.identities.items()):
            raise CorruptCheckpoint("Storage directory identity changed")

    @contextmanager
    def writer(self):
        self.guard()
        path = self.path/"writer.lock"
        token = canonical({"pid": os.getpid(), "owner_token": uuid.uuid4().hex})
        with path.open("xb") as stream: stream.write(token); stream.flush(); os.fsync(stream.fileno())
        try:
            self.load()
            yield
        finally:
            if path.read_bytes() == token: path.unlink()
            else: raise CorruptCheckpoint("Writer lock changed; manual inspection required")

    def load(self):
        self.slots = {s["slot_id"]: dict(s) for s in self.manifest["slots"]}
        if len(self.slots) != 120: raise CorruptCheckpoint("Incomplete or duplicate slot matrix")
        self.sequence, self.previous, self.suspended, self.defenses = 0, None, None, None
        files = sorted(self.events.glob("*.json"))
        for path in files:
            if path.name != f"{self.sequence + 1:06d}.json" or path.is_symlink() or path.stat().st_nlink != 1:
                raise CorruptCheckpoint("Journal gap or unsafe event")
            raw = path.read_bytes(); event = unseal(raw)
            try: utc(event["recorded_utc"])
            except (KeyError, ValueError): raise CorruptCheckpoint("Missing event time provenance")
            if event["sequence"] != self.sequence + 1 or event["previous_sha256"] != self.previous:
                raise CorruptCheckpoint("Journal chain mismatch")
            if event["kind"] == "slot":
                slot = self.slots[event["slot_id"]]
                if event["from_state"] != slot["state"] or event["to_state"] not in TRANSITIONS.get(slot["state"], set()):
                    raise CorruptCheckpoint("Illegal slot transition")
                slot.update(event["update"]); slot["state"] = event["to_state"]
                for field in ["response_ref", "evaluation_ref"]:
                    if slot.get(field): self.get(slot[field])
            elif event["kind"] == "suspend": self.suspended = event["reason"]
            elif event["kind"] == "defenses":
                if self.defenses is not None: raise CorruptCheckpoint("Duplicate frozen defenses")
                self.defenses = self.get(event["reference"])
                if set(self.defenses) != set(self.slots): raise CorruptCheckpoint("Incomplete defense matrix")
            else: raise CorruptCheckpoint("Unknown event kind")
            self.sequence += 1; self.previous = digest(raw)

    def put(self, payload):
        self.guard()
        raw = canonical(sealed({"run_fingerprint": self.manifest["run_fingerprint"], "data": payload}))
        key = digest(raw)
        immutable_write(self.objects/(key+".json"), raw)
        return key

    def get(self, key):
        if not isinstance(key, str) or not re.fullmatch(r"[a-f0-9]{64}", key): raise CorruptCheckpoint("Invalid object reference")
        path = self.objects/(key+".json")
        if path.is_symlink() or path.stat().st_nlink != 1: raise CorruptCheckpoint("Unsafe object")
        raw = path.read_bytes()
        if digest(raw) != key: raise CorruptCheckpoint("Corrupted object")
        scoped = unseal(raw)
        if scoped.get("run_fingerprint") != self.manifest["run_fingerprint"]:
            raise CorruptCheckpoint("Foreign-run object rejected")
        return scoped["data"]

    def append(self, event):
        self.guard()
        event = {**event, "sequence": self.sequence+1, "previous_sha256": self.previous,
                 "recorded_utc": datetime.now(timezone.utc).isoformat()}
        raw = canonical(sealed(event))
        immutable_write(self.events/f"{self.sequence+1:06d}.json", raw)
        if event["kind"] == "slot":
            self.slots[event["slot_id"]].update(event["update"])
            self.slots[event["slot_id"]]["state"] = event["to_state"]
        elif event["kind"] == "suspend":
            self.suspended = event["reason"]
        elif event["kind"] == "defenses":
            self.defenses = self.get(event["reference"])
        self.sequence += 1
        self.previous = digest(raw)

    def transition(self, slot_id, state, **update):
        before = self.slots[slot_id]["state"]
        if state not in TRANSITIONS.get(before, set()): raise CorruptCheckpoint("Invalid transition")
        if any(k in update for k in ["slot_id", "sample_id", "condition", "pair_id", "family_id", "scenario_id", "namespace", "source_id", "source_row_id", "label", "replicate", "fingerprint", "state"]):
            raise CorruptCheckpoint("Immutable slot identity cannot change")
        self.append({"kind": "slot", "slot_id": slot_id, "from_state": before, "to_state": state, "update": update})

    def suspend(self, reason): self.append({"kind": "suspend", "reason": reason})

    def pointer(self, name, payload=None):
        if not re.fullmatch(r"[a-f0-9]{64}\.(request|response|evaluation)", name):
            raise ValueError("Unsafe checkpoint name")
        self.guard()
        path = self.path/(name+".json")
        if payload is not None:
            immutable_write(path, canonical(sealed({"run_fingerprint": self.manifest["run_fingerprint"], "pointer_name": name, "data": payload})))
        if not path.exists(): return None
        if path.is_symlink() or path.stat().st_nlink != 1: raise CorruptCheckpoint("Unsafe checkpoint pointer")
        scoped = unseal(path.read_bytes())
        if scoped.get("run_fingerprint") != self.manifest["run_fingerprint"] or scoped.get("pointer_name") != name:
            raise CorruptCheckpoint("Foreign-run pointer rejected")
        return scoped["data"]

    def summary(self):
        return {"schema": "aethon.pilot-accounting.v1", "expected_slots": 120,
                "represented_slots": len(self.slots), "states": dict(Counter(s["state"] for s in self.slots.values())),
                "suspended": self.suspended, "accounting_complete": all(s["state"] in TERMINAL for s in self.slots.values()),
                "attempted_calls": sum(s.get("attempted", False) for s in self.slots.values()),
                "scientific_estimates_computed": False}
