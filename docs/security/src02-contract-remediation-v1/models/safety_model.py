"""Finite abstract SRC-02 safety relation. No native I/O or inference."""
from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import dataclass, field, replace
from enum import Enum


class Outcome(str, Enum):
    NOT_COMMITTED = "NOT_COMMITTED"
    COMMIT_UNKNOWN = "COMMIT_UNKNOWN"
    COMMITTED = "COMMITTED"
    REJECTED = "REJECTED"


class Operation(str, Enum):
    INFERENCE = "INFERENCE"
    PERSISTENCE = "PERSISTENCE"
    ADMINISTRATIVE = "ADMINISTRATIVE"


class Infer(str, Enum):
    NONE = "NONE"
    INTENT_PREPARED = "INTENT_PREPARED"
    INTENT_DURABLE = "INTENT_DURABLE"
    DISPATCH_MAY_HAVE_STARTED = "DISPATCH_MAY_HAVE_STARTED"
    RESPONSE_OBSERVED = "RESPONSE_OBSERVED"
    RESPONSE_VERIFIED = "RESPONSE_VERIFIED"
    RESPONSE_DURABLE = "RESPONSE_DURABLE"
    RESPONSE_COMMITTED = "RESPONSE_COMMITTED"
    INTERRUPTED_UNKNOWN = "INTERRUPTED_UNKNOWN"


class Witness(str, Enum):
    MATCH = "MATCH"
    LOCAL_AHEAD = "LOCAL_AHEAD"
    WITNESS_AHEAD = "WITNESS_AHEAD"
    SAME_SEQUENCE_CONFLICT = "SAME_SEQUENCE_CONFLICT"
    UNAVAILABLE = "UNAVAILABLE"
    PENDING = "PENDING"


class WitnessQuery(str, Enum):
    NONE = "NONE"
    REQUESTED = "REQUESTED"
    UNAVAILABLE = "UNAVAILABLE"
    RECEIVED = "RECEIVED"
    AUTHENTICATED = "AUTHENTICATED"
    VALIDATED = "VALIDATED"
    RECONCILED = "RECONCILED"


class Recovery(str, Enum):
    CLEAN = "CLEAN"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    RECONCILED = "RECONCILED"
    BLOCKED = "BLOCKED"


class AuthorityState(str, Enum):
    ACTIVE = "ACTIVE"
    UNAVAILABLE = "UNAVAILABLE"
    REVOKED = "REVOKED"


@dataclass(frozen=True, order=True)
class PublishToken:
    token_id: str
    writer: str
    lease_id: str
    epoch: int
    expected_sequence: int
    expected_head: str
    authority_id: str
    revocation_epoch: int


@dataclass(frozen=True)
class State:
    # Immutable scientific and run identity. The duplicate bound fields model
    # the authenticated intent snapshot; transition code never accepts aliases.
    run_id: str = "run-fixture"
    bound_run_id: str = "run-fixture"
    slot_id: str = "slot-fixture-B0"
    bound_slot_id: str = "slot-fixture-B0"
    operation_id: str = "op-fixture"
    bound_operation_id: str = "op-fixture"
    manifest_digest: str = "manifest-fixture"
    bound_manifest_digest: str = "manifest-fixture"
    config_digest: str = "config-fixture"
    bound_config_digest: str = "config-fixture"
    operation: Operation = Operation.INFERENCE
    infer: Infer = Infer.NONE
    intent_durable: bool = False
    dispatch_authorized: bool = False
    dispatch_marker_durable: bool = False
    dispatch_count: int = 0
    response_bytes: bytes | None = None
    response_digest: str | None = None
    bound_response_digest: str | None = None
    response_observed: bool = False
    response_verified: bool = False
    response_durable: bool = False
    response_confirmed: bool = False
    object_durable: bool = False
    journal_durable: bool = False
    persisted: tuple[tuple[str, str], ...] = ()
    source_operation_id: str | None = None
    source_response_digest: str | None = None
    source_response_durable: bool = False
    sequence: int = 0
    head: str = "h0"
    head_durable: bool = True
    expected_sequence: int = 0
    expected_head: str = "h0"
    authority_id: str = "lease-authority-fixture"
    commit_authority_id: str = "lease-authority-fixture"
    authority_state: AuthorityState = AuthorityState.ACTIVE
    authority_serial: int = 0
    lease_transfer_serial: int = 0
    lease_transfer_id: str | None = None
    lease_history: tuple[tuple[str, str, int, int, str], ...] = (
        ("lease-A-7", "A", 7, 0, "lease-authority-fixture"),
    )
    lease_id: str = "lease-A-7"
    holder: str = "A"
    epoch: int = 7
    lease_id_a: str = "lease-A-7"
    epoch_a: int = 7
    lease_id_b: str = "lease-B-0"
    epoch_b: int = 0
    lease_expired: bool = False
    lease_revoked: bool = False
    revocation_epoch: int = 0
    prepared_publications: tuple[PublishToken, ...] = ()
    publish_token_id: str | None = None
    publish_lease_id: str | None = None
    publish_authority_id: str | None = None
    publish_epoch: int | None = None
    publish_writer: str | None = None
    publish_revocation_epoch: int | None = None
    publish_lease_transfer_serial: int = 0
    witness_required: bool = True
    # Immutable launch-grant witness policy bound at initial State construction.
    bound_witness_required: bool | None = None
    policy_epoch: int = 1
    witness_identity: str = "witness-fixture"
    witness: Witness = Witness.MATCH
    witness_available: bool = True
    witness_sequence: int = 0
    witness_head: str = "h0"
    witness_policy_epoch: int = 1
    witness_revocation_epoch: int = 0
    witness_op: str | None = None
    witness_expected: tuple[int, str] | None = None
    witness_next: tuple[int, str] | None = None
    witness_committed_op: str | None = None
    witness_ack: bool = False
    witness_query: WitnessQuery = WitnessQuery.NONE
    witness_query_run_id: str | None = None
    witness_query_operation_id: str | None = None
    witness_query_policy_epoch: int | None = None
    witness_query_revocation_epoch: int | None = None
    witness_response_run_id: str | None = None
    witness_response_operation_id: str | None = None
    witness_response_policy_epoch: int | None = None
    witness_response_revocation_epoch: int | None = None
    witness_response_sequence: int | None = None
    witness_response_head: str | None = None
    witness_response_committed_op: str | None = None
    witness_response_signer: str | None = None
    witness_response_signature_valid: bool = False
    witness_response_fresh: bool = False
    witness_response_revocation_valid: bool = False
    witness_response_valid: bool = False
    # Frozen verification-time claim tuple. Reconciliation cannot rely on a stale boolean.
    witness_verified_binding: tuple[object, ...] | None = None
    ack: bool = False
    revoked: bool = False
    quota: bool = False
    recovery_blocked: bool = False
    recovery_status: Recovery = Recovery.CLEAN
    history: tuple[str, ...] = field(default=(), compare=False, hash=False)

    def __post_init__(self) -> None:
        # A newly constructed fixture fixes its witness policy. dataclasses.replace
        # retains this field, so changing only the policy flag is rejected.
        if self.bound_witness_required is None:
            object.__setattr__(self, "bound_witness_required", self.witness_required)


