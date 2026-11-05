# Scientific contract validation

**PILOT_BLOCKED.** Synthetic fixtures are not scientific observations or an ASR,
power, statistical confidence or efficacy estimate.

The canonical families are exactly `instruction-override`, `synthetic-disclosure`
and `answer-contamination`, as named in the frozen pilot plan. The collector now
requires 12 distinct matched pairs, 24 distinct cases, four pairs per family,
one integer-labeled attack and one clean control in each pair, identical task
context and unique source/scenario/structured sample identity. Unknown family or
any distribution other than 4/4/4 fails before slot construction. This validates
structure, not semantic family membership, licensing or independence.

B0 bypass, B1 L1, B2 historical L2, B3 L1 OR L2 before generation, B4 same decision
plus epsilon=1.2 noisy audit are unchanged. Historical seed 42, generation seed
2026, thresholds, model revision, CPU float32 and tokenizer/template contracts are
unchanged. B3/B4 reuse still requires matching effective inputs/configuration and
defense decisions, records its source, and never creates an independent draw.

## Separate collection and review states

The existing slot collection states remain compatible for recovery. The run adds
`collection_status=COLLECTION_IN_PROGRESS|COLLECTION_COMPLETE`; accounting complete
does not imply successful inference, scientific completeness or authorization.
The collector's scientific-review status remains conservatively REVIEW_PENDING.
An injected callback is not an authenticated vote and its output is rejected as
evaluation_error, preserving the response for later independent review. The CLI
with no judge retains evaluation_pending. Legacy unsigned evaluation pointers
are rejected rather than imported as authorized judgments.

`ReviewLedger` has a separate private signed-vote API and per-response states:

| Evidence present | Scientific state |
| --- | --- |
| No authenticated vote | REVIEW_PENDING |
| One assigned signed vote | VOTE_RECORDED |
| Two assigned votes disagree; no adjudication | ADJUDICATION_PENDING |
| Two assigned votes agree, or distinct assigned adjudicator resolves disagreement | SCIENTIFIC_REVIEW_COMPLETE |

The final audit contains both immutable vote references, adjudication reference
when needed, explicit policy, outcome and canonical audit hash. Agreement can be
indeterminate: complete review does not mean a resolved success/failure label.
No response or failed/truncated response is silently classified as defense success.
No callback can directly set these states. Two aliases of one key are rejected.
Each envelope is authenticated against the run-bound assignment and approved
rubric bundle; each evidence span binds the exact case/slot/response/rubric and
substring hash. Missing, incompatible or unapproved evidence is rejected.

Both independent raw votes are immutable, idempotent only when byte-identical;
conflicting updates are rejected. Adjudication must bind both conflicting vote
references and the distinct designated adjudicator. Journal replay reconstructs
and verifies the audit; historical vote expiry is checked at journal record time
and the run capability must still be valid. No automatic rerating occurs on resume.
Review of B4 reused output resolves through its verified B3 source and is not a
second vote/independent observation. Case IDs in that audit identify the source
slot explicitly; the B4 slot retains its reuse provenance.

The ledger returns per-response completion only; it does not turn the 120-slot
collection summary into a global scientific sign-off. A later approved reporting
stage must check all eligible slots, missingness, raw votes, dependence clusters,
blinding and complete denominators. Current technical-error suspension still uses
terminal-slot counts; a scientific denominator clarification remains pending.
