# Post-collection review authority

## Separate principal and grant

Collection authorization expires with the collection session and is not silently renewed for review. After collection closes, a separately governed review grant is issued to named evaluators and, when required, a distinct adjudicator. It binds exact run/root IDs, manifest digest, response object digests, rubric version/hash, assigned reviewer identities, quorum policy, blinding constraints, read/write scope, retention and expiry. It grants only read access to required private continuations and append-only vote/adjudication writes; it cannot alter requests, responses, slots, generation metadata or collection journal history.

The grant is checked against the existing signed assignment/rubric evidence and revocation policy. No approval is inferred from a callback, receipt existence, collector authorization, or fixture. Reviewer keys/identities are distinct under the frozen quorum contract; aliases do not count as independent identities.

## Review transaction and states

`COLLECTION_COMPLETE → REVIEW_PENDING → VOTE_RECORDED → (SCIENTIFIC_REVIEW_COMPLETE | ADJUDICATION_PENDING) → SCIENTIFIC_REVIEW_COMPLETE`.

Each immutable vote binds run, slot, case, response digest, rubric digest, reviewer identity/key, assignment evidence, vote schema/version, timestamp policy and operation ID. A retry with the same reviewer/operation/content returns the same durable receipt; changed content collides. Two independent votes are required. Concordance follows the frozen rubric policy. Discordance enters `ADJUDICATION_PENDING`; only a separately designated adjudicator may append an adjudication linked to both votes. No single vote or callback completes review.

Review storage uses the same native confinement, journal, lease, durability and witness rules. Grant expiry/revocation blocks new reads/writes; already persisted votes remain immutable and auditable. Reopening is read-only except scoped append operations. At completion, close handles, revoke session grant, preserve audit receipts under retention policy and expose only approved aggregate outputs. Private prompts/responses never enter public logs, CI artifacts or Git.

## Separation of duties

The storage custodian, collector operator, scientific approver, two reviewers and adjudicator must satisfy the independently approved role-separation policy. This document defines no real identity or signature and does not satisfy reviewer-assignment, rubric-review, private-storage or execution-authorization gates.
