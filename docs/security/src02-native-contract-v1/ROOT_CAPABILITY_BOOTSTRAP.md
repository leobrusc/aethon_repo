# Root capability bootstrap contract

## Issuer and provisioning

An identified storage custodian/provisioner, independent of the collector operator and scientific approvers, provisions a private root under a separately approved OS identity. The trust policy, allowed volume/filesystem, expected owner, ancestor chain, ACL/mode, mount policy, quota, retention deadline, supported OS build, and root identity are recorded in a versioned bootstrap receipt. Human approval and receipt verification are distinct: receipt presence does not itself authorize execution.

`RootCapability` is an opaque backend-owned object issued only by a trusted bootstrap component after it opens and verifies the actual root object. Its binding includes a random root instance ID, stable OS object identity, volume/device and filesystem identity, owner/security descriptor policy, policy digest, custodian identity, approved subject scope, quota, retention, issue/expiry, revocation epoch, supported platform profile and freshness-witness identity. It contains or refers to retained native handles; it is not reconstructed from a pathname after restart.

The untrusted inventory, manifest, run ID, caller path, and `Authorization` cannot create or select this object. `open_run` must require both the already-issued application authorization and a backend-held RootCapability. A path is allowed only as bootstrap input from trusted provisioning configuration; it is opened before untrusted inventory processing, checked against the independent receipt, and then discarded as an authority source.

## Bootstrap state transitions

`UNPROVISIONED → PROVISIONING → VERIFIED_HELD → RUN_BOUND → CLOSED/REVOKED`.

- `PROVISIONING → VERIFIED_HELD` only after identity, owner, ancestry, volume/filesystem, mount and permissions checks succeed on the opened object and its required ancestors.
- Any unsupported primitive, unexpected link/reparse point, mount change, identity mismatch, policy mismatch, failed witness, or ambiguous open enters `REJECTED`; no run state is created.
- `VERIFIED_HELD → RUN_BOUND` requires exact subject, run fingerprint, immutable manifest digest, authorization issuer evidence, resource budget, retention, expiry and witness policy binding.
- After restart, bootstrap creates a *new* capability from a fresh authenticated bootstrap receipt and newly acquired OS handle, then checks revocation and external freshness before reopening. It never trusts serialized Python objects or stale pathnames.
- Revocation invalidates future operations; active operations are cancelled at the next safe boundary, their native handles are closed, and a possibly in-flight commit is reported `COMMIT_UNKNOWN` until reconciled.

## Preconditions / postconditions

Precondition: trusted provisioner and trust root are available; the OS process identity is the approved non-admin collector identity; root and ancestors are on an explicitly supported local filesystem; untrusted inventory has not been processed; independent bootstrap policy and retention receipt are valid.

Postcondition on success: the backend owns a handle-bound capability with immutable identity/policy snapshot; caller cannot provide alternate paths; every subsequent operation is scoped to that root object and grant. No storage, root directory, ACL, or service is provisioned by this specification.

Root identity is not access authority by itself. Access authority derives from the held handle plus OS access checks and the independently approved grant. Object identity, permission state, and freshness are separately checked properties.

## Phase 7C amendment — authenticated issuer receipt

The minimum receipt fields, external trust-anchor requirement, effective OS
principal binding, root/volume/mount identities, policy epoch, expiry and
revocation freshness are specified in
`docs/security/src02-contract-remediation-v1/ROOT_BOOTSTRAP_AUTHENTICATION.md`.
Receipt presence or a caller-provided pathname is not authority. A future
verifier must authenticate the issuer independently, reject stale/revoked
epochs, and acquire handles whose exact identities match the receipt before a
run becomes visible. Revocation racing commit blocks new work; an uncertain
already-started transaction remains unknown and requires reconciliation.

This is a versioned contract only. No root, issuer key, trust anchor, service,
revocation source or RootCapability was created or validated.
