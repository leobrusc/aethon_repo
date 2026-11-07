# AUTH-REV-01 final independent review

## Disposition

**`AUTH_REV_01_CLOSURE_VALIDATED` within the application API boundary.** No
ordinary supported application call remains that can register a caller-created
authorization. The canonical `authorize()` flow still checks gates, launch
intent, operator/reviewer independence, constructs the exact object, and only
then records its identity and snapshot. The legitimate synthetic storage cycle
continues to pass in the cross-platform CI suite.

This is a closure of the API-level finding, not a claim against arbitrary code
inside the same interpreter. See `AUTH_ISSUER_TRUST_BOUNDARY.md`.

## Identity and tested source

- PR #30 finding/reproduction tree: `b8104f5a7e5970018b9c1e58b83e2eab0009b056`.
- PR #31 final HEAD reviewed: `8f851d2ad5ae7e886c58a1081f18c0d2dc284b55`.
- Implementation commit tested by CI: `803451e2045e73de103e8f4ddd8c2ea47d06a9a6`.
- `git diff --name-only 803451e..8f851d2` contains only the two PR #31 validation/adversarial reports. The reviewed implementation, tests, and source seal therefore match the tested implementation commit.
- CI `42398791189`: Linux SUCCESS (408 passed, one warning), Windows SUCCESS (408 passed, one warning), research/GPU audit SUCCESS; GPU inference `NOT_RUN`.

## Original reproduction

The unmodified PR #30 file `tests/review_private_issuer_registration.py` in its
original review worktree has SHA-256
`abe4426c99ae52332a5ae6799d55a74a8dafabda5784bff2d1d6cf099ebddc4a`.
Executed with PR #29 (`853d4fb95023461432397b4bab81803757209497`) as the project
root, it reported: distinct manual object, registered by private API,
capability created, one backend run, 120 slots. This confirms the original
finding.

The exact same script bytes executed with PR #31 as the project root fail at
import because `_AUTHORIZATION_ISSUER` is absent. The script stops before
creating its fixture, backend, capability, or run. The original file was not
rewritten. The PR #31 checkout's line-ending-normalized copy has a different
raw Windows file hash; the reproduction was deliberately executed from the
original PR #30 worktree, whose hash matches the specified value.

## Reviewed controls

- The former token, registration helper, writable module registry, and closure
  factory are absent from the initialized module namespace.
- The issuer's only registry write is nested in the closure retained by the
  module-level `authorize` entry point. It is reached after all gate, launch,
  and independence checks. There is no caller-supplied registration callback,
  bypass flag, or public state setter.
- `Authorization.check` delegates to the closure-held identity checker;
  `require_issued_authorization` enforces exact base type and invokes the base
  method non-virtually.
- `PrivateRunStore`, `StorageBackend.open_run`, the memory test backend, and
  `ReviewLedger` revalidate the same issued-object contract before use.
- Snapshot, exact object identity, subject binding, weak-reference identity,
  and expiry remain enforced. Owned-handle close only removes that backend's
  existing handle/lease; it cannot issue a new capability.
- `pilot_runtime.inspect_runtime` does not issue authority; collection remains
  blocked unless the existing independent inputs are supplied and verified.

## Findings

No ordinary API-equivalent bypass was demonstrated. No new AUTH-REV-01 finding
is opened. Closure introspection, module monkey-patching, and same-process
memory manipulation are explicitly outside this finding's scope rather than
being treated as API bypasses.

`SCI-REV-01` remains closed. No manifest, B0–B4, schedule, fingerprint, or
scientific result contract changed in PR #31.
