# Ed25519 supply-chain review

**DEPENDENCY_APPROVAL_REQUIRED; PILOT_BLOCKED.** Metadata collection only, dated
2026-11-05. No artifact acquisition/installation or dependency/lock modification.

## Evidence classification

| Evidence | Actual result | Limit |
| --- | --- | --- |
| PyPI release JSON | Exact versions, requirements, filenames, non-yanked status, sizes and SHA-256 recorded | Repository metadata is not inspection of wheel bytes |
| ABI/platform eligibility | PASS for proposed CPython 3.12 x86-64 targets | Imports/linkage/full-environment compatibility NOT_RUN |
| PyPI vulnerability fields | Empty for all three selected versions | Feed coverage/time limits; not a security approval |
| OSV package/version queries | HTTP 200, no vulnerability IDs returned for each candidate | Ecosystem/version matching only; no native binary catalog assurance |
| cryptography provenance | Two HTTP 200 bundles, publisher claim pyca/cryptography / pypi-publish.yml | Attestation signature, identity policy, log proof and subject binding NOT_AUDITED |
| cffi/pycparser provenance | Three HTTP 404 responses for the selected filenames | No bundles available through queried endpoint; not proof of a malicious package |
| Native closure and complete SBOM | Upstream declarations plus explicit unknown components | Wheel extraction, linked-library inventory, licenses and loaded image identity NOT_AUDITED |

Machine evidence is in `ed25519-v1/artifacts.json`, `metadata-audits.json` and
`sbom.cdx.json`. Original metadata response hashes and exact query logic are retained
with validation evidence. No credentials or real research data enter these queries.

The PyPI Integrity API supplies provenance documents; obtaining one is different
from cryptographically verifying it and authorizing its publisher identity.
Require the exact wheel digest/name, expected repository/workflow and approved
identity policy, certificate chain and transparency evidence. Do not accept a
publisher field or TLS response as sufficient independent artifact provenance.
[Integrity API](https://docs.pypi.org/api/integrity/)

The three OSV queries used exact PyPI package/version requests, not names alone.
Raw responses were empty JSON objects; request package versions and response hashes
are tied to this proposal. Requery before any approval/acquisition because feeds
and advisory ranges change. [OSV query contract](https://google.github.io/osv.dev/post-v1-query/)

The reviewed upstream PKCS#7 advisory identifies a fix in 50.0.0, preceding the
50.0.2 candidate. Its prose and machine affected ranges must not be confused with
an assertion that all cryptography or OpenSSL functionality is safe. This proposed
adapter exposes only Ed25519 verification, but package-level issues still require
review rather than blanket suppression.
[Upstream advisory](https://github.com/pyca/cryptography/security/advisories/GHSA-g6cj-pr64-35w5)

## Native and build bill of materials

| Component | Proposal evidence | Required future verification |
| --- | --- | --- |
| cryptography Python/Rust extension | 50.0.2 wheel identities; Apache-2.0 OR BSD-3-Clause metadata | Exact installed files/extension hashes; licenses inside wheel; build identity |
| cffi native extension | 2.1.1 cp312 wheel identities; MIT-0 metadata | Extension and libffi linkage/version/license; compiler/runtime dependencies |
| pycparser | 3.12 universal wheel; BSD-3-Clause metadata | Wheel contents, license and version/API compatibility |
| OpenSSL | 4.0.3 reported for cryptography wheels | Actual binary/provider version, linkage, provenance, embedded notices and advisories |
| PyO3 / Rust / maturin / build tooling | Changelog reports PyO3 0.29.2; tagged pyproject declares maturin/build requirements | Exact build resolution/Cargo/native closure and reproducibility evidence |
| libffi and OS/runtime libraries | Explicit incomplete components in design SBOM | Versions, hashes/OS package identities, license notices and trusted loader boundary |
| CPython | Existing audit profile 3.12.13; local launcher/base hashes observed | Approved production distribution/patch, complete runtime receipt and native library inventory |

Source declaration and changelog are supporting provenance, not reconstructed
binary content. [Tagged build manifest](https://github.com/pyca/cryptography/blob/50.0.2/pyproject.toml),
[changelog](https://cryptography.io/en/50.0.2/changelog/).

The design SBOM includes proposed artifacts with publisher digests and dependency
edges, declared OpenSSL, unresolved libffi and the target Python runtime. Its
properties mark PROPOSED_NOT_INSTALLED and incomplete native closure. It must not be
used as an attestation of a deployed environment. A complete installed SBOM and
fresh advisory review are installation acceptance requirements.
[CycloneDX 1.6 reference](https://cyclonedx.org/docs/1.6/json/)

## Approval blockers and residuals

Pending: permission to obtain artifacts; independent checksum/attestation verification;
missing transitives' provenance or reviewed exception; binary/native/license audit;
approved production Python/OS patch and immutable image; separate lock resolution;
actual Windows/Linux tests. The current development Python version is a compatibility
reference, not a claim that its production patch/security review is current.

No dependency attestation can protect against a compromised kernel/interpreter or
an authority controlling both policy and its independent pin. Exact binary advisory
coverage remains NOT_AUDITED; absence from PyPI/OSV does not cover undisclosed
issues, all bundled C/Rust libraries or build tampering. Preserve the prior
NOT_AUDITED raw-dataset and PyTorch-binary states. All gates remain PENDING.