class Reject(ValueError):
    pass


def step(s: State, name: str, **changes: object) -> State:
    return replace(s, **changes, history=s.history + (name,))


def _response_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _witness_claims(s: State) -> tuple[object, ...]:
    """Exact evidence and request bindings certified at verification time.

    This is an abstract immutable snapshot, NOT a cryptographic authenticator.
    """
    return (
        s.witness_identity, s.run_id, s.operation_id, s.witness_required,
        s.bound_witness_required, s.policy_epoch,
        s.revocation_epoch, s.witness_op, s.witness_expected, s.witness_next,
        s.witness_query_run_id, s.witness_query_operation_id,
        s.witness_query_policy_epoch, s.witness_query_revocation_epoch,
        s.witness_response_signer, s.witness_response_signature_valid,
        s.witness_response_fresh, s.witness_response_revocation_valid,
        s.witness_response_run_id, s.witness_response_operation_id,
        s.witness_response_policy_epoch, s.witness_response_revocation_epoch,
        s.witness_response_sequence, s.witness_response_head,
        s.witness_response_committed_op,
    )


def _bind_witness_evidence(s: State) -> State:
    """Capture the exact fields accepted by the trusted abstract verifier."""
    return replace(s, witness_verified_binding=_witness_claims(s))


def _check_witness_evidence(s: State) -> None:
    """Reject changed claims at every use, including after acknowledgment.

    Recheck stable claims and original query binding without requiring the
    remote service to remain online after a previously valid commit.
    """
    if not s.witness_response_valid:
        return
    if s.witness_verified_binding is None or s.witness_verified_binding != _witness_claims(s):
        raise Reject("witness verified evidence was altered after validation")
    if (not s.witness_response_signature_valid or not s.witness_response_fresh
            or not s.witness_response_revocation_valid
            or s.witness_response_signer != s.witness_identity):
        raise Reject("witness authenticated signer, signature, freshness or revocation invalid")
    if (s.witness_response_run_id, s.witness_response_operation_id,
            s.witness_response_policy_epoch, s.witness_response_revocation_epoch) != (
            s.run_id, s.operation_id, s.policy_epoch, s.revocation_epoch):
        raise Reject("witness evidence run/operation/policy/revocation mismatch")
    direct_advance = "witness_advance_result" in s.history and s.witness_query_run_id is None
    if not direct_advance and (
            s.witness_query_run_id, s.witness_query_operation_id,
            s.witness_query_policy_epoch, s.witness_query_revocation_epoch) != (
            s.run_id, s.operation_id, s.policy_epoch, s.revocation_epoch):
        raise Reject("witness evidence is not bound to its authenticated request")
    pair = (s.witness_response_sequence, s.witness_response_head)
    permitted = {(s.sequence, s.head)}
    if s.witness_expected is not None:
        permitted.add(s.witness_expected)
    if s.witness_next is not None:
        permitted.add(s.witness_next)
    if pair not in permitted:
        raise Reject("witness evidence sequence/head inconsistent with commit")
    if s.witness_next is not None and pair == s.witness_next:
        if s.witness_response_committed_op != s.operation_id:
            raise Reject("witness evidence committed operation mismatch")
    if s.witness_expected is not None and pair == s.witness_expected:
        if s.witness_response_committed_op not in (None, s.operation_id):
            raise Reject("witness predecessor operation mismatch")
    if s.witness_ack and (pair != (s.sequence, s.head)
                          or s.witness_response_committed_op != s.operation_id):
        raise Reject("witness acknowledged response does not bind committed head")


