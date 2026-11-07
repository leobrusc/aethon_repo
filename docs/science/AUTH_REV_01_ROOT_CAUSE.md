# AUTH-REV-01 — Root cause

PR #28 accepted any `Authorization` subclass at the facade/backend trust boundary and invoked `authorization.check(...)` through virtual dispatch. A caller-controlled subclass could override `check()` with a no-op while carrying plausible field values. The base issuance registry was never consulted. A synthetic reproduction used a valid v2 manifest with 120 slots; the unregistered subclass still received a capability and created one backend run.

The exact captured command is archived at `tests/historical/auth_rev_01_original_reproduction.py` (SHA-256 `D94F984C4EED8AB7EC58BC6EB7CE0CE2D1EE9BBBB4C26C5140E930DFD667CBD9`). It is evidence, not an active passing test. Output: `issued_registry_contains_object=false`, `capability_created=true`, `backend_run_count=1`, `scientific_slots=120`.

The remediation requires the exact base class, calls its verifier through a shared nonvirtual helper, and records a weak reference plus a digest snapshot of every authorization field at issuance. A subclass, dataclass clone, manual instance or mutated registered object cannot pass revalidation. The check is repeated before capability creation, at backend operations, and in review paths. The corresponding code-seal hashes in the collector config are updated to the exact remediated files; this creates a new config digest for future run identities without rewriting historical manifests.

The registry proves only that this process emitted the exact object. It is not a signature, durable authorization, hardware identity, or defense against hostile code in the same Python interpreter, monkeypatching, reflection, or host compromise.
