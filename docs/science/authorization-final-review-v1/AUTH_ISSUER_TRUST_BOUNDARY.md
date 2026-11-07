# Authorization issuer trust boundary

## In scope: application API misuse

The security claim covers ordinary application code using exported or directly
importable module names and documented entry points. It includes callers that
supply subclasses, clones, manually constructed authorization objects, copied
fields, mutated fields, a different subject, expired authorization, closed or
foreign capabilities, or an unissued authorization to storage/review APIs. It
also includes direct calls to any registration mechanism exposed as an ordinary
application API.

For these cases the module has one supported issuance entry point:
`authorize(authority, envelopes, subject, launch, technical)`. Before the
closure writes its identity registry it verifies all eight gate results, launch
intent, operator/reviewer identity and key independence, and the derived
expiration. The registry itself is closure-held and is not available as a
writable module-global mapping or a registration helper.

## Out of scope: arbitrary same-interpreter execution

The following are not claimed to be resisted by this Python-level design:

- Hostile introspection of `authorize.__closure__` or other live objects.
- Monkey-patching module/class globals or replacing the base checker.
- Arbitrary writes to process memory or execution of malicious Python/native
  code with the process's authority.
- Compromise of the interpreter, operating system, kernel, or host.

These capabilities exceed ordinary API use. Their existence does not reopen
AUTH-REV-01 under its stated application API boundary. If same-process hostile
code enters the operational threat model, an independently isolated issuer or
service with an authenticated protocol must be designed and reviewed.

## Residual authorization conditions

The closure proves only that the current process issued the exact object after
its configured checks. It is not a cryptographic signature or an independent
human authorization. Receipts, trust policy, deployment identity, storage
confinement, freshness, and operational gates retain their separate controls.
