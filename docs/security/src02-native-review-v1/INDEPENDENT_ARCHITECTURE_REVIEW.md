# Independent SRC-02 native contract review

## Disposition

**`NATIVE_CONTRACT_REMEDIATION_REQUIRED`.** PR #33 is a coherent architecture outline, but the abstract commit checker admits an impossible committed state and critical commit/lease transitions are not yet precise enough to implement safely. Do not start the Linux prototype until the blocking contract findings below are closed and reviewed. This is a specification finding, not evidence of a defect in a native backend (none exists).

## Identity and CI

- Reviewed PR #33 HEAD: `cf4a64beef8d4e94e25ac9651db7954468291ebf`.
- Base PR #32: `ada83b59ac2eb22ea7abc9acc31913b7fef6a220`; exact ancestry verified.
- CI `42405294444` is associated with the reviewed SHA. Linux, Windows, and research/GPU audit jobs all completed `SUCCESS`; pytest was 408 passed/one warning on each OS. GPU inference was `NOT_RUN`.
- Independent review branch starts from the exact PR #33 HEAD. No earlier branch or `main` was modified.

## Findings

| ID | Severity | Contract / invariant | Counterexample or gap | Required correction |
|---|---|---|---|---|
| SRC2-REV-01 | HIGH | Abstract commit model must only label COMMITTED after object, journal, head and required witness barriers | `classify(Snapshot(intent=True, acknowledged=True, head_durable=True, object_durable=False, journal_durable=False), witness_required=False)` returns `COMMITTED`; with `witness_required=True`, setting `witness_advanced=True` still returns `COMMITTED` while object/journal remain false. Reproduced locally. | Validate every prerequisite and legal transition; reject non-monotonic/impossible snapshots. Add negative assertions for missing object/journal, stale head, absent witness, and illegal state order. |
| SRC2-REV-02 | HIGH | A stale writer must be unable to publish after lease transfer | Contract says revalidate token immediately before head CAS, but does not make the token part of the atomic commit condition. Interleaving: writer A validates token 7; lease expires/transfers and writer B obtains token 8; A performs head CAS using only old expected head. “Revalidate before” leaves a TOCTOU window. | Define an authoritative monotonic fencing epoch and require the same atomic publication/CAS to reject any token other than current epoch. If filesystem primitive cannot do this, use an independently serialized commit authority; do not rely on memory or a pre-check. |
| SRC2-REV-03 | HIGH | Inference is never repeated after an uncertain external effect | A durable intent is required, but the schema/state transition does not distinguish “intent persisted, inference not dispatched” from “inference may have started”; the abstract model only has a Boolean and has no durable transition evidence for the dispatch boundary. Recovery therefore cannot prove when `NOT_COMMITTED` permits retry. | Specify per-slot durable states and exact write-ahead protocol: intent commit receipt before invocation, a conservative dispatch marker, response publication, and recovery rule. Any intent lacking proof that dispatch did not occur must become `interrupted_unknown` and cannot be retried. |
| SRC2-REV-04 | MEDIUM | Local head and monotonic witness must converge deterministically after crashes | Local head is advanced before witness. If witness advance succeeds but its acknowledgment is lost, or local head is durable while witness is behind/unavailable, the current rule blocks resume but provides no retry/reconciliation protocol or decision for “same sequence, same hash” versus conflicting state. | Specify authenticated compare-and-advance request IDs, idempotent response retrieval, four local/witness relation cases, safe reconciliation and recovery authorization. Never reset a witness sequence silently. |
| SRC2-REV-05 | MEDIUM | RootCapability issuance and revocation must be independently verifiable | Roles and bound fields are named, but issuer trust anchor, receipt authentication/schema, process principal measurement, revocation authority/source and race policy are not defined sufficiently to test a bootstrap result. A retained handle also does not revoke already granted access. | Define issuer/key custody, signed bootstrap receipt, exact OS principal and ancestor evidence, revocation epoch/source/freshness, and stop semantics for in-flight operations; state limits for held handles. |
| SRC2-REV-06 | MEDIUM | Windows path confinement must rely on a documented, testable reparse policy | `NtCreateFile` relative naming is documented, but the contract does not pin a supported Windows API/flag combination for rejecting reparses throughout component parsing; root acquisition and exact no-clobber/metadata durability are also unresolved. | Require a reviewed handle-relative adapter and documented supported reparse behavior; reject unsupported combinations. Prototype must test the exact Windows build/filesystem; do not infer guarantees from API availability. |

Severity reflects the effect on safety of the proposed contract. No native implementation was tested, and no claim is made that the findings demonstrate an exploitable production backend.

## Subsystem disposition

| Subsystem | Review status |
|---|---|
| Linux profile | **Refinement required before prototype**: candidate primitives are plausible on a narrowly supported local filesystem, but lease fencing and intent/commit state are blockers. |
| Windows profile | **Refinement required**: native handle-relative approach is plausible, but exact reparse contract and metadata durability remain unresolved. |
| Freshness witness | **Refinement required**: independence principle is sound; protocol and recovery consistency are underspecified. |
| Durable commit | **Not ready**: abstract model false-positive plus missing dispatch-state semantics. |
| Interprocess lease | **Not ready**: no atomic persisted fencing check or concrete OS primitive contract. |
| Post-collection review | **Conceptually sound; details pending**: separate grant/quorum retained, but independent issuer/revocation and durable key/assignment lifecycle need specification before implementation. |

## Safety boundary

The review does not require resistance to a compromised kernel, administrator controlling all trust domains, malicious storage firmware, or arbitrary same-process Python execution. It does require fail-closed behavior for untrusted inventory, non-privileged races, crashes, rollback and uncertain inference within the stated threat model.

Keep `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED` and all eight gates `PENDING`.
