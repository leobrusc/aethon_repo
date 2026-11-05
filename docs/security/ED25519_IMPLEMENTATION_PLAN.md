# Ed25519 implementable contract and approval plan

**DEPENDENCY_APPROVAL_REQUIRED; PILOT_BLOCKED.** No production adapter is implemented
or selected at runtime in this phase. Existing OpenSSLVerifier remains fail closed.

## Exact interface

```text
verify_ed25519(public_key_bytes, canonical_payload_bytes, signature_bytes)
    -> "VALID" | "INVALID" | "UNSUPPORTED"
```

Accept immutable bytes only. Preserve existing public-key file/policy hashes and
receipt formats: public keys are a single PEM SubjectPublicKeyInfo Ed25519 key,
whose decoded DER is the 44-byte RFC8410 encoding with prefix
`302a300506032b6570032100` and a 32-byte public key. Preserve harmless PEM whitespace
normalization for key identity. Reject other algorithms, multiple keys, trailing
DER, raw-key format ambiguity and malformed encodings. Do not broaden key acceptance
merely because a general-purpose serialization loader supports more algorithms.

Require exactly 64 signature bytes. Verify the exact supplied message bytes;
do not JSON-parse/re-serialize, normalize Unicode, strip whitespace, prehash or
switch to Ed25519ph/ctx. Receipt callers already supply `pilot_governance.canonical`:
sorted keys, compact JSON, UTF-8/ensure_ascii=False and allow_nan=False. Algorithm
test vectors may use arbitrary bytes, including the empty message; this does not
make noncanonical receipt serialization acceptable at the governance layer.

Input/encoding/signature failure returns INVALID. An absent, unapproved, changed,
unsupported or unavailable provider/runtime returns UNSUPPORTED and blocks the
gate. Unexpected provider failures must deny and surface a sanitized operational
diagnostic, never become VALID or trigger fallback. The adapter has no private
keys, signing function, approved flag, auto-install or external invocation.

After approved runtime loading, convert the narrowly validated key to the library's
Ed25519 public-key type and call its verification API. Map only successful completion
to VALID, InvalidSignature to INVALID and unavailable/unsupported runtime/provider
to UNSUPPORTED. Do not implement curve arithmetic in AETHON.
[Versioned Ed25519 API](https://cryptography.io/en/50.0.2/hazmat/primitives/asymmetric/ed25519/)

## Preserve the existing bool governance seam

ReceiptAuthority currently expects a bool-returning verifier. A future explicit
bridge must compare statuses; it must **not** return nonempty status strings directly,
because INVALID and UNSUPPORTED strings are truthy in Python:

```text
VALID       -> True
INVALID     -> False
UNSUPPORTED -> blocking provider-unavailable error / pending gate
unknown result -> blocking contract error
```

Do not change signed payload formats, canonicalization, distinct-key quorum,
role/gate matching, disposition, subject/run fingerprint, evidence hashes,
issue/expiry, independent policy pin or separate signed launch intent. Distinguish
authenticated author statements from technical checks, scientific review and
operational authorization. Retain all eight real gates PENDING in this phase.

The future environment observation must include approved provider/runtime receipt
and artifact identities before computing the environment/subject fingerprint.
Receipt wire formats remain unchanged, but changed code/runtime fingerprints require
new receipts; never reuse approvals issued for the pre-provider environment.

## Work sequence after specific authorization

1. Obtain and independently verify the five exact artifacts and source/native/
   provenance/license evidence; resolve missing transitive attestations or explicit
   exception. Do not install just because metadata matches.
2. Approve a separate production runtime/profile and Python patch; add new optional
   profile inputs and Windows/Linux hashed locks with pinned uv tooling. Review
   resolution drift; preserve all old/historical inputs, locks and environments.
3. Implement the adapter and strict bool bridge under a new isolated branch, with
   no automatic factory switch or bypass flags. Add approved runtime-attestation
   integration and use a reviewed non-editable application image.
4. Run prepared RFC8032 positives and wrong-key/message/signature/algorithm negatives
   against the actual provider on each approved system; add runtime/import/native
   replacement tests and governance replay/role/quorum regressions.
5. Produce installed/binary SBOM and runtime receipts, rerun scientific preservation,
   obtain independent review and only then consider selecting the adapter. SRC-02,
   eight gates and explicit operational consent remain separate blockers.

Documentation/proposal commits are separate from any later authorized adapter or
dependency implementation commits. No full-environment resolution, wheel download,
install, package import or runtime change is performed now. Existing hashes of the
SRC-01 historical reproductions and their logs remain untouched.

Rollback returns to the reviewed disabled provider and previous immutable runtime
image, preserving rejected/new artifacts and evidence. Never force a downgrade,
rewrite historical locks or silently accept old receipts under a changed runtime.
