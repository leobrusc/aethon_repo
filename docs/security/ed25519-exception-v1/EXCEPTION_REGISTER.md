# Exception register — Phase 5D

**EVIDENCE_GAPS_REMAIN**. Three artifact-specific provenance proposals and two distinct native-identity proposals are complete as review forms, but material libffi/license/build evidence remains insufficient for acceptance. Integrity of all five wheels and all 57 parent evidence hashes passed. No invalid/adulterated attestation was observed; three artifacts have no provenance published in the queried PyPI service at the Phase5C timestamp. Old reports and quarantined bytes are preserved.

| ID | Exact artifact scope | Proposed recommendation | Effective decision | Owner / independent approval |
|---|---|---|---|---|
| PROV-CFFI-WIN | `cffi-2.1.1-cp312-cp312-win_amd64.whl` | ADDITIONAL_EVIDENCE_REQUIRED | PENDING | PENDING |
| PROV-CFFI-LINUX | `cffi-2.1.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | ADDITIONAL_EVIDENCE_REQUIRED | PENDING | PENDING |
| PROV-PYCPARSER | `pycparser-3.12-py3-none-any.whl` | ADDITIONAL_EVIDENCE_REQUIRED | PENDING | PENDING |
| LIBFFI-WIN | `cffi-2.1.1-cp312-cp312-win_amd64.whl` | ADDITIONAL_EVIDENCE_REQUIRED | PENDING | PENDING |
| LIBFFI-LINUX | `cffi-2.1.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | ADDITIONAL_EVIDENCE_REQUIRED | PENDING | PENDING |

The JSON register and individual decisions/*.json contain exact hashes, threat/likelihood/impact, evidence references, proposed controls, validity and revocation. Their approval fields are deliberately PENDING. Distributor means PyPI/file hosting plus declared upstream project; individual uploader identity remains unauthenticated for these three wheels. A risk exception cannot grant installation authority or override an unrelated identity/license gap.

For provenance proposals only, suggested upper lifetime is 30 calendar days from real approval, ending sooner on any trigger. This is a proposed governance limit, not an evidence-derived probability or an active authorization. Native unknown-version cases have no acceptable waiver period proposed. No authority, owner, reviewer or signature is invented.

Source #22: 42540f1ddef6d975507482ac8da8970b54f6a945; #21: 0eef2cb7797df1ed21ae89cf3286462697aa3a83; engineering baseline: 9ed55709add0fc45f63847a0394315863faa0876. Isolated branch governance/ed25519-exception-review-v1. Scientific integrity is separately verified; passing science/tests does not resolve supply-chain approvals.

Effective decisions, named owners, independent reviewers, signatures and approval evidence remain **PENDING**. **DEPENDENCY_APPROVAL_REQUIRED**; **PILOT_BLOCKED**, all eight operational gates PENDING. This dossier does not authorize installation, locks, runtime provisioning, adapter implementation or pilot execution.

Evidence paths in every JSON case are resolved from the explicit repository-relative evidence_reference_base, not from the decisions/ subdirectory. Each native-identity form includes its own static/build/notice references.
