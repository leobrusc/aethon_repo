# Evidence references

This design resolves gaps without repeating prior review narratives. Source documents were read at base HEAD `ada83b59ac2eb22ea7abc9acc31913b7fef6a220`.

| Evidence | Relevance |
|---|---|
| `SRC02_STORAGE_DECISION.md` (PR #19; architecture HEAD `7431d7b423bc6fc34d1db51c12794742481f8428`) | Selected isolated collector + complete Linux descriptor / Windows handle backends (C + A/B) |
| `docs/science/storage-capabilities-v1/STORAGE_CAPABILITY_API.md` | Current synthetic API operations, binding and logical limits |
| `docs/science/storage-capabilities-v1/NATIVE_BACKEND_REQUIREMENTS.md` | Existing platform and operational prerequisites |
| `docs/science/storage-capability-review-v1/NATIVE_INTERFACE_GAP_ANALYSIS.md` | Missing root capability, commit enum, restart/revocation, freshness and quotas |
| `docs/science/storage-capability-review-v1/STORAGE_REVIEW_DISPOSITION.md` | SCI-REV-01 origin/closure context and synthetic-only test scope |
| `docs/science/authorization-final-review-v1/SRC02_NATIVE_DESIGN_READINESS.md` | Remaining readiness items after AUTH-REV-01 closure |
| `docs/science/authorization-final-review-v1/AUTH_ISSUER_TRUST_BOUNDARY.md` | Application authorization boundary and explicit same-interpreter limits |
| `src/aethon/pilot_storage_backend.py` | Actual abstract API and synthetic volatility declarations |

External primitive references are linked in platform contracts. This specification does not claim those references alone validate an implementation.
