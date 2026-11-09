# Bounded State Exploration

## Current run

Command: `python -B -m pytest -q -s -p no:cacheprovider tests/test_src02_safety_model.py::test_explorer_recounts_bounded_states_and_alias_frontiers`

The current bounded exploration used a maximum transition depth of 6 and a hard unique-state limit of 100,000. It completed without reaching the cap:

| Measure | Result |
|---|---:|
| Unique quotient states | 11,898 |
| Accepted transitions | 27,902 |
| Rejected action attempts | 177,911 |
| Maximum reached depth | 6 |
| History aliases encountered | 15,345 |
| Action-frontier mismatches | 0 |

Every accepted successor is validated before deduplication. For each reachable equal-state alias with a different history, the model compares the representative and alias action acceptance frontier; none differed. The historical test file retains the previous PR #36 depth-12 counts, but those counts do not describe this changed relation and are not reused here.

## Bounds and abstraction

One run, one inference slot, one Operation ID, one response, one head advance, two logical writers and a finite witness-response menu are modeled. Depth 6 is not complete for longer histories. The witness “signature valid” and freshness checks are abstract trusted outcomes, not cryptographic verification. State exploration is not a proof of unbounded safety, liveness, filesystem behavior, cross-process concurrency, or service correctness.

Future relation changes must rerun the alias-frontier check and report new counts, bounds and any rejected counterexample traces. Do not compare these counts directly with PR #35/#36 because the state schema and transition relation changed.
