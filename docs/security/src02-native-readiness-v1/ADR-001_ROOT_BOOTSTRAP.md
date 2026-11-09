# ADR-001 — trusted bootstrap and RootCapability issuance

Status: **PROPOSED_NOT_APPROVED**. This ADR is non-authorizing; no root, keys, issuer, credentials, or trust anchors are created.

## Problem and threat boundary
An untrusted manifest, caller path, run identifier, in-process Authorization token, or Python object constructor must not select a filesystem root. The existing SRC-02 specification requires an independently approved root capability bound to a retained native descriptor, with root/ancestor/volume/OS principal identities checked against an authenticated receipt. The abstract witness-policy binding in PR #40 derives from a synthetic constructor and is **not** a cryptographic launch grant.

## Proposed choice
Adopt an independent provisioner/issuer and a bounded `aethon-root-bootstrap/v1` receipt, canonicalized under RFC 8785, signature over `AETHON_ROOT_BOOTSTRAP_V1\0 || payload`, and verification against a trust-anchor set provisioned **outside** the collector. Ed25519 is a specified candidate; it remains `DEPENDENCY_APPROVAL_REQUIRED` and no code/dependency approval is implied.

Receipt fields: issuer key ID, approval evidence, provisioner ID, unique root/grant IDs, collector effective principal, user/mount namespace identity, root and ancestor device/inode/mount identity, filesystem profile ID, allowed run and manifest digest, policy digest/epoch, witness policy/identity, quotas, retention, issue/expiry, revocation sequence and authenticated nonce-bound revocation response. Reject duplicate keys, unknown security-relevant fields, noncanonical bytes, stale/replayed receipts, clock or revocation uncertainty.

## Issuance and restart state relation
`UNPROVISIONED -> RECEIPT_VERIFIED -> ROOT_OPENED -> IDENTITY_ATTESTED -> HELD -> RUN_BOUND`. Each arrow is guarded by independently authenticated evidence. Receipt verification **precedes** acquiring a capability for an untrusted run. Failures produce `REJECTED`, never a less constrained fallback. Bootstrap must check process effective UID/GID/supplementary groups/capabilities, relevant namespaces, approved ancestors and current revocation; the collector cannot issue its own receipt.

Reboot/restart requires a new independently obtained and authenticated receipt, reopened approved handles, exact root identity/namespace/volume and grant comparison, fresh revocation, and independent witness checkpoint verification before accepting any run. A pathname may be used only by the trusted provisioner to find its pre-approved root; it is never sufficient as root identity or authority. The platform owner must define what happens on inode reuse and mount replacement.

## Required approval/evidence
- Root custodian and independently authorized grant issuer nominated and reviewed.
- Trust anchor, key custody, rotation, revocation and principal policy approved.
- Offline bad-signature/bad-policy/replayed-epoch/altered-root/foreign-principal tests designed.
- Required negative-native test IDs: T01–T05, T12 and T14.
- Independent security review and exact approver/authorization evidence.
All remain **PENDING**. A receipt example or test fixture is not an operational credential.

## Residual
Compromised collector interpreter, root issuer, kernel, or administrator lie outside the local filesystem safety claim. Native conformance remains NOT_VALIDATED. See `ROOT_CAPABILITY_BOOTSTRAP.md` and `ROOT_BOOTSTRAP_AUTHENTICATION.md`.
