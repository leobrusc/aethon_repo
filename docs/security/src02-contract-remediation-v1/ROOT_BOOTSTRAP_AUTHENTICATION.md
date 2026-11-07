# Root bootstrap authentication and revocation contract

This refines `ROOT_CAPABILITY_BOOTSTRAP.md` and `REVOCATION_AND_QUOTAS.md` without
creating credentials, a root, or a service.

## Versioned bootstrap receipt

A future receipt uses the exact type tag `aethon-root-bootstrap/v1`. The signed
payload is UTF-8 canonical JSON under RFC 8785/JCS, with duplicate object keys
rejected before canonicalization, bounded size/depth, no floating-point values,
and unknown security-relevant fields rejected. The detached signature covers
`AETHON_ROOT_BOOTSTRAP_V1\0 || canonical_payload` using the approved Ed25519
profile. The public key is resolved from an independently deployed
trust-anchor set pinned by the verifier, never from the receipt itself. This is
a verification profile only; in-process provider dependency approval remains
pending.

The signed payload includes at least:

- receipt ID, type tag and issuance/expiry timestamps in UTC RFC 3339 form;
- issuer key ID and trust-anchor-set ID (both checked against independent local
  policy); signature is detached from this payload;
- provisioner identity and approval evidence reference;
- exact root ID, volume/filesystem ID, mount/namespace identity and stable root
  object IDs for root plus policy-relevant ancestors;
- effective OS principal/token claims for the collector, privilege profile and
  immutable runtime identity;
- policy digest/epoch, run grant, manifest digest, budget, retention and allowed
  operations;
- revocation authority, revocation sequence/epoch and freshness evidence.

Receipt presence is not authenticity. Verification validates the signature
against the independently provisioned trust-anchor set, schema bounds, exact
platform identities, current policy epoch, expiration and revocation freshness.
The revocation response is separately authenticated and binds receipt ID, root
ID, issuer key ID, policy epoch, monotonic sequence, request nonce and response
expiry. It must explicitly say `ACTIVE`; missing, stale, revoked, duplicated,
malformed or replayed evidence fails closed.
The inventory cannot supply the receipt, key, root selector or pathname. Failure
creates no run and no capability. Trust-anchor rotation and revocation must have
an auditable overlap/recovery procedure; no static source-code secret is allowed.

## Reopen and revocation

After restart, the process reopens only through a trusted bootstrap anchor,
obtains a fresh receipt and checks that the acquired handles match the recorded
root/ancestor/volume/filesystem identities. A pathname alone is not identity or
authority. If identity cannot be established, reopen fails closed.

For Linux, principal binding includes effective UID/GID, supplementary groups,
capabilities, user-namespace identity, mount-namespace identity and approved
runtime measurement. For Windows it includes effective SID, token groups,
privileges, integrity level, logon/session identity and runtime measurement.
PID is supplemental telemetry only, never identity proof.

Revocation is an independently authenticated monotonic policy epoch. Check it at
bootstrap, lease acquisition, before dispatch, before publication and before
acknowledgment. Revocation racing a transaction blocks new dispatch/publication;
an already published but unacknowledged operation becomes unknown and is
reconciled. Revocation cannot guarantee instant cancellation of an operation
already in a kernel or an already-open handle; the host must stop the process at
a defined safe boundary. These details require native tests and an approved
issuer/revocation service before a RootCapability implementation. No live
issuer, trust root, verifier, receipt, service or credential is created here.
