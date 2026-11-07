"""Opaque persistence contract. No filesystem or production backend exists here."""
from dataclasses import dataclass
from abc import ABC, ABCMeta, abstractmethod
import json
import re
from typing import ContextManager

from aethon.pilot_governance import Authorization, canonical, digest


class CorruptCheckpoint(ValueError):
    """Persistence corruption/incompatibility: stop, never silently repair."""


class StorageCollision(CorruptCheckpoint): pass
class StaleHead(CorruptCheckpoint): pass
class ResourceLimit(CorruptCheckpoint): pass
class MissingObject(CorruptCheckpoint): pass
class WriterBusy(CorruptCheckpoint): pass
class InvalidIdentifier(CorruptCheckpoint): pass
class InvalidCapability(PermissionError): pass
class StorageInterrupted(RuntimeError): pass


class RunCapability:
    """Identity-only opaque handle. Backend issuance/registry is authoritative.

    Constructing/copying/pickling this Python object does not grant a capability.
    This is an API boundary, not protection against hostile Python in-process.
    """
    __slots__ = ()

    def __repr__(self): return "<opaque pilot run capability>"


@dataclass(frozen=True)
class StorageKey:
    kind: str
    identity: str
    role: str = ""

    def __post_init__(self):
        if (self.kind not in {"object", "checkpoint"} or not isinstance(self.identity, str)
                or re.fullmatch(r"[a-f0-9]{64}", self.identity) is None
                or (self.kind == "object" and self.role != "")
                or (self.kind == "checkpoint" and self.role not in {"request", "response", "evaluation"})):
            raise InvalidIdentifier("Structured content or checkpoint identity required")


@dataclass(frozen=True)
class OperationId:
    value: str

    def __post_init__(self):
        if not isinstance(self.value, str) or re.fullmatch(r"[a-f0-9]{64}", self.value) is None:
            raise InvalidIdentifier("Scoped operation digest required")


@dataclass(frozen=True)
class ResourceBudget:
    object_bytes: int = 2 * 1024 * 1024
    manifest_bytes: int = 2 * 1024 * 1024
    event_bytes: int = 64 * 1024
    total_bytes: int = 32 * 1024 * 1024
    objects: int = 2048
    events: int = 4096
    operations: int = 8192

    def __post_init__(self):
        ceilings = {"object_bytes": 8*1024*1024, "manifest_bytes": 8*1024*1024,
                    "event_bytes": 1024*1024, "total_bytes": 128*1024*1024,
                    "objects": 8192, "events": 16384, "operations": 32768}
        if any(type(getattr(self, k)) is not int or not 0 < getattr(self, k) <= v for k, v in ceilings.items()):
            raise ResourceLimit("Unsupported resource budget")


@dataclass(frozen=True)
class WriteReceipt:
    binding_sha256: str
    operation_id: OperationId
    data_sha256: str
    sequence: int = 0
    head_sha256: str | None = None
    durability: str = "SYNTHETIC_VOLATILE_NOT_PRODUCTION"
    event: bytes | None = None


@dataclass(frozen=True)
class JournalHead:
    binding_sha256: str
    sequence: int
    head_sha256: str | None
    events: tuple[bytes, ...]
    recovery_disposition: str = "SYNTHETIC_NO_INDEPENDENT_FRESHNESS_WITNESS"


def bounded_json(value, maximum):
    """Bound depth/nodes/strings before canonical serialization; reject NaN."""
    pending, count = [(value, 0)], 0
    while pending:
        item, depth = pending.pop(); count += 1
        if depth > 48 or count > 100000: raise ResourceLimit("JSON structure budget exceeded")
        if isinstance(item, dict):
            if len(item)*2 > 100000-count: raise ResourceLimit("JSON node budget exceeded")
            if any(not isinstance(k, str) for k in item): raise CorruptCheckpoint("String JSON keys required")
            pending.extend((x, depth+1) for pair in item.items() for x in pair)
        elif isinstance(item, (list, tuple)):
            if len(item) > 100000-count: raise ResourceLimit("JSON node budget exceeded")
            pending.extend((x, depth+1) for x in item)
        elif isinstance(item, str):
            if len(item) > maximum: raise ResourceLimit("String budget exceeded")
        elif item is not None and type(item) not in {int, float, bool}:
            raise CorruptCheckpoint("JSON data required")
    try: json.dumps(value, allow_nan=False)
    except (ValueError, TypeError, OverflowError) as exc: raise CorruptCheckpoint("Finite JSON data required") from exc
    raw = canonical(value)
    if len(raw) > maximum: raise ResourceLimit("Canonical byte budget exceeded")
    return raw


def sealed(payload): return {"payload": payload, "sha256": digest(canonical(payload))}


