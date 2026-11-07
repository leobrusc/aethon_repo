# Authorization issuer threat model

## Protected assets

- Issuance of an application authorization after all required gate checks.
- Run capabilities, private run state, journal writes, and scientific review
  records bound to that authorization.
- Frozen manifest-v2 and B0–B4 protocol identity.

## Trust boundaries

The application API boundary rejects ordinary callers supplying subclasses,
clones, manually constructed instances, or snapshots that differ from the
issued object. The canonical `authorize()` flow performs the gate, launch
intent, operator/reviewer separation, and expiration checks before its closure
records an object identity and immutable snapshot.

The interpreter and process memory remain trusted. A caller with arbitrary code
execution in the same Python interpreter may inspect closures, replace module
globals, monkey-patch methods, or otherwise subvert these checks. This refactor
does not claim to defend that threat. If same-process hostile code is in scope,
the issuer and storage boundary require an independently isolated process or
service and a separately reviewed authenticated protocol.

## Residual operational boundary

This does not authorize storage backends, change the eight gates, validate their
real-world evidence, or permit a pilot. Native storage, dependency approval,
host isolation, and all operational approvals remain pending. The memory backend
is test-only.
