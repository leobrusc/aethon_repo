# SRC-02 Finding Validation Matrix

| Finding | Classification | Evidence in current abstract model | Contract result | Native status |
|---|---|---|---|---|
| SRC2-REV-01 | `OPEN` | New trace commits after durable intent/object/journal/head/witness/ack without dispatch or observed response. | Legal-history / response provenance invariant is not enforced. | NOT_VALIDATED |
| SRC2-REV-02 | `PARTIAL` | Epoch-7 writer is rejected after epoch 8 transfer; check and publish are atomic in one abstract transition. | Lease ID and explicit authoritative serialization state are absent from `State`. | NOT_VALIDATED |
| SRC2-REV-03 | `OPEN` | Dispatch-uncertain recovery blocks inference retry, but a pre-dispatch no-response operation can still commit. | Must bind committed response to observed and durably persisted response; an intent is not a result. | NOT_VALIDATED |
| SRC2-REV-04 | `OPEN` | Witness unavailable followed by query can report `RECONCILED` and clear block without witness availability. | Must retain block until an authenticated witness read/reconciliation succeeds. | NOT_VALIDATED |
| SRC2-REV-05 | `PARTIAL` | Requirements are documented; no executable root receipt, trust-anchor verification, restart revocation, or revocation-during-commit proof. | Specification only. | NOT_VALIDATED |
| SRC2-REV-06 | `PARTIAL` | Windows candidate profile is bounded; no native conformance evidence. | Specification only. | NOT_VALIDATED |

## Historical counterexamples

The original PR #34 false-commit snapshot is rejected by the existing model test. The stale writer A(epoch 7)/B(epoch 8) example is rejected. These successful regressions do not close the newly demonstrated traces. Original historical reproduction files were not modified.

## Required closure evidence

- REV-01/03: counterexample tests must reject every commit lacking a dispatched, observed response and a response object durably bound to the run, operation, and manifest.
- REV-04: unavailable, timed-out, stale, or divergent witness reads must not transition to reconciled; same-operation retry must query its outcome before another advance.
- REV-02: model lease ID, holder, epoch, expected head and authoritative serialization, with stale lease rejected at the same abstract atomic publication point.
- REV-05/06: retain NOT_VALIDATED until platform-specific implementation and native evidence exist.

No finding status implies authorization to implement or operate SRC-02.
