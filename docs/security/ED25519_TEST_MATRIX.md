# Ed25519 proposal and acceptance test matrix

**DEPENDENCY_APPROVAL_REQUIRED; PILOT_BLOCKED.** Current tests validate proposal
structure, rejection paths and prepared acceptance scaffolding, not a working
cryptography adapter. No approved cryptography provider is available in the current
Windows test environment; actual provider acceptance is NOT_RUN, not skipped PASS.

| Requirement | Viable evidence in this phase | Actual provider/runtime acceptance |
| --- | --- | --- |
| Known Ed25519 vectors | Two public RFC8032 vectors retained; byte shapes/SPKI identity checked | NOT_RUN; actual approved provider required |
| Wrong key / modified message / invalid or truncated signature | Ten prepared acceptance cases; harness rejects always-VALID, always-INVALID and unavailable stubs | NOT_RUN for cryptography; prepared corpus is not an algorithm implementation |
| Alternative/malformed key | Existing strict SPKI identity rejects wrong OID/length; prepared provider negatives | Provider-specific behavior NOT_RUN |
| Canonical payload | Existing canonical function exact bytes/ordering/UTF-8/NaN checks | Signed canonical-byte round trip pending approved adapter |
| Replay / policy substitution / aliases / flags | Existing authenticated receipt contract exercised with explicit synthetic fixture verifier | End-to-end Ed25519 governance integration pending |
| Missing provider / external execution | Current production backend always denies; subprocess and shell canaries prohibited | Future provider loader/absence classification NOT_IMPLEMENTED |
| Import shadowing | Disabled backend does not import a synthetic shadow provider | Future immutable-runtime/import-attestation tests NOT_IMPLEMENTED |
| Runtime change | Existing pinned-tool identity drift still rejects | Python/package/native-library tamper enforcement NOT_IMPLEMENTED |
| Status bridging | Test-only explicit VALID/INVALID/UNSUPPORTED bool contract; unexpected results denied | No new production bridge/adapter installed |
| Supply-chain inventory | Exact five artifacts/versions, marker/tag metadata and declared SBOM checked | Wheel bytes, attestations, native closure/licenses still NOT_AUDITED |

Tests: `tests/test_ed25519_proposal.py`; prepared runner:
`tests/ed25519_contract_cases.py`; public vectors:
`tests/fixtures/ed25519_public_vectors.json`. The runner takes an explicitly supplied
future approved callable, imports no provider and has no discovery or fallback.
Its current self-tests deliberately reject invalid stubs; they do not substitute
a canned verifier for genuine known-answer cryptographic validation.
[RFC8032 section 7.1](https://www.rfc-editor.org/rfc/rfc8032.html#section-7.1)

Existing genuine Ed25519 tests using the preexisting local OpenSSL executable are
inherited synthetic regression evidence only. They neither verify the proposed
cryptography wheels nor enable that external tool as a production fallback.

## Required regression and preservation

Run the full existing suite plus proposal tests offline in the maintained Python
3.12 environment, Ruff, pip check, staged/committed guards, whitespace, offline
preflight, Git LFS and scientific verifiers. Recheck 127 protected files, 31 indexed
artifacts, six historical manifests, 9,139 B3/B4 pairs, 80 historical metric values,
five LFS payloads and five preexisting local hashes. Preserve all previous SRC-01
reports/reproductions and their hashes. Use a new run ID; publish no generated
private keys, prompt/response objects or fixture directories.

CI #42088936881 must be recorded against exact parent HEAD
`7431d7b423bc6fc34d1db51c12794742481f8428`, distinguishing that parent CI from
this proposal's tests and from nonexistent provider validation. Native binary
advisory coverage and independent canonical raw-dataset identity remain NOT_AUDITED.

## Future acceptance gates

Actual RFC8032 positives, all negatives, unsupported provider, key parsing, bool
integration, package/import/native tamper rejection, immutable runtime custody,
no subprocess fallback and exact governance semantics must pass on each declared
approved OS before SRC01_TECHNICALLY_VALIDATED can be considered. A missing platform
or an unavailable provider is NOT_RUN/blocked for that claim. No signature result,
metadata approval, synthetic test or CI success independently authorizes a pilot.

## Observed local run

`ed25519-proposal-20261105T190913Z`: **280 passed**, one expected mocked-download
warning, zero skips (253 inherited plus 27 proposal/denial cases). Ruff, pip check,
both offline preflights, incomplete-collect denial, 127/31/six scientific verifiers,
9,139 paired identities/labels/decisions, all 80 historical metric values, LFS fsck/
five payload hashes and five original local hashes PASS. Preflight/denial exit 2
is expected and keeps all eight real gates PENDING. No actual candidate provider
was imported or installed. Python audit observed zero connection/DNS events in
the test session; package/provenance/advisory metadata queries ran separately.

Raw logs, expected exit codes, SHA-256 index, controller inventory, metadata-query
logic and parent CI receipt are retained in `ed25519-v1/validation/`. Formal SBOM
JSON-schema validation and complete native/binary SBOM remain NOT_RUN/NOT_AUDITED;
no new validator dependency was installed. Proposed artifact tags/marker closure
were checked using the existing packaging tools, not an actual environment solve.
