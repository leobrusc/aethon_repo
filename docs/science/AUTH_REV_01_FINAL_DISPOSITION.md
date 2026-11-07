# AUTH-REV-01 final disposition

## Classification

**`REMEDIATION_REQUIRED`** — the original ordinary subclass `check()` override is rejected, but the issuance boundary remains bypassable by importing the module-level `_AUTHORIZATION_ISSUER` and `_record_issued_authorization` and registering a manually constructed base instance. A synthetic reproduction created a capability and backend run. This contradicts the requirement that `authorize()` after gate verification be the only issuer.

The private-issuer route is an in-process implementation API call and is not evidence of resistance to a compromised interpreter. Its significance is that the supposedly internal issuer is a callable module-global route available to the same application-level code that can supply an authorization object.

## Separate native contract result

**`NATIVE_CONTRACT_REFINEMENT_REQUIRED`** — root capability bootstrap, durable commit-unknown semantics, cross-process leases, rollback/freshness witness, revocation, resource enforcement, and post-collection review persistence remain unspecified or unvalidated.

## Required action

Remove the directly callable issuer/token registration route from ordinary application access, add a regression for attempted private registration, rerun cross-platform full suites, and request independent re-review. Do not begin Linux native storage until that review and the native-contract requirements are complete.

Keep `SCI-REV-01` closed; this review found no manifest-validation regression. Keep `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, all eight gates `PENDING`, and `PILOT_BLOCKED`.
