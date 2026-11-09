# SRC-02 milestone — decision register and exit criteria

Baseline: PR #41 HEAD `e7f15000b682b0cb7824c71fc55daf6f9a2129c9`. Review closed SRC2-REV-01 through 04 **only for abstract synthetic State behavior**, not real native guarantees. SRC2-REV-05 and 06 remain PARTIAL. No merge or operational approval is implied by this milestone.

| Workstream | Proposed architecture | Approval needed | Evidence needed | State |
|---|---|---|---|---|
| Bootstrap | External receipt issuer; retained root FD | Provisioner, identity owner, root custodian, trust-anchor owner | Signed/verified receipt, revocation, principal/root/ancestor identity negative tests | PENDING |
| Witness | Independent linearizable compare-and-advance | Separate service operator and key custodian | Atomicity, equivocation/replay, timeout, rotation, backup independence | PENDING |
| Linux | x86_64 single-host ext4 as candidate | Platform owner, OS and infrastructure security | Exact allowlist; power-loss/fault/race tests; namespace/FS/flush evidence | PENDING |
| Commit/fencing | One serializer for lease epoch and head CAS | Systems security architecture owner | Stale-writer race, crash barrier proofs on exact stack | PENDING |
| Dependencies | No new package approved | Software supply-chain approver | Pinned SBOM, provenance, licenses, vulnerabilities, wheel audit | PENDING |
| Independent design review | Separate reviewer from proposal author | Security architecture approver | Signed review of ADRs and failure matrix | PENDING |
| Pilot | No execution authority | Eight gate owners | Each independently accepted gate plus run-specific authorization | BLOCKED |

## Sequence
1. This PR: commit ADRs, proposed profiles, manifest, fail-closed lint and tests. **Never create a root, witness, credential or pilot run**.
2. Independent architectural review: challenge issuer/anchor bootstrap, witness linearizability, Linux durability profile and combined fencing/head serialization. Record unresolved decisions and counterexamples; do not write native code.
3. Only with separate explicit approval for a **fixture-only prototype**, create a new branch for a Linux experimental adapter with sandboxed OS identity, no real confidential prompts and no inferencing.
4. Native qualification on an approved test stack: T01–T19 (as applicable), crash/fault logs, independent review, and approval gates. An adapter implementation or CI PASS is not permission to run a pilot.
5. Operational review is entirely separate: all eight launch gates, dependency approval, infrastructure controls, human authorization, scientific data quality and retention requirements.

## Preventing accidental promotion
`READINESS_MANIFEST.json` is explicitly **DESIGN_ONLY**. `scripts/check_src02_native_readiness.py` rejects missing/altered gate records, fabricated evidence, extra keys, or changed approval strings; a successful check returns status `DESIGN_ONLY_BLOCKED`, never `AUTHORIZED`. It does **not** authenticate approvers, sign policies, or grant capabilities. A future approval must be a separate independently authenticated artifact with a new schema and code path; do not edit this design manifest to simulate approvals.

## Scientific integrity
This milestone changes only additive design documents and independent synthetic readiness tests, not algorithms, inference, scientific inventory, protected artifacts, existing 80 metric receipts, six manifests, existing LFS files or test fixtures. The known canonical `hf_red_team_attempts.jsonl` non-JSONL format issue remains separate and unchanged. Historical 9,139 B3/B4 preservation should be verified by hosted CI and reported accurately; the design itself does not claim a new scientific measurement.

## Permanent states
`SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED`; all eight gates remain `PENDING`. Native backend/root/witness service remain `NOT_IMPLEMENTED/NOT_PROVISIONED`.