def validate(s: State) -> None:
    required = (s.run_id, s.slot_id, s.operation_id, s.manifest_digest, s.config_digest,
                s.authority_id, s.commit_authority_id)
    if not all(required):
        raise Reject("missing immutable run, slot, operation, configuration or authority binding")
    if (s.run_id, s.slot_id, s.operation_id, s.manifest_digest, s.config_digest) != (
        s.bound_run_id, s.bound_slot_id, s.bound_operation_id,
        s.bound_manifest_digest, s.bound_config_digest
    ):
        raise Reject("run/slot/operation/manifest/configuration binding changed")
    if s.commit_authority_id != s.authority_id:
        raise Reject("commit authority identity changed")
    if s.witness_required is not s.bound_witness_required:
        raise Reject("witness policy differs from immutable launch-grant binding")
    _check_witness_evidence(s)

    if s.operation is not Operation.INFERENCE and any((
        s.infer is not Infer.NONE, s.intent_durable, s.dispatch_authorized,
        s.dispatch_marker_durable, s.dispatch_count, s.response_observed,
        s.response_verified, s.response_durable, s.response_confirmed, s.ack,
    )):
        raise Reject("non-inference operation cannot carry inference response authority")
    if s.operation is Operation.ADMINISTRATIVE and (s.object_durable or s.journal_durable):
        raise Reject("administrative operation cannot persist an inference response")
    if s.operation is Operation.ADMINISTRATIVE and s.response_bytes is not None:
        raise Reject("administrative operation cannot masquerade as an inference response")

    if s.dispatch_count not in (0, 1):
        raise Reject("at-most-once dispatch marker violated")
    if s.dispatch_count != int(s.dispatch_marker_durable):
        raise Reject("dispatch count and durable marker disagree")
    if s.intent_durable != ("durable_intent" in s.history):
        raise Reject("intent durability/history mismatch")
    if s.dispatch_authorized != ("authorize_dispatch" in s.history):
        raise Reject("dispatch authorization/history mismatch")
    if s.dispatch_marker_durable != ("mark_dispatch" in s.history):
        raise Reject("dispatch marker/history mismatch")
    if s.response_observed != ("response_observed" in s.history):
        raise Reject("response observation/history mismatch")
    if s.response_verified != ("verify_response" in s.history):
        raise Reject("response verification/history mismatch")
    if s.response_durable != ("response_durable" in s.history):
        raise Reject("response durability/history mismatch")
    if s.object_durable != any(x in s.history for x in ("persist_object", "persist_source", "persist_retry")):
        raise Reject("object durability/history mismatch")
    if s.journal_durable != ("journal_durable" in s.history):
        raise Reject("journal durability/history mismatch")

    if s.infer is Infer.NONE:
        if any(x in s.history for x in ("prepare_intent", "durable_intent", "authorize_dispatch",
                                       "mark_dispatch", "response_observed", "verify_response",
                                       "response_durable")):
            raise Reject("inference history exists without an inference state")
    elif "prepare_intent" not in s.history:
        raise Reject("inference state lacks prepared intent")
    if s.intent_durable and (s.infer is Infer.NONE or "prepare_intent" not in s.history):
        raise Reject("durable intent lacks prepared intent")
    if s.dispatch_authorized and (not s.intent_durable or "durable_intent" not in s.history):
        raise Reject("dispatch authorization precedes durable intent")
    if s.dispatch_marker_durable and (not s.dispatch_authorized or not s.intent_durable):
        raise Reject("possible dispatch lacks authorized durable intent")
    if s.dispatch_marker_durable and s.dispatch_count != 1:
        raise Reject("possible dispatch lacks exactly one durable marker")
    if s.response_observed and (not s.dispatch_marker_durable or s.response_bytes is None
                                or len(s.response_bytes) == 0 or not s.response_digest):
        raise Reject("observed response lacks dispatch or exact nonempty bytes")
    if (s.response_bytes is None) != (s.response_digest is None):
        raise Reject("response bytes and digest presence differ")
    if s.response_observed and _response_hash(s.response_bytes or b"") != s.response_digest:
        raise Reject("observed response digest mismatch")
    if s.bound_response_digest != s.response_digest:
        raise Reject("response digest binding changed")
    if s.response_verified and (not s.response_observed or not s.response_digest
                                or _response_hash(s.response_bytes or b"") != s.response_digest):
        raise Reject("response verification lacks exact observed content")
    if s.response_durable and not s.response_verified:
        raise Reject("durable response lacks verified response")
    if s.object_durable:
        if s.operation is Operation.INFERENCE:
            if not (s.response_observed and s.response_verified and s.response_durable):
                raise Reject("inference object lacks durable verified response provenance")
            if (s.operation_id, s.response_digest or "") not in s.persisted:
                raise Reject("durable response object lacks exact operation/digest record")
        elif s.operation is Operation.PERSISTENCE:
            if not (s.source_response_durable and s.source_operation_id
                    and s.source_response_digest
                    and (s.source_operation_id, s.source_response_digest) in s.persisted):
                raise Reject("persistence operation lacks a durable source response receipt")
        else:
            raise Reject("administrative operation cannot create response objects")
    if s.response_confirmed and not (s.object_durable and s.journal_durable
                                     and s.head_durable and s.sequence > 0):
        raise Reject("response confirmation lacks object/journal/head durability")
    if s.response_confirmed != ("ack" in s.history) or s.ack != ("ack" in s.history):
        raise Reject("response confirmation and acknowledgment history disagree")

    order = ("prepare_intent", "durable_intent", "authorize_dispatch", "mark_dispatch",
             "response_observed", "verify_response", "response_durable", "persist_object",
             "persist_source", "journal_durable", "prepare_publish", "publish", "head_durable")
    positions = [s.history.index(event) for event in order if event in s.history]
    if positions != sorted(positions) or s.history.count("publish") > 1:
        raise Reject("transaction history violates legal order")
    if min(s.sequence, s.expected_sequence, s.witness_sequence, s.epoch,
           s.authority_serial, s.revocation_epoch) < 0:
        raise Reject("negative sequence, epoch or serial")
    if s.expected_sequence > s.sequence:
        raise Reject("expected head ahead of local head")
    if s.sequence != s.history.count("publish"):
        raise Reject("head sequence differs from publication history")
    if s.sequence == 0 and (s.head != "h0" or s.publish_epoch is not None):
        raise Reject("non-initial head without publication")
    if s.sequence > 0:
        if not (s.object_durable and s.journal_durable):
            raise Reject("published head lacks durable response object/journal")
        if s.head != f"h{s.sequence}:{s.response_digest}":
            raise Reject("head does not bind exact response digest")
        if not (0 <= s.publish_lease_transfer_serial < len(s.lease_history)):
            raise Reject("publication references unknown lease-transfer generation")
        if s.lease_history[s.publish_lease_transfer_serial] != (
            s.publish_lease_id, s.publish_writer, s.publish_epoch,
            s.publish_revocation_epoch, s.publish_authority_id
        ):
            raise Reject("publication lease/authority snapshot is not in authority history")
        if s.head_durable and "head_durable" not in s.history:
            raise Reject("head durability event absent")
    if s.publish_token_id is not None and "publish" not in s.history:
        raise Reject("publication token recorded without publication")
    if s.revoked and "revoke" not in s.history:
        raise Reject("revocation lacks transition")
    if s.lease_revoked and not s.revoked:
        raise Reject("lease revocation diverges from policy revocation")

    if s.ack:
        if not s.response_confirmed or not (s.object_durable and s.journal_durable and s.head_durable):
            raise Reject("acknowledgment before response and local durability")
        if s.revoked or s.lease_expired or s.lease_revoked or s.quota or s.recovery_blocked:
            raise Reject("acknowledgment after authority/resource/recovery failure")
        if (s.publish_writer, s.publish_lease_id, s.publish_epoch,
            s.publish_authority_id, s.publish_revocation_epoch) != (
            s.holder, s.lease_id, s.epoch, s.authority_id, s.revocation_epoch
        ):
            raise Reject("acknowledgment after lease/authority transfer or revocation")
        if s.witness_required and not (
            s.witness_ack and s.witness is Witness.MATCH
            and s.witness_query is WitnessQuery.RECONCILED
            and s.witness_response_valid
            and (s.witness_sequence, s.witness_head) == (s.sequence, s.head)
            and s.witness_policy_epoch == s.policy_epoch
            and s.witness_revocation_epoch == s.revocation_epoch
        ):
            raise Reject("acknowledgment lacks authenticated current witness proof")
    if s.witness_ack and not s.witness_response_valid:
        # Direct compare-and-advance returns an authenticated result modeled by
        # `witness_advance_result`; query reconciliation uses a validated proof.
        if "witness_advance_result" not in s.history:
            raise Reject("witness ack lacks authenticated evidence")
    if s.witness_query is WitnessQuery.RECONCILED:
        if not s.witness_response_valid or not any(
            event in s.history for event in ("witness_reconcile", "witness_advance_result")
        ):
            raise Reject("RECONCILED lacks validated remote evidence")
    if s.witness_query is WitnessQuery.REQUESTED and "witness_query" not in s.history:
        raise Reject("witness request state lacks request transition")
    if s.witness_query is WitnessQuery.RECEIVED and "witness_response" not in s.history:
        raise Reject("witness response state lacks received response")
    if s.witness_query is WitnessQuery.AUTHENTICATED and (
        "witness_authenticate" not in s.history or not s.witness_response_signature_valid
        or s.witness_response_signer != s.witness_identity
    ):
        raise Reject("witness authentication state lacks verified signer")
    if s.witness_query is WitnessQuery.VALIDATED and "witness_verify" not in s.history:
        raise Reject("witness validation state lacks validation transition")
    if s.witness_query is WitnessQuery.UNAVAILABLE and not s.recovery_blocked:
        raise Reject("unavailable witness query cannot clear recovery block")
    if s.witness_response_valid and s.witness_query not in {
        WitnessQuery.VALIDATED, WitnessQuery.RECONCILED
    }:
        raise Reject("validated witness evidence in inconsistent query state")

    if s.recovery_blocked and s.recovery_status not in {
        Recovery.RECONCILIATION_REQUIRED, Recovery.BLOCKED
    }:
        raise Reject("recovery flag/status mismatch")
    if not s.recovery_blocked and s.recovery_status in {
        Recovery.RECONCILIATION_REQUIRED, Recovery.BLOCKED
    }:
        raise Reject("blocked recovery status without block")
    if s.infer is Infer.INTERRUPTED_UNKNOWN and not (
        s.dispatch_marker_durable and not s.response_durable
        and any(x in s.history for x in ("crash", "recover"))
    ):
        raise Reject("unknown inference is not tied to uncertain dispatch")
    if s.ack and s.infer is not Infer.RESPONSE_COMMITTED:
        raise Reject("ack is not an inference response commit")


