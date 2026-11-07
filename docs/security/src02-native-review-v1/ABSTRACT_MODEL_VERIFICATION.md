# Abstract model verification

## Execution

Reviewed base model: `docs/security/src02-native-contract-v1/models/commit_state_model.py` at PR #33 HEAD. Executed with the existing Python environment; output:

```text
ABSTRACT_COMMIT_MODEL_PASS; no filesystem operations executed
```

This confirms only the model's own assertions. No native call, filesystem, process lease, witness service, inference or metric estimation was performed.

## Adversarial counterexample

The self-check does not test the necessary preconditions for `COMMITTED`. Reproduction through the model API:

```python
Snapshot(intent=True, acknowledged=True, head_durable=True,
         object_durable=False, journal_durable=False)
```

Observed output: `COMMITTED` with `witness_required=False`. With `witness_required=True`, set `witness_advanced=True` and it still returns `COMMITTED` with object and journal durability false. This violates the model's stated commit rule and is tracked as SRC2-REV-01 (HIGH).

The model also has no representation of: two writers; lease transfer/stale fencing epoch; expected/current sequence; witness unavailable/ahead/behind/equivocating; root revocation; quota failure; or durable inference dispatch transition. Therefore “model PASS” is not evidence for those properties. Extend the abstract model only after the state schema is corrected; each safety property needs an assertion over all reachable states, not only one happy path.

## Required safety properties

1. `COMMITTED ⇒ object_durable ∧ journal_durable ∧ head_durable ∧ witness_policy_satisfied ∧ legal_transition_order`.
2. One operation ID maps to one exact intent/result; different bytes collide.
3. No stale fencing epoch can publish a head.
4. If inference may have started and exact response is absent, status is `interrupted_unknown` and no transition invokes inference again.
5. Witness conflict/unavailability blocks automatic resume.
6. Illegal, non-monotonic or impossible state snapshots are rejected, never normalized.

## Classification

Model status: **FAIL as a safety checker** until SRC2-REV-01 is corrected and adversarial interleavings are represented. The pure model did not modify scientific data or imply an implementation-level vulnerability.
