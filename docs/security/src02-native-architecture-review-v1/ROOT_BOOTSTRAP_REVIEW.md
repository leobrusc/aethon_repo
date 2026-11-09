# ADR-001 — issuer, root and revocation independent review

Disposition: `OPEN_DECISION` (ARCH-REV-01).

## Strengths

The proposal correctly excludes user-controlled inventory from root selection, requires a held descriptor and owner/ancestor/mount validation, and separates the application Authorization token from the root custodian. It also explicitly rejects stale receipts, self-issued trust keys and pathname-only restarts.

## Missing executable trust contract

The proposal does not name an independently governed issuer identity, on-host verifier trust-anchor distribution/rotation authority, authorized collector UID/GID/capability profile, or a concrete revocation endpoint. No versioned launch-grant artifact is externally authenticated. The `bound_witness_required` field in the abstract model is initialized from a Python constructor; it is **not** a signed, independent policy. A holder of Python interpreter authority may forge both fields.

Required sign-off must resolve issuance and revocation authority separation, cryptographic receipt canonicalization, replay nonce/time bounds, actual root/ancestor mount identities, rebootstrap after restart, trust-anchor rollover and revocation failure behavior, and the allowed scope of the collector principal.

## Adversarial acceptance criteria

Reject forged signature, unpinned signer, duplicate JSON keys, changed principal UID/GID/groups/capabilities, changed root mount/object identity, symlink ancestor substitutions, expired policy, replayed/stale revocation, new run manifest after receipt, and trust-anchor failure. No fallback to a path-based root or local self-issued receipt. If an already-started effect is uncertain, emit `COMMIT_UNKNOWN` rather than retry inference.

These are **review requirements**, not native test results or key provisioning. No approval is issued.