def classify(s: State) -> Outcome:
    validate(s)
    if s.ack:
        return Outcome.COMMITTED
    if s.infer is Infer.NONE and not s.object_durable and not s.journal_durable and s.sequence == 0:
        return Outcome.NOT_COMMITTED
    return Outcome.COMMIT_UNKNOWN


def classify_snapshot(**fields: object) -> Outcome:
    try:
        return classify(State(**fields))  # type: ignore[arg-type]
    except (TypeError, Reject):
        return Outcome.REJECTED


def apply(s: State, action: str, *, writer: str | None = None,
          epoch: int | None = None, lease_id: str | None = None,
          authority_id: str | None = None, token_id: str | None = None,
          op: str | None = None, run_id: str | None = None,
          slot_id: str | None = None, manifest_digest: str | None = None,
          config_digest: str | None = None, response: bytes | None = None,
          mode: str | None = None) -> State:
    validate(s)
    if s.ack:
        raise Reject("acknowledged response is terminal")
    if s.recovery_blocked and action not in {
        "recover", "witness_query", "witness_response", "witness_verify",
        "witness_authenticate", "witness_reconcile", "crash", "revoke", "witness_restore",
    }:
        raise Reject("recovery is required before further state changes")
    if action == "prepare_intent":
        if s.operation is not Operation.INFERENCE or s.infer is not Infer.NONE or s.revoked or s.quota:
            raise Reject("only an active inference operation can prepare an intent")
        return step(s, action, infer=Infer.INTENT_PREPARED)
    if action == "durable_intent":
        if s.operation is not Operation.INFERENCE or s.infer is not Infer.INTENT_PREPARED:
            raise Reject("inference intent is not prepared")
        if s.revoked or s.quota or s.bound_operation_id != s.operation_id:
            raise Reject("intent authority or resources invalid")
        return step(s, action, infer=Infer.INTENT_DURABLE, intent_durable=True)
    if action == "authorize_dispatch":
        if (s.operation is not Operation.INFERENCE or s.infer is not Infer.INTENT_DURABLE
                or not s.intent_durable or s.revoked or s.quota
                or op != s.operation_id or run_id != s.run_id or slot_id != s.slot_id
                or manifest_digest != s.manifest_digest or config_digest != s.config_digest):
            raise Reject("dispatch authorization is not bound to durable run/slot/config intent")
        return step(s, action, dispatch_authorized=True)
    if action == "mark_dispatch":
        if (not s.dispatch_authorized or s.infer is not Infer.INTENT_DURABLE
                or not s.intent_durable or s.dispatch_marker_durable
                or op != s.operation_id or s.revoked or s.quota):
            raise Reject("dispatch requires single authorized durable intent")
        return step(s, action, infer=Infer.DISPATCH_MAY_HAVE_STARTED,
                    dispatch_marker_durable=True, dispatch_count=1)
    if action == "response_observed":
        if (s.operation is not Operation.INFERENCE or s.infer is not Infer.DISPATCH_MAY_HAVE_STARTED
                or not s.dispatch_marker_durable or response is None or len(response) == 0
                or run_id != s.run_id or slot_id != s.slot_id or op != s.operation_id
                or manifest_digest != s.manifest_digest or config_digest != s.config_digest):
            raise Reject("response observation lacks exact dispatched run/slot/config binding")
        digest = _response_hash(response)
        return step(s, action, infer=Infer.RESPONSE_OBSERVED,
                    response_bytes=bytes(response), response_digest=digest,
                    bound_response_digest=digest, response_observed=True)
    if action == "verify_response":
        if (s.operation is not Operation.INFERENCE or not s.response_observed
                or s.infer is not Infer.RESPONSE_OBSERVED or not s.response_bytes
                or _response_hash(s.response_bytes) != s.response_digest):
            raise Reject("no exact observed response to verify")
        return step(s, action, infer=Infer.RESPONSE_VERIFIED, response_verified=True)
    if action == "response_durable":
        if s.infer is not Infer.RESPONSE_VERIFIED or not s.response_verified or s.revoked or s.quota:
            raise Reject("only a verified exact response can be made durable")
        return step(s, action, infer=Infer.RESPONSE_DURABLE, response_durable=True)
    if action == "retry_inference":
        if (s.infer is not Infer.INTENT_DURABLE or s.dispatch_marker_durable
                or s.dispatch_count != 0 or s.revoked or s.quota):
            raise Reject("inference outcome may be uncertain; new dispatch forbidden")
        # This only records the proof-backed safe retry authorization. It does
        # not invoke inference; the same run/slot/operation/config remains bound.
        return step(s, action)
    if action == "persist_object":
        if (s.operation is not Operation.INFERENCE or s.infer is not Infer.RESPONSE_DURABLE
                or not (s.response_observed and s.response_verified and s.response_durable)
                or not s.response_bytes or s.revoked or s.quota):
            raise Reject("inference persistence requires the exact durable observed response")
        key = (s.operation_id, s.response_digest or "")
        if s.persisted and key not in s.persisted:
            raise Reject("Operation ID collision with different response bytes")
        return step(s, action, object_durable=True, persisted=(key,))
    if action == "persist_source":
        if (s.operation is not Operation.PERSISTENCE or not s.source_response_durable
                or not s.source_operation_id or not s.source_response_digest
                or s.revoked or s.quota):
            raise Reject("persistence operation requires an existing durable source response receipt")
        key = (s.source_operation_id, s.source_response_digest)
        if s.persisted and key not in s.persisted:
            raise Reject("source response Operation ID collision")
        return step(s, action, object_durable=True, persisted=(key,))
    if action == "persist_retry":
        if s.operation is Operation.PERSISTENCE:
            key = (s.source_operation_id or "", s.source_response_digest or "")
            source_is_durable = s.source_response_durable
        else:
            key = (s.operation_id, s.response_digest or "")
            source_is_durable = s.response_durable
        if (not s.object_durable or not source_is_durable or key not in s.persisted
                or s.revoked or s.quota):
            raise Reject("retry is not exact idempotent persistence of durable response")
        return step(s, action)
    if action == "persist_conflicting_bytes":
        raise Reject("same Operation ID with different response bytes")
    if action == "journal_durable":
        if not s.object_durable or s.journal_durable or s.revoked or s.quota:
            raise Reject("journal requires immutable durable response object")
        return step(s, action, journal_durable=True)
    if action == "prepare_publish":
        if (not s.object_durable or not s.journal_durable or not s.response_durable
                or s.authority_state is not AuthorityState.ACTIVE or s.lease_expired
                or s.lease_revoked or s.revoked or s.quota or s.recovery_blocked):
            raise Reject("publication preparation lacks durable response or active authority")
        if (writer, lease_id, epoch, authority_id) != (
            s.holder, s.lease_id, s.epoch, s.authority_id
        ):
            raise Reject("publication preparation does not hold current lease authority")
        if (s.sequence, s.head) != (s.expected_sequence, s.expected_head):
            raise Reject("publication expected head is stale")
        tid = token_id or f"pub-{writer}-{lease_id}-{s.sequence}"
        token = PublishToken(tid, writer or "", lease_id or "", epoch or 0,
                             s.expected_sequence, s.expected_head, authority_id or "",
                             s.revocation_epoch)
        if any(item.token_id == tid and item != token for item in s.prepared_publications):
            raise Reject("publication token collision")
        if token in s.prepared_publications:
            return s
        return step(s, action, prepared_publications=tuple(sorted((*s.prepared_publications, token))))
    if action == "publish":
        intent = next((x for x in s.prepared_publications if x.token_id == token_id), None)
        if intent is None:
            raise Reject("unknown publication token")
        # One abstract authority serializes lease transfers and publication.
        # All compares and head mutation occur in this indivisible transition.
        if (s.authority_state is not AuthorityState.ACTIVE or intent.authority_id != s.authority_id
                or s.commit_authority_id != s.authority_id or s.lease_expired or s.lease_revoked
                or s.revoked or s.quota or s.recovery_blocked):
            raise Reject("commit authority, lease, revocation or resources invalid")
        if (intent.writer, intent.lease_id, intent.epoch, intent.revocation_epoch) != (
            s.holder, s.lease_id, s.epoch, s.revocation_epoch
        ):
            raise Reject("stale lease identity, holder, epoch or revocation epoch")
        if (intent.expected_sequence, intent.expected_head) != (s.sequence, s.head):
            raise Reject("expected-head compare-and-swap conflict")
        if not (s.object_durable and s.journal_durable and s.response_durable
                and s.response_verified and s.response_observed):
            raise Reject("response provenance or local durability barriers missing")
        return step(s, action, sequence=s.sequence + 1,
                    head=f"h{s.sequence + 1}:{s.response_digest}", head_durable=False,
                    expected_sequence=s.sequence, expected_head=s.head,
                    publish_token_id=intent.token_id, publish_lease_id=intent.lease_id,
                    publish_authority_id=intent.authority_id, publish_epoch=intent.epoch,
                    publish_writer=intent.writer,
                    publish_revocation_epoch=intent.revocation_epoch,
                    publish_lease_transfer_serial=s.lease_transfer_serial,
                    authority_serial=s.authority_serial + 1,
                    infer=Infer.RESPONSE_COMMITTED,
                    witness=Witness.LOCAL_AHEAD if s.witness_required else s.witness)
    if action == "head_durable":
        if s.sequence == 0 or s.head_durable or not (s.object_durable and s.journal_durable):
            raise Reject("head barrier out of order")
        if ((s.publish_writer, s.publish_lease_id, s.publish_epoch,
             s.publish_authority_id, s.publish_revocation_epoch) !=
            (s.holder, s.lease_id, s.epoch, s.authority_id, s.revocation_epoch)
                or s.publish_token_id is None or s.publish_authority_id != s.authority_id
                or s.publish_revocation_epoch != s.revocation_epoch or s.revoked):
            raise Reject("fence/authority/revocation changed before head durability")
        return step(s, action, head_durable=True)
    if action == "transfer":
        if (s.authority_state is not AuthorityState.ACTIVE or s.lease_expired or s.lease_revoked
                or s.revoked or s.sequence and not s.head_durable
                or (writer, lease_id, epoch, authority_id) !=
                   (s.holder, s.lease_id, s.epoch, s.authority_id)):
            raise Reject("only current valid lease holder can transfer through authority")
        new_holder = "B" if writer == "A" else "A"
        new_epoch = s.epoch + 1
        new_serial = s.lease_transfer_serial + 1
        new_lease = f"lease-{new_holder}-{new_epoch}"
        changes: dict[str, object] = {"holder": new_holder, "epoch": new_epoch,
            "lease_id": new_lease, "lease_transfer_serial": new_serial,
            "lease_transfer_id": f"transfer-{new_serial}", "authority_serial": s.authority_serial + 1,
            "lease_expired": False,
            "lease_history": s.lease_history + ((new_lease, new_holder, new_epoch,
                                                   s.revocation_epoch, s.authority_id),)}
        changes["lease_id_b" if new_holder == "B" else "lease_id_a"] = new_lease
        changes["epoch_b" if new_holder == "B" else "epoch_a"] = new_epoch
        return step(s, action, **changes)
    if action == "expire_lease":
        return step(s, action, lease_expired=True, recovery_blocked=True,
                    recovery_status=Recovery.BLOCKED)
    if action == "authority_unavailable":
        return step(s, action, authority_state=AuthorityState.UNAVAILABLE,
                    recovery_blocked=True, recovery_status=Recovery.BLOCKED)
    if action == "witness_prepare":
        if not s.witness_required or not s.head_durable or not s.witness_available or s.revoked:
            raise Reject("witness unavailable or local head not durable")
        if s.witness_policy_epoch != s.policy_epoch:
            raise Reject("witness policy epoch differs")
        expected, nxt = (s.witness_sequence, s.witness_head), (s.sequence, s.head)
        if s.witness_op:
            if (s.witness_op, s.witness_expected, s.witness_next) == (op or s.operation_id, expected, nxt):
                return s
            raise Reject("conflicting witness operation")
        if expected != (s.expected_sequence, s.expected_head) or nxt[0] != expected[0] + 1:
            raise Reject("witness CAS predecessor/sequence mismatch")
        return step(s, action, witness_op=op or s.operation_id,
                    witness_expected=expected, witness_next=nxt, witness=Witness.PENDING)
    if action == "witness_advance":
        if (not s.witness_available or not s.witness_op or not s.witness_next
                or s.witness_op != s.operation_id or s.witness_policy_epoch != s.policy_epoch
                or s.revoked or s.lease_revoked):
            raise Reject("witness compare-and-advance unavailable or not operation-bound")
        if s.witness_committed_op == s.witness_op:
            if (s.witness_sequence, s.witness_head) != s.witness_next:
                raise Reject("idempotent witness result conflicts with recorded next tuple")
            seq, head = s.witness_next
            result = step(s, "witness_advance_result", witness_ack=True, witness=Witness.MATCH,
                        witness_query=WitnessQuery.RECONCILED, witness_response_valid=True,
                        witness_response_run_id=s.run_id,
                        witness_response_operation_id=s.operation_id,
                        witness_response_policy_epoch=s.policy_epoch,
                        witness_response_revocation_epoch=s.revocation_epoch,
                        witness_response_sequence=seq, witness_response_head=head,
                        witness_response_committed_op=s.operation_id,
                        witness_response_signer=s.witness_identity,
                        witness_response_signature_valid=True, witness_response_fresh=True,
                        witness_response_revocation_valid=True)
            return _bind_witness_evidence(result)
        if (s.witness_sequence, s.witness_head) != s.witness_expected:
            raise Reject("witness expected-state compare failed")
        seq, head = s.witness_next
        result = step(s, "witness_advance_result", witness_sequence=seq, witness_head=head,
                    witness_policy_epoch=s.policy_epoch, witness_revocation_epoch=s.revocation_epoch,
                    witness_committed_op=s.witness_op, witness_ack=True, witness=Witness.MATCH,
                    witness_query=WitnessQuery.RECONCILED, witness_response_valid=True,
                    witness_response_run_id=s.run_id,
                    witness_response_operation_id=s.operation_id,
                    witness_response_policy_epoch=s.policy_epoch,
                    witness_response_revocation_epoch=s.revocation_epoch,
                    witness_response_sequence=seq, witness_response_head=head,
                    witness_response_committed_op=s.operation_id,
                    witness_response_signer=s.witness_identity,
                    witness_response_signature_valid=True, witness_response_fresh=True,
                    witness_response_revocation_valid=True)
        return _bind_witness_evidence(result)
    if action == "witness_timeout_before_commit":
        if not s.witness_op or s.witness_committed_op == s.witness_op:
            raise Reject("no pending witness operation")
        return step(s, action, witness_ack=False, witness=Witness.PENDING,
                    recovery_blocked=True, recovery_status=Recovery.RECONCILIATION_REQUIRED,
                    witness_query=WitnessQuery.NONE, witness_response_valid=False)
    if action == "witness_timeout_after_commit":
        if s.witness_committed_op != s.witness_op or not s.witness_op:
            raise Reject("witness operation not remotely committed")
        return step(s, action, witness_ack=False, witness=Witness.PENDING,
                    recovery_blocked=True, recovery_status=Recovery.RECONCILIATION_REQUIRED,
                    witness_query=WitnessQuery.NONE, witness_response_valid=False)
    if action == "witness_query":
        if not s.witness_required:
            raise Reject("no witness configured")
        if not s.witness_available:
            return step(s, action, witness_query=WitnessQuery.UNAVAILABLE,
                        witness_ack=False, witness=Witness.UNAVAILABLE,
                        recovery_blocked=True, recovery_status=Recovery.BLOCKED,
                        witness_response_valid=False)
        return step(s, action, witness_query=WitnessQuery.REQUESTED,
                    witness_query_run_id=s.run_id, witness_query_operation_id=s.operation_id,
                    witness_query_policy_epoch=s.policy_epoch,
                    witness_query_revocation_epoch=s.revocation_epoch,
                    witness_response_valid=False, witness_ack=False,
                    recovery_blocked=True, recovery_status=Recovery.RECONCILIATION_REQUIRED)
    if action == "witness_response":
        if s.witness_query is not WitnessQuery.REQUESTED or not s.witness_available:
            raise Reject("no available authenticated witness query request")
        kind = mode or "current"
        resp = (s.witness_sequence, s.witness_head)
        rrun, rop, rpolicy, rrev = s.run_id, s.operation_id, s.policy_epoch, s.revocation_epoch
        committed_op = s.witness_committed_op
        if kind == "next" and s.witness_next:
            resp, committed_op = s.witness_next, s.operation_id
        elif kind == "stale":
            resp = (max(0, s.witness_sequence - 1), "stale-head")
        elif kind == "wrong_op":
            rop = "foreign-operation"
        elif kind == "wrong_run":
            rrun = "foreign-run"
        elif kind == "wrong_policy":
            rpolicy += 1
        elif kind == "wrong_revocation":
            rrev += 1
        elif kind == "ahead":
            resp = (s.sequence + 1, "foreign-ahead")
        elif kind == "conflict":
            resp = (s.sequence, "foreign-same-sequence")
        elif kind not in {"current", "expected", "invalid_signature", "stale_freshness",
                          "next", "stale", "wrong_op", "wrong_run", "wrong_policy",
                          "wrong_revocation", "ahead", "conflict"}:
            raise Reject("unknown synthetic witness response")
        if kind == "expected" and s.witness_expected:
            resp, committed_op = s.witness_expected, None
        return step(s, action, witness_query=WitnessQuery.RECEIVED,
                    witness_response_run_id=rrun, witness_response_operation_id=rop,
                    witness_response_policy_epoch=rpolicy,
                    witness_response_revocation_epoch=rrev,
                    witness_response_sequence=resp[0], witness_response_head=resp[1],
                    witness_response_committed_op=committed_op,
                    witness_response_signer=("untrusted" if kind == "invalid_signature" else s.witness_identity),
                    witness_response_signature_valid=kind != "invalid_signature",
                    witness_response_fresh=kind != "stale_freshness",
                    witness_response_revocation_valid=kind != "wrong_revocation")
    if action == "witness_authenticate":
        if s.witness_query is not WitnessQuery.RECEIVED:
            raise Reject("witness response has not been received")
        if not s.witness_response_signature_valid or s.witness_response_signer != s.witness_identity:
            raise Reject("witness response signature/identity invalid")
        return step(s, action, witness_query=WitnessQuery.AUTHENTICATED)
    if action == "witness_verify":
        if s.witness_query is not WitnessQuery.AUTHENTICATED:
            raise Reject("witness response has not been authenticated")
        if not s.witness_response_fresh or not s.witness_response_revocation_valid:
            raise Reject("witness response stale or revocation status invalid")
        if (s.witness_response_run_id, s.witness_response_operation_id,
            s.witness_response_policy_epoch, s.witness_response_revocation_epoch) != (
            s.witness_query_run_id, s.witness_query_operation_id,
            s.witness_query_policy_epoch, s.witness_query_revocation_epoch
        ):
            raise Reject("witness response run/operation/policy/revocation binding mismatch")
        pair = (s.witness_response_sequence, s.witness_response_head)
        accepted_pairs = {(s.sequence, s.head)}
        if s.witness_expected:
            accepted_pairs.add(s.witness_expected)
        if s.witness_next:
            accepted_pairs.add(s.witness_next)
        if pair not in accepted_pairs:
            raise Reject("witness response is stale, rolled back or conflicting")
        if pair == s.witness_next and s.witness_next is not None:
            if s.witness_response_committed_op != s.operation_id:
                raise Reject("witness next head lacks exact Operation ID result")
        if pair == s.witness_expected and s.witness_response_committed_op not in (None, s.operation_id):
            raise Reject("witness predecessor reports conflicting operation result")
        verified = step(s, action, witness_query=WitnessQuery.VALIDATED,
                        witness_response_valid=True)
        return _bind_witness_evidence(verified)
    if action == "witness_reconcile":
        if s.witness_query is not WitnessQuery.VALIDATED or not s.witness_response_valid:
            raise Reject("reconciliation requires validated authenticated witness evidence")
        pair = (s.witness_response_sequence, s.witness_response_head)
        if pair == s.witness_next and s.witness_next is not None:
            if s.witness_response_committed_op != s.operation_id:
                raise Reject("remote commit not bound to same Operation ID")
            return step(s, action, witness_sequence=pair[0] or 0,
                        witness_head=pair[1] or "", witness_committed_op=s.operation_id,
                        witness_policy_epoch=s.policy_epoch,
                        witness_revocation_epoch=s.revocation_epoch,
                        witness_ack=True, witness=Witness.MATCH,
                        witness_query=WitnessQuery.RECONCILED,
                        recovery_blocked=False, recovery_status=Recovery.RECONCILED)
        if pair in {(s.sequence, s.head), s.witness_expected}:
            return step(s, action, witness_sequence=pair[0] or 0,
                        witness_head=pair[1] or "", witness_ack=False,
                        witness_policy_epoch=s.policy_epoch,
                        witness_revocation_epoch=s.revocation_epoch,
                        witness=Witness.MATCH, witness_query=WitnessQuery.RECONCILED,
                        recovery_blocked=False, recovery_status=Recovery.RECONCILED)
        raise Reject("validated witness result does not reconcile local state")
    if action == "witness_restore":
        return step(s, action, witness_available=True, witness_query=WitnessQuery.NONE,
                    witness_response_valid=False, recovery_blocked=True,
                    recovery_status=Recovery.RECONCILIATION_REQUIRED)
    if action == "witness_diverge":
        kind = op
        if kind == "unavailable":
            return step(s, action, witness_available=False, witness=Witness.UNAVAILABLE,
                        witness_ack=False, witness_query=WitnessQuery.UNAVAILABLE,
                        witness_response_valid=False, recovery_blocked=True,
                        recovery_status=Recovery.BLOCKED)
        if kind == "ahead":
            return step(s, action, witness_sequence=s.sequence + 1, witness_head="foreign-ahead",
                        witness=Witness.WITNESS_AHEAD, witness_ack=False,
                        witness_response_valid=False, recovery_blocked=True,
                        recovery_status=Recovery.BLOCKED)
        if kind == "same":
            return step(s, action, witness_sequence=s.sequence, witness_head="foreign-same",
                        witness=Witness.SAME_SEQUENCE_CONFLICT, witness_ack=False,
                        witness_response_valid=False, recovery_blocked=True,
                        recovery_status=Recovery.BLOCKED)
        if kind == "local":
            return step(s, action, witness_sequence=max(0, s.sequence - 1), witness_head="old",
                        witness=Witness.LOCAL_AHEAD, witness_ack=False,
                        witness_response_valid=False, recovery_blocked=True,
                        recovery_status=Recovery.BLOCKED)
        if kind == "epoch":
            return step(s, action, witness_policy_epoch=s.policy_epoch + 1,
                        witness_ack=False, witness_response_valid=False,
                        recovery_blocked=True, recovery_status=Recovery.BLOCKED)
        raise Reject("unknown witness divergence fixture")
    if action == "crash":
        uncertain = s.dispatch_marker_durable and not s.response_durable
        return step(s, action, infer=Infer.INTERRUPTED_UNKNOWN if uncertain else s.infer,
                    recovery_blocked=True, recovery_status=Recovery.RECONCILIATION_REQUIRED,
                    ack=False, witness_ack=False, witness_response_valid=False,
                    witness_query=WitnessQuery.NONE)
    if action == "barrier_failure":
        return step(s, action, recovery_blocked=True,
                    recovery_status=Recovery.RECONCILIATION_REQUIRED, ack=False)
    if action == "revoke":
        return step(s, action, revoked=True, lease_revoked=True,
                    revocation_epoch=s.revocation_epoch + 1,
                    policy_epoch=s.policy_epoch + 1, witness_ack=False,
                    recovery_blocked=True, recovery_status=Recovery.BLOCKED)
    if action == "quota":
        return step(s, action, quota=True, recovery_blocked=True,
                    recovery_status=Recovery.BLOCKED, ack=False)
    if action == "recover":
        if s.revoked or s.lease_revoked or s.quota or s.authority_state is not AuthorityState.ACTIVE:
            raise Reject("revoked, exhausted or unavailable authority requires governed recovery")
        if s.infer is Infer.INTERRUPTED_UNKNOWN:
            return step(s, action, recovery_blocked=True, recovery_status=Recovery.BLOCKED)
        if s.witness_required and (s.recovery_blocked or s.sequence > 0):
            if s.witness_query is not WitnessQuery.RECONCILED or not s.witness_response_valid:
                raise Reject("recovery requires fresh authenticated witness reconciliation")
        return step(s, action, recovery_blocked=False, recovery_status=Recovery.RECONCILED)
    if action == "ack":
        if not (s.infer is Infer.RESPONSE_COMMITTED and s.response_durable
                and s.object_durable and s.journal_durable and s.head_durable
                and s.publish_token_id is not None and not s.revoked
                and not s.lease_expired and not s.lease_revoked and not s.quota):
            raise Reject("response commit barriers or authority are incomplete")
        if s.witness_required and not (s.witness_ack and s.witness_query is WitnessQuery.RECONCILED
                                       and s.witness_response_valid):
            raise Reject("witness proof is not reconciled")
        return step(s, action, ack=True, response_confirmed=True)
    if action == "admin_record":
        if s.operation is not Operation.ADMINISTRATIVE or s.infer is not Infer.NONE or s.ack:
            raise Reject("administrative record cannot be treated as inference")
        return step(s, action)
    raise Reject(f"unknown action {action}")