def unseal(raw):
    try:
        record = json.loads(raw)
        if set(record) != {"payload", "sha256"} or record["sha256"] != digest(canonical(record["payload"])):
            raise ValueError("Envelope mismatch")
        return record["payload"]
    except (ValueError, KeyError, TypeError, UnicodeError, RecursionError) as exc:
        raise CorruptCheckpoint("Invalid checkpoint envelope") from exc


_VALIDATED_MANIFEST_SEAL = object()


class ValidatedRunManifest:
    """Immutable proof object created only by StorageBackend.open_run validation."""
    __slots__ = ("_canonical_bytes",)

    def __init__(self, canonical_bytes: bytes, *, _seal=None):
        if _seal is not _VALIDATED_MANIFEST_SEAL or type(canonical_bytes) is not bytes:
            raise TypeError("ValidatedRunManifest is issued only by the base backend validator")
        object.__setattr__(self, "_canonical_bytes", canonical_bytes)

    def __setattr__(self, name, value):
        raise AttributeError("ValidatedRunManifest is immutable")

    @property
    def canonical_bytes(self): return self._canonical_bytes

    @property
    def document(self): return json.loads(self._canonical_bytes)


class _StorageBackendMeta(ABCMeta):
    def __new__(metaclass, name, bases, namespace, **kwargs):
        if any(isinstance(base, _StorageBackendMeta) for base in bases) and "open_run" in namespace:
            raise TypeError("StorageBackend.open_run is final; implement _open_validated_run")
        return super().__new__(metaclass, name, bases, namespace, **kwargs)


class StorageBackend(ABC, metaclass=_StorageBackendMeta):
    """Template-method backend: validation is mandatory before capability minting.

    Subclasses implement `_open_validated_run`; overriding `open_run` is rejected.
    This is an application contract, not protection from hostile Python reflection.
    Native implementations must use this validator and additionally bind a trusted
    root-object capability, durable commit policy and independent freshness policy.
    """
    def open_run(self, authorization, manifest: bytes, budget: ResourceBudget) -> RunCapability:
        if not isinstance(authorization, Authorization):
            raise InvalidCapability("Issued Authorization required")
        if not isinstance(budget, ResourceBudget) or type(manifest) is not bytes:
            raise CorruptCheckpoint("Typed manifest and budget required")
        if len(manifest) > budget.manifest_bytes:
            raise ResourceLimit("Manifest byte budget exceeded")
        try:
            parsed = json.loads(manifest)
            if canonical(parsed) != manifest:
                raise CorruptCheckpoint("Canonical manifest bytes required")
            bounded_json(parsed, budget.manifest_bytes)
            if not isinstance(parsed, dict) or not isinstance(parsed.get("subject"), dict):
                raise CorruptCheckpoint("Structured authorized subject required")
        except CorruptCheckpoint:
            raise
        except Exception as exc:
            raise CorruptCheckpoint("Scientific manifest validation failed") from exc
        authorization.check(parsed["subject"])
        try:
            from aethon.pilot_scientific_manifest import validate_manifest_document
            validate_manifest_document(parsed)
        except CorruptCheckpoint:
            raise
        except Exception as exc:
            raise CorruptCheckpoint("Scientific manifest validation failed") from exc
        expected = {"policy_sha256": authorization.policy_sha256,
                    "receipts_sha256": authorization.receipts_sha256,
                    "launch_sha256": authorization.launch_sha256,
                    "expires_at": authorization.expires_at,
                    "storage_custodian": authorization.storage_custodian,
                    "retention_delete_after": authorization.retention_delete_after,
                    "retention_plan_sha256": authorization.retention_plan_sha256}
        if parsed["authorization_provenance"] != expected:
            raise CorruptCheckpoint("Authorization provenance mismatch")
        if (parsed["retention"].get("custodian") != authorization.storage_custodian
                or parsed["retention"].get("delete_after") != authorization.retention_delete_after
                or not authorization.retention_plan_sha256):
            raise CorruptCheckpoint("Retention differs from signed storage approval")
        validated = ValidatedRunManifest(manifest, _seal=_VALIDATED_MANIFEST_SEAL)
        return self._open_validated_run(authorization, validated, budget)

    @abstractmethod
    def _open_validated_run(self, authorization, manifest: ValidatedRunManifest,
                            budget: ResourceBudget) -> RunCapability: ...

    @abstractmethod
    def put_if_absent(self, run: RunCapability, key: StorageKey, raw: bytes, operation: OperationId) -> WriteReceipt: ...

    @abstractmethod
    def get_verified(self, run: RunCapability, key: StorageKey) -> bytes | None: ...

    @abstractmethod
    def append_event(self, run: RunCapability, sequence: int, previous: str | None,
                     event: bytes, operation: OperationId) -> WriteReceipt: ...

    @abstractmethod
    def read_head(self, run: RunCapability) -> JournalHead: ...

    @abstractmethod
    def writer(self, run: RunCapability) -> ContextManager[None]: ...

    @abstractmethod
    def close(self, run: RunCapability) -> None: ...
