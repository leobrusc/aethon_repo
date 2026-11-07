# AUTH-REV-01 — issuer route root cause

## Finding

PR #30 demonstrated that PR #29 exported both `_AUTHORIZATION_ISSUER` and
`_record_issued_authorization` as module attributes. Application code able to
import those names could register a manually constructed `Authorization`
instance without passing through `authorize()`.

## Historical reproduction

The unchanged reproduction is `tests/review_private_issuer_registration.py`.
Its SHA-256 is
`abe4426c99ae52332a5ae6799d55a74a8dafabda5784bff2d1d6cf099ebddc4a`.
Executed with PR #29 (`853d4fb95023461432397b4bab81803757209497`) as the current
project root, it reported a distinct manual object, successful registration,
capability creation, one backend run, and 120 slots. This is evidence of the
vulnerability, not an acceptance test.

## Remediation

The writable registry is now captured by the authorization API's closure. The
only registry write is inside the issuer closure after `verify_gates`, launch
intent verification, operator/reviewer independence checks, and authorization
construction. The old token and registration function no longer exist as
module attributes. The exact-type, object-identity, weak-reference, complete
snapshot, subject, and expiry checks remain in the authorization checker.

This is an application API boundary. Python introspection, module monkey-patching,
memory modification, and arbitrary code in the same interpreter remain outside
the guarantee. No cryptographic or OS isolation claim is made.
