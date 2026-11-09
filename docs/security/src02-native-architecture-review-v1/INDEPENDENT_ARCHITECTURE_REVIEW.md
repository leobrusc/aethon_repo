# Independent review of PR #42 — SRC-02 native architecture

## Identity, scope and decision

Reviewed exact PR #42 HEAD: `bf28e2f93bf94f71dda995505813cdc0d0537fb7`. This is a **separate review branch**, not the original architecture design. Prior PR #41 abstract safety closure is accepted solely within the finite synthetic State/API model. No native backend, real witness, signed grant, platform mount or trust anchor exists in this review.

**Disposition: `REVIEW_COMPLETE_WITH_BLOCKERS`** (technical critique only). The three ADRs are coherent candidate directions but **not APPROVED for implementation**. The architectural **release blocker is the missing concrete atomic serialization authority for epoch transfer and durable head CAS**. Root bootstrap issuer/key custody, witness administration and precise Linux stack also remain undecided. Only the relevant organizational custodian and independent approvers can sign off those properties.

### Findings and severity

| ID | Severity | Area | Finding | Required resolution |
|---|---|---|---|---|
| ARCH-REV-01 | HIGH | ADR-001 | Independent root issuer, signed trust-anchor set, OS principal and revocation service are unspecified and unprovisioned | Approval owner, non-self-issued receipt contract, restart/revocation negative evidence |
| ARCH-REV-02 | HIGH | ADR-002 | Service A proposed without approved operator, independent durable state, disaster recovery and cryptographic proof selection | Linearizability and anti-equivocation contract; independent identity, backup and key custody |
| ARCH-REV-03 | **CRITICAL** | Commit/fencing | No concrete native one-serializer implementation for epoch transfer and head publication | Specify atomic authority or block native writer takeover; demonstrate stale-writer rejection and durable recovery |
| ARCH-REV-04 | HIGH | ADR-003 | Candidate Linux x86_64/ext4 lacks exact kernel/build/mount/device/flush qualification | Supported stack allowlist and crash/power-loss/namespace fault matrix |
| ARCH-REV-05 | HIGH | Approval | Human approval and dependency authorization remain missing | Independent security/operations and software supply-chain approval; separate prototype-only grant |
| ARCH-REV-06 | MEDIUM | Manifest | Design-only lint exit 0 could be mistakenly read as operational readiness | Preserve explicit `authorized=false`; no bridge to runtime authority |

### Review conclusion

ADR-001: `REVISE_AND_OBTAIN_EXTERNAL_APPROVAL`.
ADR-002: `REVISE_AND_OBTAIN_EXTERNAL_APPROVAL`.
ADR-003: `REVISE_AND_QUALIFY_PLATFORM`.
Commit/fencing: `BLOCKING_CONCRETE_PROTOCOL_REQUIRED`.

The design-only manifest remains `DESIGN_ONLY_BLOCKED`; passing synthetic tests cannot issue a grant or change the eight operational gates. The exact negative-native test matrix T01–T19 remains `NOT_RUN`. The prior scientific 9,139 B3/B4 pairs, 127 protected files, 31 evidence hashes, six manifests and five LFS payloads remain outside modification scope. The 80 metric receipts are historical, not recalculated here.

A separate, genuinely independent security architecture reviewer must review any remediation and approve a fixed implementation profile before an isolated fixture-only Linux prototype is requested. Reviewer authored this technical test proposal but is not the organizational grant issuer.
