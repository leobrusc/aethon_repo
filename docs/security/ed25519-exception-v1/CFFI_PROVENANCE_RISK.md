# cffi provenance risk — independent platform decisions

## PROV-CFFI-WIN

- Artifact: `cffi-2.1.1-cp312-cp312-win_amd64.whl`; SHA-256 `f53e442b08449d42821fa4a4fba000095af9f62742a500f978a9f557ec44339a`.
- Platform/ABI: Windows x86_64 CPython cp312.
- Distribution: official PyPI project `cffi==2.1.1` and files.pythonhosted.org; per-file uploader identity NOT_AUTHENTICATED. Frozen allowlist, index/local digest and sizes agree; ZIP/RECORD passed previously and bytes rechecked now.
- Upstream: `v2.1.1` / `fd33e7700f0ebafe6f30bd5053f13327221b77a2`. Package license bytes match that source; this does not prove the wheel was built from it.
- Missing evidence: Authenticated publisher-to-wheel binding, Verified builder execution/source-to-binary or source-to-wheel relationship, Named risk owner and independent approval evidence, libffi exact identity, notices and version-scoped applicability.
- Threat: Upstream/index credential compromise or malicious release could publish malicious bytes that agree with index hashes; hash pinning cannot authenticate intent or trusted builder.
- Likelihood: **UNDETERMINED**; no numerical probability or unjustified low-risk label. No incident/base-rate/control-effectiveness data; absence of attestation neither proves compromise nor bounds probability.
- Impact: **HIGH_POTENTIAL_IF_LATER_EXECUTED**. Malicious native/Python package code could act with interpreter privileges, expose keys/receipts or falsify decisions; current read-only quarantine does not execute it.
- Proposed compensating controls: exact artifact/index recheck; private quarantine; independent source/license/composition review; later separately authorized hash-pinned immutable/no-egress runtime; installed SBOM and rollback. Existing static checks are evidenced; future runtime controls are pending, not claimed deployed.
- Residual: Publisher/build compromise and omitted components remain possible; hashes, HTTPS and isolation are not equivalent to signed provenance.
- Proposal: **ADDITIONAL_EVIDENCE_REQUIRED**. Actual decision, owner, authority, independent reviewer and authenticated approval: **PENDING**.
- Proposed validity: at most 30 calendar days from real approval, with an explicit earlier valid_until where appropriate; currently valid_from/valid_until **PENDING**, no active approval. Revoke/reassess on hash/version/platform/ABI/runtime/policy change, material advisory, compromise, control failure or expiry.

Fillable record: `decisions/PROV-CFFI-WIN.json`. Required human justification must explicitly address all listed missing evidence; blanket acceptance of another platform/artifact is invalid.

## PROV-CFFI-LINUX

- Artifact: `cffi-2.1.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl`; SHA-256 `c1453022f490d2459a11819d83ad1d586e9ff65a12ac3e705ffebd46d3685dcf`.
- Platform/ABI: Linux x86_64 CPython cp312, manylinux2014/glibc>=2.17.
- Distribution: official PyPI project `cffi==2.1.1` and files.pythonhosted.org; per-file uploader identity NOT_AUTHENTICATED. Frozen allowlist, index/local digest and sizes agree; ZIP/RECORD passed previously and bytes rechecked now.
- Upstream: `v2.1.1` / `fd33e7700f0ebafe6f30bd5053f13327221b77a2`. Package license bytes match that source; this does not prove the wheel was built from it.
- Missing evidence: Authenticated publisher-to-wheel binding, Verified builder execution/source-to-binary or source-to-wheel relationship, Named risk owner and independent approval evidence, libffi exact identity, notices and version-scoped applicability.
- Threat: Upstream/index credential compromise or malicious release could publish malicious bytes that agree with index hashes; hash pinning cannot authenticate intent or trusted builder.
- Likelihood: **UNDETERMINED**; no numerical probability or unjustified low-risk label. No incident/base-rate/control-effectiveness data; absence of attestation neither proves compromise nor bounds probability.
- Impact: **HIGH_POTENTIAL_IF_LATER_EXECUTED**. Malicious native/Python package code could act with interpreter privileges, expose keys/receipts or falsify decisions; current read-only quarantine does not execute it.
- Proposed compensating controls: exact artifact/index recheck; private quarantine; independent source/license/composition review; later separately authorized hash-pinned immutable/no-egress runtime; installed SBOM and rollback. Existing static checks are evidenced; future runtime controls are pending, not claimed deployed.
- Residual: Publisher/build compromise and omitted components remain possible; hashes, HTTPS and isolation are not equivalent to signed provenance.
- Proposal: **ADDITIONAL_EVIDENCE_REQUIRED**. Actual decision, owner, authority, independent reviewer and authenticated approval: **PENDING**.
- Proposed validity: at most 30 calendar days from real approval, with an explicit earlier valid_until where appropriate; currently valid_from/valid_until **PENDING**, no active approval. Revoke/reassess on hash/version/platform/ABI/runtime/policy change, material advisory, compromise, control failure or expiry.

Fillable record: `decisions/PROV-CFFI-LINUX.json`. Required human justification must explicitly address all listed missing evidence; blanket acceptance of another platform/artifact is invalid.

The two cffi decisions are independent: a Windows decision does not authorize Linux or the reverse. Neither can waive LIBFFI-WIN/LIBFFI-LINUX or third-party notice closure. The absence of provenance is based on documented PyPI 404 semantics, not a failed signature check. No evidence proves why the publisher omitted attestations, nor that signatures do not exist elsewhere.

Effective decisions, named owners, independent reviewers, signatures and approval evidence remain **PENDING**. **DEPENDENCY_APPROVAL_REQUIRED**; **PILOT_BLOCKED**, all eight operational gates PENDING. This dossier does not authorize installation, locks, runtime provisioning, adapter implementation or pilot execution.
