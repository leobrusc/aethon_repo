# Independent SRC-02 Safety Model Review

## Scope and identity

Reviewed PR #35 at `f49f1ce6481719fc6696a08769cbb7cfde46dfb9`, based on PR #34 `c5567fd947f9a776da98cbf0b3ac98e93bac51e7`. The implementation commit identified by the user is `e1821ce83b714cde52ea917f48e7fd1453fc95e5`. This review examines the finite abstract model and its tests; it does not validate a native filesystem backend.

The review worktree is `review/src02-safety-and-integrity-v1`. No baseline, dataset, lock, or historical result was edited. The five pre-existing files in the original checkout remain untouched.

## Method

Inspected `docs/security/src02-contract-remediation-v1/models/safety_model.py`, `tests/test_src02_safety_model.py`, and the six SRC2-REV remediation contracts. Ran the existing model tests plus six independent synthetic audit tests. The finite explorer reports 16,642 quotient states, 32,651 accepted transitions, 339,477 rejected transition attempts, and maximum depth 12. These are bounded-model results, not an unbounded proof and not evidence of native OS behavior.

## Findings

### SRC2-REV-01 — OPEN

The model does not enforce that a committed response originated from a dispatch and an observed response. A reproducible sequence is `prepare_intent`, `durable_intent`, `persist_object`, `journal_durable`, `publish`, `head_durable`, `witness_prepare`, `witness_advance`, `ack`. No dispatch marker or response is recorded, yet `validate()` accepts `COMMITTED`. This violates the declared legal-history and response-provenance invariant. The original false-commit counterexample from PR #34 is rejected, but this distinct trace remains accepted.

### SRC2-REV-02 — PARTIAL

The stale-writer scenario is rejected: after writer A obtains epoch 7 and writer B takes epoch 8, A cannot publish. In the abstract model, epoch check and head publication are one transition. However, `State` does not model a lease ID or an explicit authoritative lease-transfer/commit serialization object, although the written fencing contract requires them. The model therefore does not fully cover lease identity and authority replacement.

### SRC2-REV-03 — OPEN

Dispatch after a durable intent is represented, and recovery after `DISPATCH_MAY_HAVE_STARTED` correctly prevents an unsafe inference retry. However, the model accepts persistence and commit without any dispatch or response, as described under REV-01. The crash distinction is insufficient unless every committed response is tied to `RESPONSE_OBSERVED` and its durable object.

### SRC2-REV-04 — OPEN

After witness divergence/unavailability, `witness_query` can clear `recovery_blocked` and return `RECONCILED` without a successful witness read. Acknowledgment remains blocked, but the recovery status itself falsely indicates reconciliation. Recovery must remain blocked until an authenticated, fresh witness result is obtained.

### SRC2-REV-05 — PARTIAL

The bootstrap, receipt, trust-anchor, identity, expiry, policy epoch, and revocation requirements are specified, but remain design requirements. There is no executable authenticated root-capability or restart-revocation implementation in this phase. No native claim is made.

### SRC2-REV-06 — PARTIAL

The Windows profile is constrained to a candidate platform/filesystem and defines fail-closed requirements. Handle-relative operations, DACL/reparse behavior, no-clobber, and flush/durability semantics remain NOT_VALIDATED because no native adapter was implemented or tested.

## Explorer deduplication

`State.history` is excluded from equality and hashing, while `validate()` consults history. An invalid altered history can therefore compare equal to a valid state. The explorer validates every generated successor before putting it in `seen`, and does not accept arbitrary externally supplied initial states. An independent depth-12 traversal checked 15,941 reachable history aliases across 16,642 quotient states; no alias had a different accepted-action frontier from its representative. This is bounded evidence for the current transition relation only. Keep validation-before-seen as an invariant; future transition changes must rerun the congruence audit. A compact validator-relevant history summary in the key, or replay validation of supplied states, would make the abstraction less fragile without storing an unbounded raw trace.

## Disposition

`SRC02_CONTRACT_REMEDIATION_REQUIRED`. The model rejects the named stale-fencing and historic false-commit examples, but the two counterexamples above prevent a pass. Linux profile readiness is `LINUX_CONTRACT_REFINEMENT_REQUIRED`. Native guarantees remain NOT_VALIDATED. Operational states remain `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED`; all eight gates remain PENDING.
