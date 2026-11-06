# libffi: targeted build traceability

**Windows and Linux actual identity: NOT_IDENTIFIED.** This investigation reused PR23's source snapshots and inspected public release/CI/commit metadata only; no new source, wheel, tool, native binary or artifact archive was downloaded. Generic symbols are not version proof.

| Traceability edge | New evidence | Conclusion |
|---|---|---|
| cffi release -> source commit/tree | v2.1.1 release; fd33e7700f0ebafe6f30bd5053f13327221b77a2; tree dc954328517d7d06ee8ecf663ee61c8f7511b4d5 | Public source/release context established; GitHub reports valid commit signature, not independently trusted key verification |
| Source SHA -> platform jobs | Manual run 30836879169; Windows cp312 job 91764146011, Linux cp312 job 91764159393, both SUCCESS with build/test/upload steps | Documentary execution/platform context established |
| Platform job -> compiler/libffi/link inputs | Both job-log endpoints returned HTTP 410; no current run artifacts listed | Inputs and final output hashes cannot be recovered from these endpoints |
| Output -> acquired wheel SHA256 | No per-wheel signed receipt/digest recovered; GitHub releases contain no assets | NOT_ESTABLISHED; CI success/naming is not a binary binding |

Manual Windows job ran 2026-08-03 17:28:23–17:30:21Z; Linux 17:45:39–17:49:20Z. PyPI uploads were Windows 21:19:56.890792Z and Linux 21:19:52.054167Z. Ordering permits these jobs as candidates but does not uniquely identify the producer. The later tag run 30854037511 has no CPython 3.12 Windows/Linux build job in its 38-job listing, so its general success is not proof for these two wheels. A cancelled earlier run is not credited as a successful producer.

Prior acquired Linux CI recipe declares libffi 3.4.6 static-build inputs; actual compiler, container digest, archive digest, applied patches, effective linker inputs and output-to-PyPI association remain unproven. Windows setup selects a CPython-derived vendored source tree; its stale README labels cannot identify the current fork/version. The acquired native-member hashes and static imports remain consistent with previous evidence, not a new source-to-binary proof. No version-scoped libffi advisory finding can be assigned to these exact binaries yet.

Artifacts APIs returned zero entries; this is not proof no artifacts were ever uploaded. Job metadata says upload succeeded, while log endpoints now return410. Age exceeds GitHub's documented default90-day retention, which is consistent with expiry but does not prove this repository's actual retention/deletion cause. No prohibited archive download was attempted. Repeating the same unavailable endpoints is unlikely to resolve the material gap.

High-value remaining evidence: already-retained original build logs/manifests with final wheel hashes, source/libffi patch identifiers, compiler/container/link inputs; authenticated publisher statements linking those hashes; or a separately authorized reproducible-build comparison with explicit limitations. A rebuilt artifact alone would not authenticate historical PyPI publication. No request was sent to maintainers.

Evidence: evidence/phase5e/public-api-receipts.json and build-link-matrix.json; source hashes are API text hashes and source-snapshot hashes from PR23, not signatures on the wheels. [Candidate run](https://github.com/python-cffi/cffi/actions/runs/30836879169), [release](https://github.com/python-cffi/cffi/releases/tag/v2.1.1), [retention documentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts).

**DEPENDENCY_APPROVAL_REQUIRED / PILOT_BLOCKED**. All eight operational gates and all effective human decisions remain PENDING. No installation, import/execution of acquired artifacts, dependency/lock/runtime change, inference, deployment or maintainer contact occurred.
