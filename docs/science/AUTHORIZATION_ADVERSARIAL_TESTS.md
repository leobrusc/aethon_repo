# Authorization adversarial tests

The original vulnerable reproduction is retained byte-for-byte as `tests/historical/auth_rev_01_original_reproduction.py`; SHA-256: `D94F984C4EED8AB7EC58BC6EB7CE0CE2D1EE9BBBB4C26C5140E930DFD667CBD9`. It is not pytest-collected.

`tests/test_authorization_boundary.py` uses only synthetic `setup_run` evidence. It covers subclasses overriding `check()` with `None` and `True`, equal dataclass clones, manual base instances, modified fields, foreign subjects, and a positive 120-slot storage/reopen cycle with authorization emitted through `authorize()` using synthetic receipts. Existing tests also cover expiry, foreign/closed handles, cross-backend capabilities, and cleanup after expiry. No efficacy metrics or real inference are involved.

The captured vulnerable invocation was rerun before changes and reproduced capability issuance and one backend run. After changes, a standalone synthetic harness rejected the subclass at both the facade and backend with empty run/handle maps, and completed the positive 120-slot write/idempotent retry/journal/close/reopen/read cycle. These are direct synthetic checks, not pytest results.

Local focused pytest attempts occurred before the fixture-registration and implementation-seal fixes. The runner reported `ERROR` without a traceback and did not complete; a later process-creation attempt failed with Win32 error 5. Those attempts do not establish the status of the final code and are not counted as a final local pass. The approved PR CI run `42328753556` passed full Linux and Windows suites (407 passed on each), including these adversarial cases.
