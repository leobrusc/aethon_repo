# Ed25519 dependency proposal v1

**DEPENDENCY_APPROVAL_REQUIRED; PILOT_BLOCKED.** This is a proposal, not an
installation, dependency approval, working production verifier or pilot permission.
Parent #19: `7431d7b423bc6fc34d1db51c12794742481f8428`. Engineering baseline
`9ed55709add0fc45f63847a0394315863faa0876` and all previous branches are preserved.

## Exact candidate and compatibility

| Candidate | Role | Published Python constraint | Declared license |
| --- | --- | --- | --- |
| cryptography==50.0.2 | Ed25519 in-process provider | >=3.9, excluding 3.9.0/3.9.1 | Apache-2.0 OR BSD-3-Clause |
| cffi==2.1.1 | Active CPython transitive dependency | >=3.10 | MIT-0 |
| pycparser==3.12 | Active cffi transitive dependency | >=3.11 | BSD-3-Clause |

The constraints and selected wheel tags accommodate CPython 3.12; metadata checks
used the existing 64-bit 3.12.13 profile. They do not prove installation/import or
compatibility of the full research environment. No extras are proposed: the ssh
bcrypt extra and Python<3.11 typing-extensions marker are inactive. Runtime closure
is cryptography -> cffi -> pycparser for this CPython target.
[cryptography metadata](https://pypi.org/pypi/cryptography/50.0.2/json),
[cffi metadata](https://pypi.org/pypi/cffi/2.1.1/json),
[pycparser metadata](https://pypi.org/pypi/pycparser/3.12/json).

Targets are Windows x86-64 and Linux x86-64/glibc>=2.28. The cryptography cp311-abi3
wheels are eligible for CPython 3.12; cffi uses cp312-cp312. The universal pycparser
wheel is shared. ARM, PyPy, free-threaded CPython, musl and other wheel variants are
outside this proposed allowlist. Eligibility is a tag/metadata result only.
[Wheel tag specification](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/)

## Proposed artifact allowlist — published SHA-256 only

| Artifact | SHA-256 |
| --- | --- |
| cryptography-50.0.2-cp311-abi3-win_amd64.whl | `7afa5a6602a9f29af1f3a2965f831bae7c9d5d597b7cbb716d41ab3b7d89879c` |
| cryptography-50.0.2-cp311-abi3-manylinux_2_28_x86_64.whl | `4061c0079120205fb760c58acab6443e217307dcf05e3702cf970e0689972856` |
| cffi-2.1.1-cp312-cp312-win_amd64.whl | `f53e442b08449d42821fa4a4fba000095af9f62742a500f978a9f557ec44339a` |
| cffi-2.1.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl | `c1453022f490d2459a11819d83ad1d586e9ff65a12ac3e705ffebd46d3685dcf` |
| pycparser-3.12-py3-none-any.whl | `a076f3f489b39b43ed13563a1dafe42447445bec2e294154ec5c57fcdda4c85e` |

Source, upload time, sizes, markers and digest evidence are in
`ed25519-v1/artifacts.json`. Only public JSON metadata was retrieved. **No wheel or
sdist was downloaded, hashed locally, installed or executed.** These are verified
published digest values, not verified possession/integrity of downloaded bytes.
The five entries are a proposed allowlist, not an executable requirements/lock file.

## Approval boundary and remaining prerequisites

Specific future authorization must identify these three versions, five artifacts,
two target platforms and permitted acquisition/lock-generation/test work. Before
installation, verify actual bytes, package metadata/licenses, provenance and native
closure; resolve the missing transitive attestations or obtain an explicit reviewed
provenance exception. Approval must not silently waive unresolved evidence.

The upstream 50.0.2 changelog reports OpenSSL 4.0.3 in its wheels and PyO3 0.29.2
for the build. These are upstream declarations, not inspection of the selected
payloads. Actual native libraries, libffi details and complete build/OS SBOM remain
pending. [Versioned changelog](https://cryptography.io/en/50.0.2/changelog/)

`ed25519-v1/sbom.cdx.json` is a CycloneDX design-phase, metadata-only SBOM. It is
explicitly incomplete for installed/binary closure. Package/license fields are
publisher assertions until verified in the distributions. No signing authority,
reviewer, runtime provisioning or operational approval has been invented.

## Lock plan and rollback — not executed

Keep all seven current maintained locks, bootstrap and six historical manifests
unchanged. After approval, introduce a separate optional verifier profile and
platform-specific locks, with the existing pinned uv 0.13.7 tooling and binary-only,
hash-required resolution. Extend the resolver/profile allowlist explicitly; do not
assume it already supports a new profile. Preserve the exact artifact ledger and
review the complete resolution diff, not just these three package names.

Use new marked test environments; never upgrade historical or existing scientific
environments in place. Production requires a reviewed non-editable AETHON wheel and
immutable runtime deployment, separate from the current development installer.
Builds, offline wheel acquisition, lock regeneration and installation require
separate authorization; no command for them is run by this proposal.

Rollback selects the previous reviewed source/runtime image and restores the
fail-closed provider disposition. Preserve new locks, receipts, logs and environments
as evidence; do not delete/rewrite them or downgrade an existing environment in
place. Any changed code/runtime fingerprint requires fresh receipts and explicit
launch intent. SRC-02 and all eight gates remain blocking independently of SRC-01.
