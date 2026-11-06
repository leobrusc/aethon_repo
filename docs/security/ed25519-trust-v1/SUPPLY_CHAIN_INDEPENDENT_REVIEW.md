# Independent supply-chain trust review — Phase 5C

**Integrity: VERIFIED (5/5). Provenance: PARTIALLY_VERIFIED (two VERIFIED, three NOT_VERIFIED). Native coverage: COVERAGE_PARTIAL. Dependency decision: EXCEPTION_REVIEW_REQUIRED.**

Reviewed immutable PR #21 `0eef2cb7797df1ed21ae89cf3286462697aa3a83`, dependent on PR #20 `b3f7819b94e8710cc4df9e7fb8ab87d5b323fc15`; baseline `9ed55709add0fc45f63847a0394315863faa0876`. Branch `review/ed25519-supply-chain-trust-v1`, isolated worktree `ed25519-trust-review`. Original dirty checkout and five local files preserved. No old report/evidence was overwritten. Source #21 SHA index passed 28/28; five wheels were rediscovered from the custody manifest and rehashed without reacquisition.

| Wheel | Integrity | Provenance |
|---|---|---|
| `cryptography-50.0.2-cp311-abi3-win_amd64.whl` | VERIFIED | VERIFIED (publish identity) |
| `cryptography-50.0.2-cp311-abi3-manylinux_2_28_x86_64.whl` | VERIFIED | VERIFIED (publish identity) |
| `cffi-2.1.1-cp312-cp312-win_amd64.whl` | VERIFIED | NOT_VERIFIED (PyPI 404: no provenance) |
| `cffi-2.1.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | VERIFIED | NOT_VERIFIED (PyPI 404: no provenance) |
| `pycparser-3.12-py3-none-any.whl` | VERIFIED | NOT_VERIFIED (PyPI 404: no provenance) |

New evidence: preexisting gh 2.92.0 performed TUF-root-backed Sigstore verification for both cryptography wheels. DSSE, artifact digest, Fulcio certificate/identity, signed log timestamp and inclusion/checkpoint checks passed; independent RFC6962 path checks also passed. This authenticates a publishing workflow and its subject bytes, not reproducible builds or complete source-to-binary equivalence.

Existing full suite: 322 PASS, one mocked model-load warning; zero Python test network events. Ruff, pip check, offline blocked preflight, publication guards, whitespace, LFS and scientific verifiers passed. Normative CycloneDX 1.5 schema validation passed using existing Test-Json plus documented reference bundling; malformed control rejected. All 91 refs, 85 canonical PURLs and package/native hashes agree.

Scientific before/after: 127 protected files, 31 indexed evidence items, six manifests, 9,139 B3/B4 pairs, 80 metrics (atol 1e-12 / rtol 0), five LFS payloads and five preexisting local files PASS. Requirements/locks, installed distribution metadata/interpreter hashes and preserved refs are identical. Independent raw dataset hash and exact-bin vulnerability completeness remain NOT_AUDITED.

Remaining: three transitives lack signed provenance; libffi exact version unproven; incorporated notices and Rust build/runtime roles incomplete; no legal or installation approval. See the risk exception request. Existing parent audit CI was intentionally not run; this draft also uses [skip ci] because the existing workflow installs dependencies outside scope. Local checks are not CI. No tools or artifact packages were installed.

**DEPENDENCY_APPROVAL_REQUIRED** remains for installation/locks/runtime/adapter. **PILOT_BLOCKED**, all eight operational gates PENDING. No installation, wheel/native import or execution, inference, runtime change, dependency/lock update or merge occurred.
