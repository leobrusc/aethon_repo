# SRC-01 verifier architecture decision

Target: **B, in-process Ed25519 through an approved cryptographic library**.
Current disposition: **D, fail closed**. No dependency, lock, verifier or production
authorization behavior changes in this review.

## Comparison of all four alternatives

| Option | Boundary and integrity | TOCTOU / dependency chain | Version, provenance and tests | Residual risk / cost |
| --- | --- | --- | --- | --- |
| A native object-bound execution | Trusted bootstrap, native launcher, executable object, OS loader | Linux descriptor execution binds a main image, not automatically interpreter/DSOs; Windows needs separately proven image/share/ancestor/DLL behavior | Pin launcher/image/loader closure; SBOM per OS/build; race barriers, mapped-writer/DLL substitution and failure injection | Highest implementation burden; platform-specific ABI and lifecycle; retain denial without proof |
| B in-process **target** | Approved Python runtime, crypto extension and OS; public verification keys only | No receipt-time external exec/path fallback; immutable imports/runtime deployment are required | Pin exact Python/package/native-wheel artifacts and transitive SBOM; known-answer, invalid-signature and packaging tests | Native crypto/interpreter compromise remains possible; dependency approval required |
| C isolated verifier service | Service principal/image, authenticated channel and independent peer trust | Moves image/dependency integrity to service deployment; does not eliminate it | Pin server/client protocol and image, include nonce/payload/policy/run binding; substitution/replay/timeout tests | More RPC/authentication/availability and operations; not selected for initial local boundary |
| D denial **current** | Existing inspected code and trusted OS/Python | Never executes the mutable verifier path | Current identity/drift/no-fallback tests; exact code seal | Safe loss of availability; no usable production verification |

Linux `execveat` supports descriptor-relative execution, including an empty-path
mode; this is narrower than proving every executable dependency. This distinction
is the basis for rejecting a claim that a main-file descriptor alone resolves
SRC-01. [Linux execveat documentation](https://man7.org/linux/man-pages/man2/execveat.2.html)

On Windows, documented CreateFile sharing controls can constrain conflicting
opens, but a protected file handle is not itself a documented pathless CreateProcess
interface. Any proposed native launcher must prove loader resolution, preexisting
mapped writers and every mutable ancestor/dependency; this review does not supply
that proof. [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)

## Selected B contract

Use the established Ed25519 verification API, not a handwritten implementation.
The official API distinguishes invalid signatures and unsupported algorithms; both
must lead to denial. Restrict keys to Ed25519, canonicalize the same receipt bytes,
require the exact public-key and signature encoding/length, reject other algorithms,
and preserve distinct-key quorum, roles, subject, issue/expiry and independent
policy-pin checks. A successful signature is not an authorization decision.
[Ed25519 API](https://cryptography.io/en/stable/hazmat/primitives/asymmetric/ed25519/)

Proposed interface, not implemented:

```text
verify_ed25519(public_key_bytes, canonical_payload_bytes, signature_bytes)
    -> VALID | INVALID | UNSUPPORTED
```

No subprocess, PATH lookup, shell, DLL override, auto-install, online key lookup,
algorithm downgrade or alternate executable fallback is allowed. Import/load
failure is blocking. The verifier must have no approval-signing private key.
Signed launch intent and all eight gates remain distinct higher-level decisions.

Deployment must use a versioned, read-only application environment under a principal
distinct from the restricted collector. Use isolated Python startup, reviewed
module paths and no editable/user-site/CWD import substitution. Validate installed
artifacts from an independent bootstrap trust root before entering the adversarial
window; checking RECORD files controlled by an attacker is insufficient. A mutable
Python environment does not become secure merely because verification is in-process.

Pin exact wheel/source versions, Python ABI, OS/architecture artifact hashes and
installation provenance after specific approval. The library publishes statically
linked wheels for supported platforms; that can reduce external OpenSSL lookup,
but the actual selected wheel and native closure must be inspected. Do not infer
that every distro/source build has the same linkage.
[Library installation and linkage documentation](https://cryptography.io/en/stable/installation/)

SBOM must include Python, crypto package/extension, bundled OpenSSL or other crypto
provider, optional native binding packages, runtime/OS libraries in the declared
TCB, build tools/provenance, licenses and advisory coverage limits. Generate an
environment receipt binding the actual imported module paths/digests to the run
subject. This receipt supplements immutable deployment, not substitutes for it.
No package version is selected or installed in this phase; consulted documentation
is an API reference, not approval of its current release.

## C service contract if reconsidered

Local IPC must authenticate the expected principal and actual reviewed service,
not just a pathname/PID or `valid: true` JSON. Bind protocol version, purpose,
request nonce, payload digest, policy digest, run/subject and expiry in the response.
Reject substitution, replay, cross-run use, oversized messages and timeouts; do not
cache validity across fingerprints. OS peer credentials require native evidence;
remote deployment would additionally need an approved authenticated transport and
key rotation policy. Authenticating a service must not circularly depend on an
unauthenticated response from that same service.

## Evidence and release boundary

PR #18 removes pathname subprocess invocation and unconditionally denies execution.
Its pin/ancestor/dependency rechecks are diagnostic, not TOCTOU closure. Historical
tests demonstrate the old acceptance; current tests require denial even for an
unchanged tool. Genuine Ed25519 validity/tamper tests use an existing local OpenSSL
only in controlled synthetic test code, never as a newly enabled production backend.

Acceptance requires verified B packaging on Windows and Linux, valid/invalid
vectors, role/alias/replay regression, environment replacement rejection and
independent source review. Kernel/admin/interpreter compromise remains outside
this guarantee; exact native binary vulnerability coverage stays NOT_AUDITED unless
independently established. Production remains blocked pending all of the above.
