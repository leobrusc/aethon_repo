"""Bounded abstract SRC-02 state machine; standard library only, no native I/O."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field, replace
from enum import Enum


class Outcome(str, Enum):
    NOT_COMMITTED = "NOT_COMMITTED"
    COMMIT_UNKNOWN = "COMMIT_UNKNOWN"
    COMMITTED = "COMMITTED"
    REJECTED = "REJECTED"


class Infer(str, Enum):
    NONE = "NONE"
    INTENT_PREPARED = "INTENT_PREPARED"
    INTENT_DURABLE = "INTENT_DURABLE"
    DISPATCH_MAY_HAVE_STARTED = "DISPATCH_MAY_HAVE_STARTED"
    RESPONSE_OBSERVED = "RESPONSE_OBSERVED"
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


class Recovery(str, Enum):
    CLEAN = "CLEAN"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    RECONCILED = "RECONCILED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class State:
    run_id: str = "run-fixture"
    bound_run_id: str = "run-fixture"
    operation_id: str = "op-fixture"
    bound_operation_id: str = "op-fixture"
    manifest_digest: str = "manifest-fixture"
    bound_manifest_digest: str = "manifest-fixture"
    response_digest: str = "response-fixture"
    bound_response_digest: str = "response-fixture"
    infer: Infer = Infer.NONE
    intent_durable: bool = False
    dispatch_marker_durable: bool = False
    response_durable: bool = False
    object_durable: bool = False
    journal_durable: bool = False
    sequence: int = 0
    head: str = "h0"
    head_durable: bool = True
    expected_sequence: int = 0
    expected_head: str = "h0"
    epoch: int = 7
    holder: str = "A"
    epoch_a: int = 7
    epoch_b: int = 0
    publish_epoch: int | None = None
    publish_writer: str | None = None
    witness_required: bool = True
    policy_epoch: int = 1
    witness: Witness = Witness.MATCH
    witness_available: bool = True
    witness_policy_epoch: int = 1
    witness_sequence: int = 0
    witness_head: str = "h0"
    witness_op: str | None = None
    witness_expected: tuple[int, str] | None = None
    witness_next: tuple[int, str] | None = None
    witness_committed_op: str | None = None
    witness_ack: bool = False
    ack: bool = False
    revoked: bool = False
    quota: bool = False
    recovery_blocked: bool = False
    recovery_status: Recovery = Recovery.CLEAN
    persisted: tuple[tuple[str, str], ...] = ()
    history: tuple[str, ...] = field(default=(), compare=False, hash=False)


class Reject(ValueError):
    pass


def step(s: State, name: str, **changes: object) -> State:
    return replace(s, **changes, history=s.history + (name,))


def validate(s: State) -> None:
    if not all((s.run_id, s.operation_id, s.manifest_digest, s.response_digest)):
        raise Reject("missing immutable binding")
    if (s.run_id, s.operation_id, s.manifest_digest, s.response_digest) != (
        s.bound_run_id, s.bound_operation_id, s.bound_manifest_digest, s.bound_response_digest
    ):
        raise Reject("run/operation/digest binding changed")
    ordered = ("prepare_intent", "durable_intent", "mark_dispatch", "response_observed",
               "response_durable", "persist_object", "journal_durable", "publish", "head_durable")
    positions = [s.history.index(name) for name in ordered if name in s.history]
    if positions != sorted(positions) or s.history.count("publish") > 1:
        raise Reject("transaction history violates legal ordering")
    if (s.infer is Infer.NONE) != ("prepare_intent" not in s.history):
        raise Reject("inference state and intent history disagree")
    if s.intent_durable != ("durable_intent" in s.history):
        raise Reject("intent durability and history disagree")
    if s.dispatch_marker_durable != ("mark_dispatch" in s.history):
        raise Reject("dispatch marker and history disagree")
    if s.response_durable != ("response_durable" in s.history):
        raise Reject("response durability and history disagree")
    object_event = "persist_object" in s.history or "persist_retry" in s.history
    if s.object_durable != object_event:
        raise Reject("object durability and history disagree")
    if s.object_durable and (s.operation_id, s.response_digest) not in s.persisted:
        raise Reject("durable object lacks exact operation/digest record")
    if s.journal_durable != ("journal_durable" in s.history):
        raise Reject("journal durability and history disagree")
    if min(s.sequence, s.expected_sequence, s.witness_sequence) < 0:
        raise Reject("negative sequence")
    if s.expected_sequence > s.sequence:
        raise Reject("expected head ahead of local head")
    if s.sequence > 0 and s.head_durable and not (s.object_durable and s.journal_durable):
        raise Reject("head durable without object and journal")
    if s.sequence != s.history.count("publish"):
        raise Reject("head sequence does not match legal publication history")
    if s.sequence == 0 and (s.head != "h0" or s.publish_epoch is not None):
        raise Reject("non-initial head without publication")
    if s.sequence == 1 and s.head != f"h1:{s.response_digest}":
        raise Reject("head does not bind the response digest")
    if s.sequence and s.head_durable and "head_durable" not in s.history:
        raise Reject("head durability absent from history")
    if s.sequence and not (s.object_durable and s.journal_durable):
        raise Reject("published head lacks durable object/journal")
    if s.dispatch_marker_durable and not s.intent_durable:
        raise Reject("dispatch before durable intent")
    if s.infer in {Infer.DISPATCH_MAY_HAVE_STARTED, Infer.RESPONSE_OBSERVED,
                   Infer.RESPONSE_DURABLE, Infer.RESPONSE_COMMITTED,
                   Infer.INTERRUPTED_UNKNOWN} and not s.dispatch_marker_durable:
        raise Reject("inference state without durable may-dispatch marker")
    if s.infer is Infer.INTERRUPTED_UNKNOWN and not any(
        x in s.history for x in ("crash", "recover")
    ):
        raise Reject("unknown inference has no interruption history")
    if s.response_durable and s.infer not in {Infer.RESPONSE_DURABLE, Infer.RESPONSE_COMMITTED}:
        raise Reject("response durability/state mismatch")
    if s.ack:
        if not s.history or s.history[-1] != "ack":
            raise Reject("ack not reached through legal transition")
        if not (s.object_durable and s.journal_durable and s.head_durable):
            raise Reject("ack before local durability barriers")
        if (s.publish_epoch, s.publish_writer) != (s.epoch, s.holder):
            raise Reject("ack from stale writer")
        if s.revoked or s.recovery_blocked:
            raise Reject("ack after revocation or unresolved recovery")
        if s.witness_required:
            if not s.witness_ack or s.witness is not Witness.MATCH:
                raise Reject("required witness not acknowledged")
            if s.witness_policy_epoch != s.policy_epoch:
                raise Reject("witness policy epoch differs")
            if (s.witness_sequence, s.witness_head) != (s.sequence, s.head):
                raise Reject("witness/head mismatch at ack")
    if s.witness_ack and s.witness_committed_op != s.operation_id:
        raise Reject("witness ack is not operation-bound")
    if s.witness_ack and not any(x in s.history for x in ("witness_advance", "witness_query")):
        raise Reject("witness ack absent from legal history")
    if s.witness_expected and s.witness_next and s.witness_next[0] != s.witness_expected[0] + 1:
        raise Reject("witness sequence gap")
    if s.revoked and "revoke" not in s.history:
        raise Reject("revocation absent from history")
    if s.quota and "quota" not in s.history:
        raise Reject("quota exhaustion absent from history")
    if s.recovery_blocked and not any(x in s.history for x in (
        "crash", "barrier_failure", "witness_unavailable", "witness_timeout_after_commit",
        "witness_timeout_before_commit", "witness_diverge", "recover", "revoke", "quota"
    )):
        raise Reject("recovery block has no triggering event")
    if s.recovery_blocked and s.recovery_status not in {
        Recovery.RECONCILIATION_REQUIRED, Recovery.BLOCKED
    }:
        raise Reject("recovery flag/status disagree")
    if not s.recovery_blocked and s.recovery_status in {
        Recovery.RECONCILIATION_REQUIRED, Recovery.BLOCKED
    }:
        raise Reject("recovery status requires a blocked state")


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
          epoch: int | None = None, op: str | None = None) -> State:
    validate(s)
    if s.ack:
        raise Reject("committed transaction is terminal")
    if s.recovery_blocked and action not in {
        "recover", "witness_query", "witness_advance", "crash", "revoke"
    }:
        raise Reject("recovery is required before further state changes")
    if action == "prepare_intent":
        if s.infer is not Infer.NONE or s.revoked or s.quota:
            raise Reject("intent not permitted")
        return step(s, action, infer=Infer.INTENT_PREPARED)
    if action == "durable_intent":
        if s.infer is not Infer.INTENT_PREPARED or s.revoked or s.quota:
            raise Reject("intent not prepared")
        return step(s, action, infer=Infer.INTENT_DURABLE, intent_durable=True)
    if action == "mark_dispatch":
        if (s.infer is not Infer.INTENT_DURABLE or not s.intent_durable
                or s.object_durable or op != s.operation_id or s.revoked or s.quota):
            raise Reject("dispatch requires durable bound intent")
        return step(s, action, infer=Infer.DISPATCH_MAY_HAVE_STARTED, dispatch_marker_durable=True)
    if action == "response_observed":
        if s.infer is not Infer.DISPATCH_MAY_HAVE_STARTED:
            raise Reject("dispatch marker absent")
        return step(s, action, infer=Infer.RESPONSE_OBSERVED)
    if action == "response_durable":
        if s.infer is not Infer.RESPONSE_OBSERVED or s.quota:
            raise Reject("no response to persist")
        return step(s, action, infer=Infer.RESPONSE_DURABLE, response_durable=True)
    if action == "retry_inference":
        if s.infer is not Infer.INTENT_DURABLE or s.dispatch_marker_durable or s.revoked or s.quota:
            raise Reject("possibly dispatched inference cannot be retried")
        return step(s, action)
    if action == "persist_object":
        safe_source = s.infer is Infer.RESPONSE_DURABLE or (
            s.infer is Infer.INTENT_DURABLE and not s.dispatch_marker_durable)
        if not safe_source or s.revoked or s.quota:
            raise Reject("no known durable source")
        key = (s.operation_id, s.response_digest)
        if s.persisted and key not in s.persisted:
            raise Reject("operation ID collision")
        return step(s, action, object_durable=True, persisted=(key,))
    if action == "persist_retry":
        key = (s.operation_id, s.response_digest)
        if key not in s.persisted or s.revoked or s.quota:
            raise Reject("retry is not exact idempotent persistence")
        return step(s, action, object_durable=True)
    if action == "persist_conflicting_bytes":
        raise Reject("same Operation ID with different bytes")
    if action == "journal_durable":
        if not s.object_durable or s.journal_durable or s.revoked or s.quota:
            raise Reject("journal requires durable object")
        return step(s, action, journal_durable=True)
    if action == "publish":
        holder_epoch = s.epoch_a if writer == "A" else s.epoch_b
        # Lease epoch and expected head are checked atomically with publication.
        if writer != s.holder or epoch != s.epoch or holder_epoch != s.epoch:
            raise Reject("stale fencing epoch")
        if s.revoked or s.quota or s.recovery_blocked:
            raise Reject("authority/resources/recovery block publication")
        if not (s.object_durable and s.journal_durable):
            raise Reject("object/journal barriers missing")
        if (s.sequence, s.head) != (s.expected_sequence, s.expected_head):
            raise Reject("head CAS conflict")
        if s.infer in {Infer.DISPATCH_MAY_HAVE_STARTED, Infer.RESPONSE_OBSERVED,
                       Infer.INTERRUPTED_UNKNOWN}:
            raise Reject("uncertain response cannot be published")
        return step(s, action, sequence=s.sequence + 1,
                    head=f"h{s.sequence + 1}:{s.response_digest}", head_durable=False,
                    publish_epoch=epoch, publish_writer=writer,
                    witness=Witness.LOCAL_AHEAD if s.witness_required else s.witness,
                    infer=Infer.RESPONSE_COMMITTED if s.infer is Infer.RESPONSE_DURABLE else s.infer)
    if action == "head_durable":
        if s.sequence == 0 or s.head_durable or not (s.object_durable and s.journal_durable):
            raise Reject("head barrier out of order")
        if (s.publish_epoch, s.publish_writer) != (s.epoch, s.holder) or s.revoked:
            raise Reject("fence changed or revoked before head barrier")
        return step(s, action, head_durable=True)
    if action == "transfer":
        if writer != s.holder or epoch != s.epoch or s.revoked:
            raise Reject("only current holder transfers lease")
        new_holder, new_epoch = ("B" if writer == "A" else "A"), s.epoch + 1
        return step(s, action, holder=new_holder, epoch=new_epoch,
                    **({"epoch_b": new_epoch} if new_holder == "B" else {"epoch_a": new_epoch}))
    if action == "witness_prepare":
        if not s.witness_required or not s.head_durable or not s.witness_available or s.revoked:
            raise Reject("witness unavailable")
        if s.witness_policy_epoch != s.policy_epoch:
            raise Reject("witness policy epoch differs")
        expected, nxt = (s.witness_sequence, s.witness_head), (s.sequence, s.head)
        if s.witness_op:
            if (s.witness_op, s.witness_expected, s.witness_next) == (op or s.operation_id, expected, nxt):
                return s
            raise Reject("conflicting witness operation")
        if expected != (s.expected_sequence, s.expected_head) or nxt[0] != expected[0] + 1:
            raise Reject("witness CAS precondition/sequence conflict")
        return step(s, action, witness_op=op or s.operation_id, witness_expected=expected,
                    witness_next=nxt, witness=Witness.PENDING)
    if action == "witness_advance":
        if not s.witness_available or not s.witness_op or not s.witness_next:
            raise Reject("no witness request")
        if s.witness_committed_op == s.witness_op:
            if s.witness_policy_epoch != s.policy_epoch:
                raise Reject("committed witness epoch differs")
            return step(s, action, witness_ack=True, witness=Witness.MATCH)
        if (s.witness_sequence, s.witness_head) != s.witness_expected or s.witness_op != s.operation_id:
            raise Reject("witness CAS mismatch")
        seq, head = s.witness_next
        return step(s, action, witness_sequence=seq, witness_head=head,
                    witness_policy_epoch=s.policy_epoch, witness_committed_op=s.witness_op,
                    witness_ack=True, witness=Witness.MATCH)
    if action == "witness_timeout_before_commit":
        if not s.witness_op or s.witness_committed_op == s.witness_op:
            raise Reject("no uncommitted witness request to time out")
        return step(s, action, witness_ack=False, witness=Witness.PENDING,
                    recovery_blocked=True, recovery_status=Recovery.RECONCILIATION_REQUIRED)
    if action == "witness_timeout_after_commit":
        if s.witness_committed_op != s.witness_op:
            raise Reject("remote operation not committed")
        return step(s, action, witness_ack=False, witness=Witness.PENDING, recovery_blocked=True,
                    recovery_status=Recovery.RECONCILIATION_REQUIRED)
    if action == "witness_query":
        if not s.witness_op:
            raise Reject("no idempotency key")
        if (s.witness_committed_op == s.witness_op
                and s.witness_next == (s.witness_sequence, s.witness_head)
                and s.witness_policy_epoch == s.policy_epoch):
            return step(s, action, witness_ack=True, witness=Witness.MATCH,
                        recovery_blocked=False, recovery_status=Recovery.RECONCILED)
        if (s.witness_sequence, s.witness_head) == s.witness_expected:
            return step(s, action, witness_ack=False, witness=Witness.PENDING,
                        recovery_blocked=False, recovery_status=Recovery.RECONCILED)
        raise Reject("witness conflict")
    if action == "witness_diverge":
        kind = op
        if kind == "unavailable":
            return step(s, action, witness_available=False, witness=Witness.UNAVAILABLE,
                        witness_ack=False, recovery_blocked=True,
                        recovery_status=Recovery.BLOCKED)
        if kind == "ahead":
            return step(s, action, witness_sequence=s.sequence + 1, witness_head="foreign",
                        witness=Witness.WITNESS_AHEAD, witness_ack=False, recovery_blocked=True,
                        recovery_status=Recovery.BLOCKED)
        if kind == "same":
            return step(s, action, witness_sequence=s.sequence, witness_head="foreign-same",
                        witness=Witness.SAME_SEQUENCE_CONFLICT, witness_ack=False, recovery_blocked=True,
                        recovery_status=Recovery.BLOCKED)
        if kind == "local":
            return step(s, action, witness_sequence=max(0, s.sequence - 1), witness_head="old",
                        witness=Witness.LOCAL_AHEAD, witness_ack=False, recovery_blocked=True,
                        recovery_status=Recovery.BLOCKED)
        if kind == "epoch":
            return step(s, action, witness_policy_epoch=s.policy_epoch + 1,
                        witness_ack=False, recovery_blocked=True,
                        recovery_status=Recovery.BLOCKED)
        raise Reject("unknown divergence fixture")
    if action == "crash":
        uncertain = s.infer in {Infer.DISPATCH_MAY_HAVE_STARTED, Infer.RESPONSE_OBSERVED}
        return step(s, action, infer=Infer.INTERRUPTED_UNKNOWN if uncertain else s.infer,
                    recovery_blocked=True, recovery_status=Recovery.RECONCILIATION_REQUIRED,
                    ack=False)
    if action == "barrier_failure":
        return step(s, action, recovery_blocked=True,
                    recovery_status=Recovery.RECONCILIATION_REQUIRED, ack=False)
    if action == "revoke":
        return step(s, action, revoked=True, policy_epoch=s.policy_epoch + 1,
                    recovery_blocked=True, recovery_status=Recovery.BLOCKED, ack=False)
    if action == "quota":
        return step(s, action, quota=True, recovery_blocked=True,
                    recovery_status=Recovery.RECONCILIATION_REQUIRED, ack=False)
    if action == "recover":
        if not s.witness_available and s.witness_required:
            raise Reject("witness unavailable")
        if (s.witness in {Witness.WITNESS_AHEAD, Witness.SAME_SEQUENCE_CONFLICT, Witness.LOCAL_AHEAD}
                or (s.witness_required and s.witness_policy_epoch != s.policy_epoch)):
            raise Reject("divergence requires governed recovery")
        if s.infer in {Infer.DISPATCH_MAY_HAVE_STARTED, Infer.RESPONSE_OBSERVED, Infer.INTERRUPTED_UNKNOWN}:
            return step(s, action, infer=Infer.INTERRUPTED_UNKNOWN, recovery_blocked=True,
                        recovery_status=Recovery.BLOCKED)
        if s.witness_required and (s.witness_sequence, s.witness_head) != (s.sequence, s.head):
            if (s.witness_op == s.operation_id
                    and s.witness_next == (s.sequence, s.head)):
                reconciled = apply(s, "witness_advance", op=s.operation_id)
                return step(reconciled, action, recovery_blocked=False,
                            recovery_status=Recovery.RECONCILED)
            raise Reject("local/witness mismatch without same-operation evidence")
        return step(s, action, recovery_blocked=False, recovery_status=Recovery.RECONCILED)
    if action == "ack":
        nxt = step(s, action, ack=True)
        validate(nxt)
        return nxt
    raise Reject(f"unknown action {action}")


def complete_history(witness_required: bool = True) -> tuple[State, ...]:
    s = State(witness_required=witness_required)
    actions = [("prepare_intent", {}), ("durable_intent", {}),
               ("mark_dispatch", {"op": s.operation_id}), ("response_observed", {}),
               ("response_durable", {}), ("persist_object", {}), ("journal_durable", {}),
               ("publish", {"writer": "A", "epoch": 7}), ("head_durable", {})]
    if witness_required:
        actions += [("witness_prepare", {"op": s.operation_id}), ("witness_advance", {})]
    actions.append(("ack", {}))
    out = [s]
    for name, kw in actions:
        s = apply(s, name, **kw)
        out.append(s)
    return tuple(out)


def actions(s: State) -> tuple[tuple[str, dict[str, object]], ...]:
    return (("prepare_intent", {}), ("durable_intent", {}),
            ("mark_dispatch", {"op": s.operation_id}), ("response_observed", {}),
            ("response_durable", {}), ("retry_inference", {}),
            ("persist_object", {}), ("persist_retry", {}), ("persist_conflicting_bytes", {}),
            ("journal_durable", {}), ("publish", {"writer": "A", "epoch": 7}),
            ("publish", {"writer": "A", "epoch": s.epoch}),
            ("publish", {"writer": "B", "epoch": 8}),
            ("publish", {"writer": "B", "epoch": s.epoch}), ("head_durable", {}),
            ("transfer", {"writer": s.holder, "epoch": s.epoch}),
            ("witness_prepare", {"op": s.operation_id}), ("witness_advance", {}),
            ("witness_timeout_before_commit", {}), ("witness_timeout_after_commit", {}),
            ("witness_query", {}),
            ("witness_diverge", {"op": "ahead"}), ("witness_diverge", {"op": "same"}),
            ("witness_diverge", {"op": "local"}), ("witness_diverge", {"op": "unavailable"}),
            ("witness_diverge", {"op": "epoch"}),
            ("crash", {}), ("barrier_failure", {}), ("revoke", {}),
            ("quota", {}), ("recover", {}), ("ack", {}))


def explore(max_depth: int = 12, max_states: int = 100_000) -> dict[str, int]:
    q = deque([(State(), 0)])
    seen = {State()}
    accepted = rejected = deepest = 0
    while q:
        s, depth = q.popleft()
        deepest = max(deepest, depth)
        validate(s)
        if s.ack:
            assert classify(s) is Outcome.COMMITTED
        if depth >= max_depth:
            continue
        for name, kw in actions(s):
            try:
                nxt = apply(s, name, **kw)
            except Reject:
                rejected += 1
                continue
            accepted += 1
            validate(nxt)
            if nxt not in seen:
                if len(seen) >= max_states:
                    raise RuntimeError("exploration state bound exceeded")
                seen.add(nxt)
                q.append((nxt, depth + 1))
    return {"states": len(seen), "accepted_transitions": accepted,
            "rejected_attempts": rejected, "max_depth": deepest}


def self_check() -> None:
    assert classify(complete_history()[-1]) is Outcome.COMMITTED
    assert classify(complete_history(False)[-1]) is Outcome.COMMITTED
    original = dict(intent=True, acknowledged=True, head_durable=True,
                    object_durable=False, journal_durable=False)
    assert classify_snapshot(**original) is Outcome.REJECTED
    assert explore()["states"] > 1


if __name__ == "__main__":
    self_check()
    print(f"SRC02_ABSTRACT_SAFETY_PASS {explore()}; no native I/O")