def _dispatch(s: State) -> State:
    return apply(s, "authorize_dispatch", op=s.operation_id, run_id=s.run_id,
                 slot_id=s.slot_id, manifest_digest=s.manifest_digest,
                 config_digest=s.config_digest)


def _observe(s: State) -> State:
    return apply(s, "response_observed", response=b"synthetic generated continuation",
                 run_id=s.run_id, slot_id=s.slot_id, op=s.operation_id,
                 manifest_digest=s.manifest_digest, config_digest=s.config_digest)


def _prepare_response(witness_required: bool = True) -> State:
    s = State(witness_required=witness_required)
    for event, kw in (("prepare_intent", {}), ("durable_intent", {})):
        s = apply(s, event, **kw)
    s = _dispatch(s)
    for event, kw in (("mark_dispatch", {"op": s.operation_id}),
                      ("response_observed", {})):
        if event == "mark_dispatch":
            s = apply(s, event, **kw)
        else:
            s = _observe(s)
    for event in ("verify_response", "response_durable", "persist_object", "journal_durable"):
        s = apply(s, event)
    return s


def complete_history(witness_required: bool = True) -> tuple[State, ...]:
    s = State(witness_required=witness_required)
    out = [s]
    for event in ("prepare_intent", "durable_intent"):
        s = apply(s, event)
        out.append(s)
    s = _dispatch(s); out.append(s)
    s = apply(s, "mark_dispatch", op=s.operation_id); out.append(s)
    s = _observe(s); out.append(s)
    for event in ("verify_response", "response_durable", "persist_object", "journal_durable"):
        s = apply(s, event); out.append(s)
    s = apply(s, "prepare_publish", writer=s.holder, lease_id=s.lease_id,
              epoch=s.epoch, authority_id=s.authority_id); out.append(s)
    token = s.prepared_publications[-1].token_id
    s = apply(s, "publish", token_id=token); out.append(s)
    s = apply(s, "head_durable"); out.append(s)
    if witness_required:
        s = apply(s, "witness_prepare", op=s.operation_id); out.append(s)
        s = apply(s, "witness_advance"); out.append(s)
        s = apply(s, "witness_query"); out.append(s)
        s = apply(s, "witness_response", mode="next"); out.append(s)
        s = apply(s, "witness_authenticate"); out.append(s)
        s = apply(s, "witness_verify"); out.append(s)
        s = apply(s, "witness_reconcile"); out.append(s)
    s = apply(s, "ack"); out.append(s)
    return tuple(out)


