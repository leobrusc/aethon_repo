# Targeted transitive publisher evidence

| Case | Added public evidence | What closes | What does not close |
|---|---|---|---|
| PROV-CFFI-WIN | Official v2.1.1 release, source commit API signature status; exact cp312 Windows job before upload | Release/source/platform execution context | Per-wheel publisher identity, exact output digest, build inputs |
| PROV-CFFI-LINUX | Same release/source; exact cp312 x86_64 manylinux job before upload | Release/source/platform execution context | Per-wheel publisher identity, libffi 3.4.6 recipe-to-binary identity, compiler/link closure |
| PROV-PYCPARSER | Official release_v3.12, source tree/unsigned commit metadata; test/dependabot runs and upload timeline | Official release context; excludes found post-upload CI as producer | Authenticated source-to-wheel/publisher binding |

cffi's release API reports publication 2026-08-03T21:17:55Z, author account nitzmahone, no release assets, immutable=false. GitHub reports source commit signature valid; no independent maintainer-key trust verification was performed. These are service-reported source/publication observations, not an artifact attestation or proof that the release actor uploaded these files to PyPI.

pycparser's release API reports publication 2026-10-22T13:41:52Z, author account eliben, no assets, immutable=false. Commit 3ec766b7cd94724cba714296509604597ea4ce4e is reported unsigned. The acquired wheel upload was 13:40:02.021539Z; discovered pycparser-tests run39789013043 started13:41:04Z, and Dependabot graph run39789040258 started13:41:15Z. Both postdate upload; neither can be assumed to have produced it. An unsigned source commit is not an invalid wheel signature, and absence of a publishing run is not proof publication was malicious.

Supplemental GitHub attestations-by-digest queries retrieved no attestations: HTTP 404 for all three cases using preexisting gh. The connector itself rejected that endpoint family, so its HTTP400 is a tool capability limitation, not evidence of missing provenance; fallback query receipts distinguish the two. GitHub404 is reported as no attestation retrieved in this repository/API view, not universal proof of absence or a failed cryptographic verification. The three exact PyPI endpoints were queried again in Phase5E and all returned HTTP 404 with timestamped response hashes (pypi-provenance-query.json); hashes and exact-version metadata remain integrity evidence only.

Current technical recommendation for all three: ADDITIONAL_EVIDENCE_REQUIRED. No invalid/adulterated artifact attestation was demonstrated. Existing source/license byte consistency, exact hashes and isolation proposals are compensating evidence, not authenticated provenance. Highest-value next artifact is an authenticated historical per-wheel receipt or retained output digest linked to the actual release/build; repeating generic CI, index hashing or inventories cannot manufacture that binding.

Exact URLs, retrieval times and hashes: evidence/phase5e/public-api-receipts.json and github-attestation-query.json. Existing three decision IDs, scope hashes and PENDING human approval fields are reused unchanged; phase5e_closure records the precise additions. [cffi release](https://github.com/python-cffi/cffi/releases/tag/v2.1.1), [pycparser release](https://github.com/eliben/pycparser/releases/tag/release_v3.12).

**DEPENDENCY_APPROVAL_REQUIRED / PILOT_BLOCKED**. All eight operational gates and all effective human decisions remain PENDING. No installation, import/execution of acquired artifacts, dependency/lock/runtime change, inference, deployment or maintainer contact occurred.
