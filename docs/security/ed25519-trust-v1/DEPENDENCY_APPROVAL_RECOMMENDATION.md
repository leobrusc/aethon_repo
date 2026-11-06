# Dependency approval recommendation

**EXCEPTION_REVIEW_REQUIRED**. Integrity VERIFIED; aggregate provenance PARTIALLY_VERIFIED (cryptography publishing identity VERIFIED; cffi/pycparser NOT_VERIFIED); native COVERAGE_PARTIAL. No installation, lock update, runtime choice or adapter implementation is approved.

Before an approval request can be accepted: accountable security/governance owners must explicitly decide the three exact-artifact provenance exceptions, obtain/assess libffi source/build identity and notices, resolve third-party license closure, distinguish Rust build/runtime components and document the incomplete native/OS advisory coverage. An unsigned exact-hash exception is a separate risk acceptance, not equivalent cryptographic provenance. Consider requesting missing publisher attestations/SBOMs; do not substitute new versions or rebuild/download artifacts under this authorization.

If any proposed exception is rejected, the affected dependency remains blocked. If accepted later, approval must still name exact hashes/platforms, independently reviewed runtime/import-path controls, offline installation procedure, rollback and review expiration. SRC-01 production implementation and native storage controls require their own review. Authentication of the publishing workflow does not establish a trusted builder, reproducible binary or safety against a compromised upstream maintainer/host.

Eight gates remain PENDING: independent_inventory, semantic_review, rubric_review, reviewer_assignment, private_storage, model_assets, hardware_check, execution_authorization. No reviewer identities, signatures, expiry or approval decisions are invented. Recommended next step is independent review of this draft and the pending exception request; do not install or run a pilot.

**DEPENDENCY_APPROVAL_REQUIRED** remains for installation/locks/runtime/adapter. **PILOT_BLOCKED**, all eight operational gates PENDING. No installation, wheel/native import or execution, inference, runtime change, dependency/lock update or merge occurred.
