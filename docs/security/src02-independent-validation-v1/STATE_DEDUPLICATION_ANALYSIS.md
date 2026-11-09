# State Deduplication Analysis

## Question

The model's `State.history` has `compare=False, hash=False`, but `validate()` reads it. Can two equal states have different valid futures?

## Reproduction and bounded check

`tests/test_src02_dedup_audit.py` constructs distinct histories with identical compared fields and confirms the equality alias. It also creates an invalid history variant equal to a valid state; direct validation rejects that invalid variant. Because `explore()` validates successors before inserting them into `seen`, that malformed variant is not admitted by the current explorer.

An independent bounded traversal to depth 12 enumerated 16,642 quotient states and examined 15,941 reachable history aliases against each representative. All aliases had the same accepted-action frontier; no frontier mismatch was found. The recorded result is:

```text
quotient_states=16642
reachable_history_aliases=15941
depth_bound=12
frontier_mismatches=0
```

The audit test additionally records two security counterexamples in current model behavior: a pre-dispatch commit with no response is accepted, and an unavailable witness query can clear the recovery block. These are transition/validation defects, not deduplication mismatches.

## Conclusion and limit

Deduplication is safe for the explorer's currently reachable, validated histories within the stated depth and transition relation. This is not a proof for arbitrary states, unbounded histories, or future transitions. Equality aliases exist, so correctness depends on validate-before-seen and on not seeding the explorer with untrusted snapshots.

## Minimal hardening

Before expanding the model, either include a bounded canonical summary of all history facts used by `validate()` in the deduplication key, or require full transition replay and validation for every externally seeded state. Do not retain an unbounded trace solely to prevent state-space growth. Add the alias-frontier property test to the routine model suite, and rerun the bounded exploration whenever relevant transitions change.

## Evidence

The audit test source is `tests/test_src02_dedup_audit.py`. It is synthetic and does not create filesystem state, run inference, or estimate scientific efficacy. The test names and assertions intentionally preserve demonstrated insecure outcomes as findings; they are not security acceptance tests.
