# Authorization issuer refactor

The supported issuance flow remains `authorize(authority, envelopes, subject,
launch, technical)`. It checks all eight gate results, the signed launch intent,
identity independence, expiration, reviewer assignment, evaluator keys, and
storage retention claims before registering the resulting exact `Authorization`
object.

The former module-level `_AUTHORIZATION_ISSUER` token and
`_record_issued_authorization()` writer were removed. The issuance registry is
held in closures created for the module's authorization API; an ordinary import
of a module-global mutable registry or registration helper is no longer
available. `_make_authorization_api()` creates an isolated API/registry pair;
only the module's canonical checker is used by `Authorization.check`, so a
separately created pair cannot issue an object accepted by application entry
points.

Consumers retain their existing interface: `require_issued_authorization()`
performs exact-type validation and calls the base-class check non-virtually.
Storage facade/backend and `ReviewLedger` therefore continue to reject
subclasses, clones, manually constructed objects, field mutation, subject drift,
and expiration. Closing remains limited to resources owned by the original
capability and does not issue authority.

No gate, receipt signature, quorum, manifest-v2 field, B0–B4 definition, or
fingerprint formula changed. The only scientific configuration edit is the
implementation SHA allowlist in `configs/science/collector_v1.json`: the prior
governance source digest was replaced by the digest of the refactored module so
the existing runtime integrity check recognizes the reviewed implementation.
No generation, model, template, baseline, or protocol field was changed.
