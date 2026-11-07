# Independent review — AUTH-REV-01

## Scope and identity

- PR #29 final HEAD: `853d4fb95023461432397b4bab81803757209497`.
- PR #28 vulnerable parent: `587ec791d0e88476b66f0fc37a817865f3ec70c9`.
- PR #27 SCI-REV-01 closure: `2034aade9b56bf76ff13f4816a5ff9de73a879a6`.
- Independent branch is based on the exact PR #29 HEAD. No production code, main, locks, environments, or existing PR branch was modified.
- CI run `42328753556` tested implementation commit `20662acb840dd6dd0a6c773dc1d4121a163c871c`; comparison to final HEAD shows only three report files changed afterward.

## Confirmed improvement

The original subclass override (`check()` returning `None`) reproduced on PR #28: `capability_created=true`, `backend_run_count=1`, `scientific_slots=120`. The exact same archived reproduction on PR #29 fails closed at `require_issued_authorization` with `PermissionError: Exact issued operational Authorization required`. Subclasses returning `True` and `None`, clones, manual instances, mutated snapshots, and subject mismatches are covered by the new tests; the full CI suite passed on Linux and Windows.

## Blocking residual in the emission boundary

`_AUTHORIZATION_ISSUER` and `_record_issued_authorization` are module-level importable names. A synthetic caller can copy every field from a valid fixture authorization into a fresh `Authorization`, import those two names, register the manual object, then pass exact-type, identity, snapshot, subject, and expiry checks. `tests/review_private_issuer_registration.py` reproduces this on PR #29: `manual_object_is_original=false`, `registered_by_private_api=true`, `capability_created=true`, `backend_run_count=1`, `slots=120`.

This is an in-process call to an underscore-prefixed internal API, not a hostile-kernel, native-code, or monkey-patching attack. It nevertheless violates the stated condition that only the `authorize()` flow after gates can register an object. Any caller able to construct and supply Python objects can import these module globals; the token is an ordinary object reference, not an independent or unforgeable authorization.

**Disposition: `REMEDIATION_REQUIRED`.** The subclass virtual-dispatch defect is corrected, but AUTH-REV-01 is not fully closed while the internal issuer can be invoked to mint registration for a manual object. This retains the existing finding; no new severity is assigned.

## Required follow-up

Remove the callable module-level registration route from the application boundary. Prefer a design where `authorize()` alone constructs and registers the object through an issuer that is not separately callable by application code; continue to treat arbitrary code executing in the same interpreter as outside Python-level guarantees. Add a regression reproducing the private-helper route and prove it cannot register a manually constructed object. Then rerun the exact-type, full lifecycle, and cross-platform suites and obtain another independent review.

## Other dispositions

- SCI-REV-01: no regression observed; independent manifest contract tests passed in CI.
- Native storage: no backend was implemented. Contract remains incomplete for production durability/freshness and interprocess isolation; `NATIVE_CONTRACT_REFINEMENT_REQUIRED`.
- Operational status remains `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED`; all eight gates `PENDING`.
