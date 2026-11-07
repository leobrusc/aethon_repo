"""Abstract SRC-02 commit model. No filesystem calls or native primitives."""

from dataclasses import dataclass
from enum import Enum


class Outcome(str, Enum):
    NOT_COMMITTED = "NOT_COMMITTED"
    COMMIT_UNKNOWN = "COMMIT_UNKNOWN"
    COMMITTED = "COMMITTED"


@dataclass(frozen=True)
class Snapshot:
    intent: bool = False
    inference_may_have_started: bool = False
    object_durable: bool = False
    journal_durable: bool = False
    head_durable: bool = False
    witness_advanced: bool = False
    acknowledged: bool = False


def classify(s: Snapshot, *, witness_required: bool = True) -> Outcome:
    """Classify only from modeled evidence; never infer commit from object bytes."""
    if s.acknowledged and s.head_durable and (s.witness_advanced or not witness_required):
        return Outcome.COMMITTED
    if not s.intent and not s.inference_may_have_started:
        return Outcome.NOT_COMMITTED
    if s.intent and not s.inference_may_have_started and not s.object_durable:
        # Retry is allowed only for persistence with the same operation ID; the
        # caller must separately prove the external effect never began.
        return Outcome.NOT_COMMITTED
    return Outcome.COMMIT_UNKNOWN


def simulate(cut_after: str | None, *, witness_required: bool = True) -> tuple[Outcome, Snapshot]:
    """Crash after named barrier; barriers are abstract durable observations."""
    s = Snapshot()
    steps = (
        ("intent", {"intent": True}),
        ("inference_started", {"inference_may_have_started": True}),
        ("object", {"object_durable": True}),
        ("journal", {"journal_durable": True}),
        ("head", {"head_durable": True}),
        ("witness", {"witness_advanced": True}),
        ("ack", {"acknowledged": True}),
    )
    for name, update in steps:
        s = Snapshot(**(s.__dict__ | update))
        if name == cut_after:
            break
    return classify(s, witness_required=witness_required), s


def self_check() -> None:
    assert simulate(None)[0] is Outcome.COMMITTED
    assert simulate("intent")[0] is Outcome.NOT_COMMITTED
    assert simulate("inference_started")[0] is Outcome.COMMIT_UNKNOWN
    assert simulate("object")[0] is Outcome.COMMIT_UNKNOWN
    assert simulate("journal")[0] is Outcome.COMMIT_UNKNOWN
    assert simulate("head")[0] is Outcome.COMMIT_UNKNOWN
    assert simulate("witness")[0] is Outcome.COMMIT_UNKNOWN
    assert simulate("ack")[0] is Outcome.COMMITTED
    assert simulate("ack", witness_required=False)[0] is Outcome.COMMITTED
    assert simulate("head", witness_required=False)[0] is Outcome.COMMIT_UNKNOWN


if __name__ == "__main__":
    self_check()
    print("ABSTRACT_COMMIT_MODEL_PASS; no filesystem operations executed")
