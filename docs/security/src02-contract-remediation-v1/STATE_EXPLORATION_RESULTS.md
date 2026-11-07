# Finite state exploration results

## Reproducibility

Command: `python -B docs/security/src02-contract-remediation-v1/models/safety_model.py`
Runtime: Python 3.10.11 already available; standard library only. No filesystem
backend, native I/O, network, inference or service was invoked by the model.

Exploration: breadth-first over two logical writers (A/B), one run and one
Operation ID, one expected head advance, required-witness and no-witness policy
branches, with the action relation listed in `models/safety_model.py`.

| Bound/result | Value |
|---|---:|
| Maximum transition depth | 12 |
| Maximum allowed unique states | 100,000 |
| Unique reachable states | 16,642 |
| Accepted transitions examined | 32,651 |
| Rejected action attempts | 339,477 |
| State bound exceeded | No |
| Safety assertion failures | 0 |

The counts are from the final successful run. The explorer validates every
reachable successor and asserts that every acknowledged state classifies as
`COMMITTED`. Rejected transitions include impossible barriers, duplicate
conflicting operations, stale epochs, witness conflicts, post-crash writes,
revoked authority and invalid retries. Tests additionally cover legal histories
with and without required witness, crash cuts, stale writer transfer, timeout
query, idempotent persistence, digest alteration, sequence gap and quota/revocation.

## Historical reproduction

PR #34's original model source working-tree SHA-256:
`c4dd46acb740dd2cf8960857b788507291908fe673d574f769757b2e7c1ecae2`;
Git blob `04490105d90603f131f8baf3663eaaf59cb6e021`. The false-commit case and
its result are preserved in the immutable PR #34 review. The corrected model
returns `REJECTED` for that legacy snapshot under both witness profiles.
The active synthetic contract suite contains 24 passing cases, including
before/after witness timeouts, same-operation query/retry, policy-epoch
divergence and pre-dispatch versus post-dispatch crash behavior.

## Limits

This is finite bounded exploration, not an unbounded proof or native test. It
models no filesystem reordering, actual OS lock semantics, power-loss behavior,
network partitions, multiple runs, multiple sequential committed operations,
cryptographic identity, or a malicious kernel/host. Liveness is not established;
blocking on unavailable witness, conflicts or uncertain inference is intentional.
The next step is independent review of this transition relation, then a separately
authorized platform prototype only after remaining implementation gates close.
