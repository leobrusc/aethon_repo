# Prospective collector threat model

Scope: PR #16 at `aa6d171d82961aa297808c24ac602076abf47883`.
State: **PILOT_BLOCKED**. Findings are in INDEPENDENT_SECURITY_REVIEW.md.

| Asset | Required property |
| --- | --- |
| Private prompts, responses, token IDs, oracles, votes | Confidentiality; external encrypted access-controlled storage; retention |
| Inventory, labels, pairing, 120 slots, generation metadata | Complete immutable provenance, no silent exclusions or retries |
| Policy pin, public-key registry, operational receipts | Independent trust distribution, role/quorum/subject/time integrity |
| Code, tokenizer, model, detector, verifier, environment | Exact reviewed identity through use, not merely initial pathname hash |
| Historical datasets, metrics, locks, local user edits | Byte continuity; no new experimental writes |
| Run budget and journals | At most authorized calls; recoverable, attributable state transitions |

Trust boundaries: public repository versus private inventory/storage; unsigned
receipt bytes versus authenticated statements; scientific approval versus
operational authority and separate launch intent; adapter versus token decoder;
untrusted continuation versus evaluator oracle; process checks versus OS guarantees;
preflight snapshot versus subsequent filesystem use; local journal versus any
independent rollback anchor.

Adversaries include an untrusted model output author, receipt-file substituter
without signing keys, an operator confusing roles, and an actor able to mutate a
specific tool or storage ancestor without owning the Python process. The last
capability is conditional: secure tool/ancestor ACLs can exclude it. A malicious
application callback can return bad judgments; production CLI currently avoids
that path. Compromised administrator/kernel/Python process and compromised
independent trust-anchor distribution are outside the cryptographic mechanism.
Signatures establish authorship of statements, not scientific truth.

Surfaces: CLI paths/pins; policy and key files; external evidence references;
JSON identity/schema fields; model/cache symlinks; subprocess executable loading;
private root ancestors; hard-link publication and pointer journals; evaluator
callbacks; native extensions/process launch APIs. Path prechecks are not held
filesystem capabilities. Absolute names alone do not prevent check/use races.

Launch conditions: all eight independently evidenced gates must verify for the
same subject/configuration/code/inventory/destination/environment; technical live
observations must match signed receipts; independent operations authority and
operator must sign the bounded 120-slot/96-call launch; capability must remain
unexpired, retention valid, source clean, local assets exact. No report or approved
flag can independently grant that capability.

Critical failures: confidentiality loss at replaced storage, forged verification
through replaced tool, unknown-run checkpoint acceptance, duplicated uncertain
inference, prompt contamination of judge, suppressed missing observations and
unreviewed judgments appearing scientifically complete. Confirmed conditional
failures SRC-01/02 and scientific gaps SCI-01/02 require remediation.

OS-dependent guarantees: trusted owner/admin identities; protected directory and
ancestor ACLs; effective volume encryption; executable/loader protection; atomic
hard-link semantics and crash durability; exclusive worker; firewall egress;
private backups, anti-rollback anchor and eventual erasure. Application socket
patches do not establish egress containment. These require native deployment
evidence; synthetic tests cannot certify them. No production ACL, directory,
firewall or encryption setting was changed by this review.
