# RootCapability review

## What is sound in the proposal

The PR #33 proposal correctly separates custodian/provisioner from operator and scientific approval, rejects inventory-selected roots, requires an actual held native handle, binds root/run/manifest/budget/retention and requires a new bootstrap after restart. It also correctly distinguishes object identity from access authority and freshness, and does not claim that the handle defeats administrator/kernel compromise.

## Gaps before bootstrap is testable

1. **Issuer authentication:** “versioned bootstrap receipt” has no canonical schema, signature/attestation format, trust anchor, key rotation/revocation, or independent verifier requirements. Receipt existence cannot authenticate its issuer.
2. **Principal identity:** bind an OS security principal and effective token/credentials, not a human label or PID alone. Define whether the process is constrained by UID/GID/capabilities and mount namespace (Linux) or SID/token privileges/integrity level (Windows), and how executable/runtime identity is verified.
3. **Root object profile:** specify the identity tuple and allowed filesystem types/volume serial handling, mount namespace identity/topology, owner and permission invariants, ancestor ownership/writability, and how each is checked against independently approved evidence.
4. **Reopen:** opening a trusted configured path after restart is not sufficient by itself. A fresh signed receipt must bind the expected object/volume/filesystem and current policy, and lookup must be relative to a trusted bootstrap anchor. If the original handle is gone and the identity cannot be authenticated without the path, fail closed.
5. **Revocation race:** periodic checks cannot instantly revoke an already-open descriptor/handle. Define maximum check interval and cancellation boundaries; an operation crossing revocation becomes unknown unless its commit state is reconciled. OS ACL changes do not themselves revoke all already-open handles.

## Verifiable pre/postconditions

**Pre:** authenticated provisioner evidence; approved non-admin collector principal; supported local filesystem and mount profile; root/ancestor handles acquired without following unsupported reparse/link paths; every identity/security field equals the receipt; current authorization, policy epoch, expiry and freshness witness valid; no untrusted inventory has been parsed.

**Post:** backend privately retains the exact root and ancestor handle set; a read-only audit record binds their stable IDs, filesystem/volume, principal, policy digest and grant; caller-visible API exposes no path or raw OS handle; no run state exists on any failed check. On restart, a newly opened handle must match a fresh receipt before any prior run is visible.

## Disposition

The RootCapability concept is suitable, but bootstrap trust evidence and process-principal/revocation contracts remain `REFINEMENT_REQUIRED`. It is not yet an executable acceptance test. No root was provisioned or opened by this review.
