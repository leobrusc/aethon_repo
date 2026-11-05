# Prospective collector remediation v1

Technical classification: **REMEDIATION_PARTIAL**. Operational classification:
**PILOT_BLOCKED**. This version does not claim production execution readiness.

Parent review #17: `355e07d9bb20200df953628d49f20368d6439e54`; collector #16:
`aa6d171d82961aa297808c24ac602076abf47883`; science #15:
`1c6fc01edef58cc1565a7c233c7a23722a4d72a1`; engineering baseline:
`9ed55709add0fc45f63847a0394315863faa0876`.
Branch: `fix/prospective-collector-security-v1`, isolated worktree
`.worktrees/collector-remediation`. Original branches/worktrees/main are preserved.

## Finding disposition

| ID | Original | Change | Acceptance tests | Evidence | Final |
| --- | --- | --- | --- | --- | --- |
| SRC-01 | FAIL | Remove pathname subprocess invocation; pin and compare tool/dependency/ancestor identities; deny execution without approved object-bound loader backend | verifier drift, rename, dependency, ancestor, no fallback; genuine local Ed25519 baseline | test_pilot_remediation.py; test_pilot_collector.py; validation/ | FAIL for operational closure; denial PASS; native backend NOT_AUDITED |
| SRC-02 | FAIL | Bind observation to subject, path/object/ancestor identity and fingerprint; reject stale observations before mkdir; guard identity changes; deny production writes without native confinement | replaced root, foreign observation, changed ancestor/mode, stable fixture, interrupted atomic write, foreign recovery | test_pilot_remediation.py; adapted regression suite; validation/ | FAIL for operational closure; denial PASS; native I/O NOT_AUDITED |
| SCI-01 | FAIL | Enforce exactly four matched pairs for each canonical family, preserve structured identities | 4/4/4; 12/0/0; 5/4/3; 6/3/3; unknown/incomplete/duplicate/context drift | test_pilot_remediation.py | PASS, structural contract only |
| SCI-02 | FAIL | Reject callback judgment authority; authenticated independent review ledger binds assignment, slot, response and rubric; two immutable votes, adjudication on disagreement | unassigned/aliased evaluator; foreign case/hash/rubric/evidence; one vote; conflict; wrong/missing adjudicator; valid agreement/adjudication and recovery | test_pilot_remediation.py; pilot_review.py | PASS for synthetic software contract; human truth/real crypto deployment NOT_AUDITED |

SRC-01/02 no longer expose the original operational paths: they fail closed.
They remain incomplete as usable production capabilities. A second hash read is
diagnostic, not a claimed solution to TOCTOU. No receipt flag enables either path.
The explicit Python confinement/verifier injection seam is trusted application
code for synthetic fixtures; it is absent from the CLI and not an approved backend.

## Preservation of original demonstrations

Original PR #17 test files are retained byte-for-byte as canonical Git payloads in
`historical/*.py.txt`, with source commit, Git SHA-256 and observed Windows-checkout
SHA-256 in `historical/index.json`. Original four reports and `review-evidence/`
remain unchanged. The archived tests demonstrated vulnerable acceptance and are
not collected as current acceptance tests. Running them requires the exact old
commit and original fixtures, not the fixed implementation.

The active independent-review tests explicitly assert denial for SRC-01/02,
SCI-01 invalid quota rejection, and SCI-02 no authorized evaluation. Their original
names identify the historical findings; docstrings identify the changed oracle.
Existing synthetic fixtures now use the exact canonical families and subject-bound
identity observations with an explicitly test-only confinement fake. Synthetic
callback results are rejected, so earlier `completed` expectations become
`evaluation_error`; generated outputs remain preserved for authenticated review.
No test is silently skipped to preserve a vulnerability. The genuine local OpenSSL
test still checks a valid Ed25519 signature and rejects tampering in a controlled
test subprocess; it separately verifies that production pathname execution is denied.

`collector_v1.json` implementation seals are updated only for the remediation
sources/tests, adding the new identity/review modules and acceptance tests. This
changes the protocol fingerprint and invalidates old run receipts. Frozen PR #15
protocol/target/generation, B0–B4 definitions, thresholds, seeds and all historical
locks/results remain unchanged. New review-rubric bindings extend the run manifest;
old manifests missing them cannot be silently upgraded into scientifically reviewed
runs. No old response/evaluation file is overwritten.

## Validation and next review

Actual commands, exit codes and output hashes belong in `validation/`; the final
run records its new identifier. Preflight exit 2/PILOT_BLOCKED is the expected safe
result. No real target inference, model download, paid service, production root,
ACL change or pilot is authorized or performed here.

Run `remediation-final-20261105T182459Z`: **249 passed**, one expected mocked-download
warning, zero skips (214 inherited/adapted cases plus 35 new acceptance cases).
Ruff, pip check, whitespace, 127-file inventory, 31 indexed artifacts, six historical
dependency manifests, LFS fsck/five hydrated hashes, 9,139 historical B3/B4 pairs
with zero decision differences, all 80 published metric values and five preexisting
local-file hashes PASS. No historical dataset/result/lock or frozen PR #15 protocol,
target or generation manifest changed. Both offline preflights and the explicitly
incomplete collect invocation returned expected exit 2; no target model loaded.
Python network audit observed zero connection/DNS events; native egress remains
NOT_AUDITED. This local Windows run is not evidence of native Linux execution.

Development run 1 is retained separately: 84 passed/four failures (missing dependency
fixture, two stale state/backend expectations and stale implementation seals).
The fixture and active compatibility expectations were corrected; updated seals
bind the final sources. The old vulnerable assertions remain in the hash-indexed
historical archive, and final acceptance tests explicitly require rejection.

Request a new independent review of the source, denial paths, authenticated ledger
and original-to-acceptance mapping. Before operational closure, design and audit
platform-specific executable/loader confinement and all storage operations under
stable directory capabilities, or select a separately authorized audited verifier
and storage architecture. Do not promote test injection to a production backend.
All eight gates remain PENDING and require independent evidence plus explicit
operational authorization after remediation review.