def actions(s: State) -> tuple[tuple[str, dict[str, object]], ...]:
    result: list[tuple[str, dict[str, object]]] = [
        ("prepare_intent", {}), ("durable_intent", {}),
        ("authorize_dispatch", {"op": s.operation_id, "run_id": s.run_id,
         "slot_id": s.slot_id, "manifest_digest": s.manifest_digest,
         "config_digest": s.config_digest}),
        ("mark_dispatch", {"op": s.operation_id}),
        ("response_observed", {"response": b"synthetic generated continuation",
         "run_id": s.run_id, "slot_id": s.slot_id, "op": s.operation_id,
         "manifest_digest": s.manifest_digest, "config_digest": s.config_digest}),
        ("verify_response", {}), ("response_durable", {}), ("retry_inference", {}),
        ("persist_object", {}), ("persist_retry", {}), ("persist_conflicting_bytes", {}),
        ("persist_source", {}),
        ("journal_durable", {}), ("head_durable", {}),
        ("transfer", {"writer": s.holder, "lease_id": s.lease_id,
         "epoch": s.epoch, "authority_id": s.authority_id}),
        ("witness_prepare", {"op": s.operation_id}), ("witness_advance", {}),
        ("witness_timeout_before_commit", {}), ("witness_timeout_after_commit", {}),
        ("witness_query", {}), ("witness_restore", {}), ("witness_verify", {}),
        ("witness_authenticate", {}),
        ("witness_reconcile", {}), ("witness_response", {"mode": "current"}),
        ("witness_response", {"mode": "next"}), ("witness_response", {"mode": "expected"}),
        ("witness_response", {"mode": "stale"}), ("witness_response", {"mode": "wrong_op"}),
        ("witness_response", {"mode": "wrong_run"}), ("witness_response", {"mode": "wrong_policy"}),
        ("witness_response", {"mode": "wrong_revocation"}),
        ("witness_response", {"mode": "invalid_signature"}),
        ("witness_response", {"mode": "stale_freshness"}),
        ("witness_diverge", {"op": "ahead"}), ("witness_diverge", {"op": "same"}),
        ("witness_diverge", {"op": "local"}), ("witness_diverge", {"op": "unavailable"}),
        ("witness_diverge", {"op": "epoch"}),
        ("crash", {}), ("barrier_failure", {}), ("expire_lease", {}),
        ("authority_unavailable", {}),
        ("revoke", {}), ("quota", {}), ("recover", {}), ("ack", {}),
    ]
    if s.operation is Operation.ADMINISTRATIVE:
        result.append(("admin_record", {}))
    if s.object_durable and s.journal_durable and s.response_durable:
        for token in s.prepared_publications:
            result.append(("publish", {"token_id": token.token_id}))
        if s.authority_state is AuthorityState.ACTIVE:
            result.append(("prepare_publish", {"writer": s.holder, "lease_id": s.lease_id,
                "epoch": s.epoch, "authority_id": s.authority_id}))
    return tuple(result)


