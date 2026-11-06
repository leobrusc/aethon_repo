# pycparser provenance risk

## PROV-PYCPARSER

- Artifact: `pycparser-3.12-py3-none-any.whl`; SHA-256 `a076f3f489b39b43ed13563a1dafe42447445bec2e294154ec5c57fcdda4c85e`.
- Platform/ABI: Pure Python wheel; future use restricted to proposed Windows/Linux x86_64 runtimes.
- Distribution: official PyPI project `pycparser==3.12` and files.pythonhosted.org; per-file uploader identity NOT_AUTHENTICATED. Frozen allowlist, index/local digest and sizes agree; ZIP/RECORD passed previously and bytes rechecked now.
- Upstream: `release_v3.12` / `3ec766b7cd94724cba714296509604597ea4ce4e`. Package license bytes match that source; this does not prove the wheel was built from it.
- Missing evidence: Authenticated publisher-to-wheel binding, Verified builder execution/source-to-binary or source-to-wheel relationship, Named risk owner and independent approval evidence.
- Threat: Upstream/index credential compromise or malicious release could publish malicious bytes that agree with index hashes; hash pinning cannot authenticate intent or trusted builder.
- Likelihood: **UNDETERMINED**; no numerical probability or unjustified low-risk label. No incident/base-rate/control-effectiveness data; absence of attestation neither proves compromise nor bounds probability.
- Impact: **HIGH_POTENTIAL_IF_LATER_EXECUTED**. Malicious native/Python package code could act with interpreter privileges, expose keys/receipts or falsify decisions; current read-only quarantine does not execute it.
- Proposed compensating controls: exact artifact/index recheck; private quarantine; independent source/license/composition review; later separately authorized hash-pinned immutable/no-egress runtime; installed SBOM and rollback. Existing static checks are evidenced; future runtime controls are pending, not claimed deployed.
- Residual: Publisher/build compromise and omitted components remain possible; hashes, HTTPS and isolation are not equivalent to signed provenance.
- Proposal: **ADDITIONAL_EVIDENCE_REQUIRED**. Actual decision, owner, authority, independent reviewer and authenticated approval: **PENDING**.
- Proposed validity: at most 30 calendar days from real approval, with an explicit earlier valid_until where appropriate; currently valid_from/valid_until **PENDING**, no active approval. Revoke/reassess on hash/version/platform/ABI/runtime/policy change, material advisory, compromise, control failure or expiry.

Fillable record: `decisions/PROV-PYCPARSER.json`. Required human justification must explicitly address all listed missing evidence; blanket acceptance of another platform/artifact is invalid.

Distribution version 3.12 is the package release, not a declaration of the Python interpreter version. This wheel is pure Python; that removes a native-composition question for this artifact but does not remove malicious Python-code/publisher risk. A universal wheel tag does not broaden the proposed AETHON platform scope beyond the later explicitly approved Windows/Linux runtime configurations.

Effective decisions, named owners, independent reviewers, signatures and approval evidence remain **PENDING**. **DEPENDENCY_APPROVAL_REQUIRED**; **PILOT_BLOCKED**, all eight operational gates PENDING. This dossier does not authorize installation, locks, runtime provisioning, adapter implementation or pilot execution.
