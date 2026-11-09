# SRC-02 safety model remediation

Status: abstract contract remediation for independent review. No native backend,
root capability, witness service, OS lock, filesystem I/O, or inference was used.

## Root cause and corrected invariant

The PR #33 classifier treated `acknowledged`, `head_durable`, and an optional
witness flag as independent booleans. It omitted `object_durable` and
`journal_durable`, and accepted states with no legal transition history. The
PR #34 counterexample therefore classified an impossible transaction as
`COMMITTED`.

The replacement at `models/safety_model.py` uses a closed action relation. Durable
facts are produced only by named transitions; a snapshot must satisfy bindings,
ordering, sequence, operation digest, fencing and witness invariants before it can
be classified. The acceptance invariant is:

```text
COMMITTED => object_durable AND journal_durable AND head_durable
            AND fencing_valid AND witness_policy_satisfied
            AND legal_history AND exact_run_operation_manifest_binding
```

`COMMIT_UNKNOWN` is not a successful state. The state carries explicit inference
and recovery enums, current/published fencing epochs, durable local head and
witness policy epochs, revocation, quota and operation bindings. Illegal or
inconsistent snapshots return `REJECTED`. A no-witness profile is modeled separately: it removes only the
external witness prerequisite and explicitly gives up protection against
coherent whole-store rollback. It still requires local barriers, legal history,
and current fencing.

## Legal commit transitions

`INTENT_PREPARED → INTENT_DURABLE → DISPATCH_MAY_HAVE_STARTED → RESPONSE_OBSERVED
→ RESPONSE_DURABLE → OBJECT_DURABLE → JOURNAL_DURABLE → HEAD_PUBLISHED
→ HEAD_DURABLE → WITNESS_ACKNOWLEDGED (when required) → ACKNOWLEDGED`.

Head publication is one abstract transition that compares the current writer and
epoch with the expected head. A later durable barrier is separate; no receipt is
acknowledged before it. The witness uses compare-and-advance with a fixed
Operation ID and predecessor. Repeating the same request is idempotent; a changed
request or divergent checkpoint is rejected.

## Historical counterexample preservation

The original PR #33 model remains unchanged in history and at its original path.
At PR #34, its working-tree SHA-256 was
`c4dd46acb740dd2cf8960857b788507291908fe673d574f769757b2e7c1ecae2`; Git blob
`04490105d90603f131f8baf3663eaaf59cb6e021`. The original counterexample is
preserved byte-for-byte in PR #34's `COMMIT_AND_RECOVERY_REVIEW.md` (working-tree
SHA-256 `67148a524be9d2fc338de9970c97ac38e1ba8d724f340ec08727b410c75b54eb`;
GitHub report at reviewed PR #34). No historical file was rewritten.

The corrected tests reject the old `intent=True, acknowledged=True,
head_durable=True, object_durable=False, journal_durable=False` snapshot under
both witness-required and no-witness profiles. Additional tests remove each
durability prerequisite, mutate a digest, create a witness sequence gap, or
attempt an acknowledgment outside a legal transition.

## Limits

This finite model does not prove syscall behavior, power-loss durability, kernel
locking, witness independence, or liveness. Its single-run/one-operation state
space and finite exploration bounds are recorded in `STATE_EXPLORATION_RESULTS.md`.
The implementation gate remains closed pending independent review and native
fault-injection plans.

## Phase 7E superseding addendum

The independent PR #36 review found additional accepted traces: commit without
dispatch/observed response and recovery reconciliation without a valid remote
witness response. Phase 7E changes the transition relation to reject these
traces and adds explicit run/slot/op/manifest/config response binding, observed
continuation SHA-256 verification, durable-response gating, separate witness
response/authentication/freshness/reconciliation states, and lease ID/authority serialization state. The Phase 7C
counts above are historical only; current bounds and results are recorded in
`docs/security/src02-safety-closure-v1/BOUNDED_STATE_EXPLORATION.md`.

The witness signature/freshness checks are abstract trusted outcomes, not a
cryptographic or deployed service implementation. SRC2-REV-05/06 remain partial;
native SRC-02 remains NOT_AUTHORIZED pending independent review.