def explore(max_depth: int = 6, max_states: int = 100_000) -> dict[str, int]:
    initial = State()
    queue = deque([(initial, 0)])
    representatives = {initial: initial}
    accepted = rejected = deepest = aliases = 0
    frontier_mismatches = 0
    while queue:
        s, depth = queue.popleft()
        deepest = max(deepest, depth)
        validate(s)
        if s.ack:
            assert classify(s) is Outcome.COMMITTED
        if depth >= max_depth:
            continue
        for name, kw in actions(s):
            try:
                nxt = apply(s, name, **kw)
                validate(nxt)
            except Reject:
                rejected += 1
                continue
            accepted += 1
            previous = representatives.get(nxt)
            if previous is not None and previous.history != nxt.history:
                aliases += 1
                if _frontier(previous) != _frontier(nxt):
                    frontier_mismatches += 1
                    raise AssertionError("history-excluded states have different action frontiers")
            if nxt not in representatives:
                if len(representatives) >= max_states:
                    raise RuntimeError("exploration state bound exceeded")
                representatives[nxt] = nxt
                queue.append((nxt, depth + 1))
    return {"states": len(representatives), "accepted_transitions": accepted,
            "rejected_attempts": rejected, "max_depth": deepest,
            "history_aliases": aliases, "frontier_mismatches": frontier_mismatches}


def _frontier(s: State) -> frozenset[tuple[str, tuple[tuple[str, object], ...], bool]]:
    frontier = set()
    for name, kw in actions(s):
        try:
            apply(s, name, **kw)
            accepted = True
        except Reject:
            accepted = False
        frontier.add((name, tuple(sorted(kw.items())), accepted))
    return frozenset(frontier)


def self_check() -> None:
    assert classify(complete_history()[-1]) is Outcome.COMMITTED
    assert classify(complete_history(False)[-1]) is Outcome.COMMITTED
    assert classify_snapshot(intent=True, acknowledged=True, head_durable=True,
                             object_durable=False, journal_durable=False) is Outcome.REJECTED
    assert explore()["states"] > 1


if __name__ == "__main__":
    self_check()
    print(f"SRC02_ABSTRACT_SAFETY_PASS {explore(max_depth=6)}; no native I/O")
