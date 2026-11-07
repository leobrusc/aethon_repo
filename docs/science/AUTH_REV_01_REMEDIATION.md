# AUTH-REV-01 remediation

Changed `pilot_governance.py` to bind the exact object and all field values at issuance, restrict registration to the gate-checked issuer path, and expose a shared nonvirtual validator. The facade, backend, test memory backend and review ledger now use exact-type and nonvirtual validation before granting or exercising authority. Added synthetic adversarial and positive-cycle tests, and preserved the original reproduction with its SHA-256.

No scientific manifest schema, B0–B4 definition, threshold, schedule, run fingerprint formula, receipt format, dependency, or lock changed. The fingerprint remains `fingerprint([subject, config, validated_rows, retention, order])`.

Code-level mitigation is implemented, but do not classify `AUTH_REV_01_REMEDIATED`: focused test execution did not produce a complete result. Require focused and full-suite CI plus independent review. `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, eight gates `PENDING`, and `PILOT_BLOCKED` remain.
