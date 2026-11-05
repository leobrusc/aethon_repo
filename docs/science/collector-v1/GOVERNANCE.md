# Evidence, storage and authorization governance

**Current state: all eight gates PENDING; PILOT_BLOCKED.** Public JSON templates
in `configs/science/receipts/` contain null identities, dates, evidence and signatures.
They are forms, not approvals. The original PR #15 manifest remains unchanged.

## Four distinct claims

1. Technical verification: file identities, live ACL/encryption observations,
   pinned assets, installed environment and resource observations.
2. Human review: blinded semantic/family review and rubric judgments, authenticated
   by independent scientific-reviewer signatures and their evidence ledgers.
3. Scientific approval: reviewer assignment/oracles/protocol disposition, distinct
   from a machine's ability to read files.
4. Operational authorization: a specific bounded run, destination, code/inventory/
   configuration/environment and budget. It is not implied by any prior receipt.

Receipt payloads bind schema/version, gate/kind, responsible signer, UTC issue and
expiry, complete subject hash and independently hash-checked external evidence.
Default maximum receipt validity is 24 hours. Role/quorum checks use external public
keys from a trust policy whose SHA-256 is supplied independently by the operator;
the receipt author cannot supply its own trusted root. Semantic/rubric review
requires two distinct scientific-reviewer signatures. Evaluator assignment requires
two evaluators plus a distinct adjudicator. Operations authority/operator must be
independent of the scientific reviewers used for those approvals.
Quorum counts distinct Ed25519 keys after DER normalization, not aliases or PEM
whitespace variants. Signed dispositions must explicitly verify/approve/authorize
the applicable gate; a signed rejection is not approval. Signatures are checked
before following evidence paths named by the receipt.

Production verification is Ed25519 through an existing absolute-path OpenSSL binary
whose executable hash is pinned by that policy. No verifier, key, dependency or
weight is installed/downloaded. Missing verifier/key/proof is a blocking condition.
Human identity/key distribution, revocation and verifier security review are external
responsibilities; signatures authenticate a statement, not its scientific truth.
In-process test verifiers are trusted injected code using synthetic keys; the CLI
does not expose a fixture/synthetic bypass. A compromised process/operator trust
anchor is outside this mechanism's protection.

`verify_gates` is a report only. `authorize` re-verifies the receipts and independent
live observations; it does not accept a caller-fabricated PASS report. A separate
signed launch_intent by the operator and an explicit collect invocation are required.
The issued in-process capability binds subject, policy, receipts, launch and expiry.
It is rechecked during writes. Merely constructing an approved flag, copying a
receipt, fabricating a report or possessing a template cannot start collection.

## Storage proof and retention

The root must already exist and be outside the repository, Git metadata and every
linked worktree, including external worktrees discovered through NUL-delimited Git
porcelain. Relative paths, symlink/junction/reparse ancestors and unsafe links are
rejected. Directory device/inode identities are checked through the run. The task
never provisions a production root, changes an ACL or enables encryption.

Windows read-only observations use Get-Acl/current SID and Get-BitLockerVolume.
Owner must be the current user, inherited ACLs disabled, user read/write allowed,
and no allowed principals beyond that user, SYSTEM and local Administrators. This
explicit privileged-admin trust assumption requires custodian acceptance. BitLocker
must be fully encrypted at 100%, with protection On. Missing module, permission,
unsupported volume or unverified result leaves storage PENDING. POSIX owner/mode
0700 can verify access but volume encryption is PENDING by default; no generic
unsupported-platform encryption claim is made.

A signed private_storage receipt must match the LIVE observation fingerprint and
a concrete external `aethon.retention-plan.v1` file with policy version, named
custodian, deletion process and future deletion date. Its bytes and hash are checked.
The collector refuses access after that date and records the policy hash. It does
not claim that future deletion has occurred, schedule an unapproved deletion task
or erase scientific evidence. Future erasure remains NOT_AUDITED until performed
and independently evidenced. Encryption protects storage-at-rest, not data from
the authorized owner or an already compromised host.

## Offline commands

```powershell
python scripts/prospective_collector.py preflight
```

Expected: exit 2, PILOT_BLOCKED and eight PENDING gates. No model, directory or
private case is created. The stronger preflight first checks the original frozen
protocol files, then authenticates external receipts; legacy PASS strings alone
never substitute for those stronger checks.

A future authorized operator supplies absolute external inventory/receipt/trust
policy paths, an independently obtained policy SHA, private root and run ID to
preflight. Only after all evidence checks and review, the same arguments plus a
separately signed `--launch` may be used with `collect`. No filled command or launch
authorization exists in this delivery. Production inventories require the private
inventory schema, 24 valid cases and `fixture_only=false`; unit fixtures are ineligible.

Evidence files are bounded to 10 MiB to prevent unbounded receipt/inventory parsing;
large model assets are hashed in streaming chunks. Public gate output contains only
sanitized statuses, no receipt claims, IDs, paths, raw prompts or responses. An
interrupted collect error reports unknown execution state and directs inspection of
the private journal rather than falsely asserting that nothing executed.

## Required external receipts

| Gate | Roles / independent evidence |
| --- | --- |
| independent_inventory | Steward; sealed inventory/hash and licensed-source ledger |
| semantic_review | Two reviewers; prior inventory coverage, pinned screen and review/disposition ledger |
| rubric_review | Two reviewers; scenario oracles and versioned objective/task rubric bundle |
| reviewer_assignment | Scientific lead; two known evaluators, distinct adjudicator, blinding plan |
| private_storage | Custodian; current ACL/encryption probe, concrete retention policy |
| model_assets | Asset reviewer; six exact snapshot-file hashes, template/revision binding |
| hardware_check | Platform reviewer; live environment/RAM/CPU and OS network-isolation evidence |
| execution_authorization | Operations authority; subject-bound bounded_pilot, 120 slots, max 96 calls |

Launch intent is an additional operator request, not a ninth scientific gate. No
names, approvals, authorizations or native security results were invented for these
eight gates. Current receipts, trust anchor, private inventory and production root
are absent; the checked-in configuration therefore stays PILOT_BLOCKED.

## Primary implementation references

[OpenSSL pkeyutl](https://docs.openssl.org/3.1/man1/openssl-pkeyutl/)
documents Ed25519 raw-message verification. [Microsoft Get-BitLockerVolume](https://learn.microsoft.com/powershell/module/bitlocker/get-bitlockervolume)
and the [BitLocker operations guide](https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/operations-guide)
describe the read-only volume/protection observations used here. [Python os](https://docs.python.org/3/library/os.html)
documents flush/fsync/link primitives; those primitives do not independently prove
power-loss durability on every deployment filesystem.
