# Ed25519 runtime trust model

**DEPENDENCY_APPROVAL_REQUIRED; PILOT_BLOCKED.** Requirements below are proposed
controls, not claims that a runtime is provisioned, attested or enabled.

## Trust boundary

Trusted: independently distributed policy pin/public authorities, reviewed bootstrap,
approved immutable Python/application/native artifacts, OS and deployment authority.
Untrusted: receipts, referenced evidence bytes, prompts/responses, mutable CWD/user
site/import paths and package caches. Verification uses public keys only; collector
identity has no authority private keys and cannot approve its own run.

Protect against module/extension replacement and shadowing before provider loading,
and preserve the validated identity through operation with deployment immutability.
A second hash followed by an import from an attacker-writable directory is still
a check/use race. A hash measured by a compromised interpreter is not independent
attestation. Kernel/admin/interpreter compromise is explicitly outside assurance.

## Required bootstrap evidence, before importing the provider

| Control | Evidence / rejection condition |
| --- | --- |
| Artifact acquisition | Exact proposed wheel filename, independently pinned digest, publisher evidence, bytes hashed before install; reject sdists, alternate builds and resolver drift |
| Python identity | Exact approved distribution/patch, launcher AND real interpreter, ABI/cache tag, architecture, prefix/base-prefix, OS libraries and authoritative artifact receipt |
| Import paths | Reviewed immutable site-packages/application prefix only; reject unexpected sys.path, user site, CWD, .pth/import hooks, PYTHONPATH and alternate loaders |
| Installation mode | No editable install, mutable source checkout or user-writeable production prefix; wheel RECORD/direct_url support inventory but are not an independent root of trust |
| Native extension/provider | Actual imported module origin, extension digest, mapped images and actual crypto provider/version; compare against reviewed wheel/OS inventory |
| Runtime custody | Owner/DACL or UID/mode, ancestors/reparse points, deployment principal distinct from collector, no collector write/rename permission to executable/module/loader closure |
| Lifecycle | Fresh authorization on runtime/code change; deny missing, changed, unapproved or unverifiable runtime; no package installation or repair at launch |

Use isolated Python startup and an approved non-editable application. Python -I
removes CWD/user-site influence and ignores PYTHON* variables; it is useful hygiene,
not complete protection against writable prefixes, .pth hooks or a hostile host.
[Python isolated mode](https://docs.python.org/3.12/using/cmdline.html#cmdoption-I)

Existing dev/CI installers intentionally build an editable local project; that is
not the proposed production pattern. Do not change those workflows or existing
environments under the guise of a runtime attestation. Obtain approval for a new
isolated verifier/application profile and deployment procedure first.

Current audit inventory records Windows CPython 3.12.13/AMD64, cpython-312, actual
launcher and base-interpreter SHA-256, and absence of cryptography/cffi/pycparser
in the maintained Windows environment. Those observations identify the test
controller; they do not approve it for production. The previously observed WSL
distro cryptography and Python 3.14.4 are not adopted as pins or an approved provider.

## Loaded provider, custody and revocation

The future adapter may import only the approved cryptography provider after the
bootstrap boundary passes. Compare its declared version and file/module origins
with the installation receipt. Inspect actual native linkage and mapped images;
the upstream OpenSSL build statement is not proof of the running library. Avoid
version-probing APIs as a substitute for artifact identity. Full runtime/native
inspection remains NOT_AUDITED in this metadata-only phase.

Provision immutable prefix ownership/ACL under a separate trusted authority; the
collector runs restricted and cannot modify approval policy, runtime or deployment
receipt. OS filesystem/loader behavior and existing writable mappings require
platform tests. Public-key revocation and policy rotation must be independently
approved, versioned and run-bound; a valid old signature is not fresh consent.

Establish custody through the separately trusted deployment/controller before
loading the proposed provider. Do not use an unapproved library to certify its own
runtime as a circular bootstrap. A future environment observation must bind the
approved runtime receipt and imported provider/native artifact identities before
computing the subject/environment fingerprint; version strings alone are insufficient.

No subprocess, shell, PATH lookup, online key/provider retrieval, alternative crypto
algorithm, runtime auto-install or external OpenSSL fallback is permitted in the
adapter. Invalid/unavailable/unsupported providers never produce a verified gate.
Python network interception does not establish native egress isolation, and SRC-02
production storage remains independently blocked. A valid signature alone cannot
satisfy the eight gates or the separate signed operational launch intent.
