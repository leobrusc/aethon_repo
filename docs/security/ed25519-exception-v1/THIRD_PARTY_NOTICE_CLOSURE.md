# Third-party notice closure

**COMPLIANCE_REVIEW_PENDING**. No legal approval or definitive noncompliance finding.

| Component | Declared license | Text evidence | Incorporation confidence | Potential obligation | Closure evidence missing | Legal owner / approval |
|---|---|---|---|---|---|
| cryptography | Apache-2.0 OR BSD-3-Clause | Acquired LICENSE/APACHE/BSD; matching platform texts | Package texts proven; native inventory partial | Preserve chosen-license text/attribution; Apache NOTICE handling if applicable | Chosen terms and third-party notice closure | PENDING |
| cffi | MIT-0 | Acquired LICENSE matches pinned source | Package text proven; libffi version unknown | MIT-0 top-level does not discharge incorporated-code obligations | Separate libffi identity/copyright/notice disposition | PENDING |
| pycparser | BSD-3-Clause | Acquired LICENSE matches pinned source | Pure Python acquired archive | Preserve copyright, conditions/disclaimer in applicable source/binary distribution; no endorsement | Distribution-specific notice packaging/legal review | PENDING |
| OpenSSL 4.0.3 | Apache-2.0 upstream | Exact-tag upstream LICENSE; embedded version/SBOM/literal | Declared + binary-literal evidence; exact linkage/options unproven | Applicable Apache license/attribution and any NOTICE | Component-specific notice applicability and completeness | PENDING |
| libffi | MIT source evidence | Pinned vendored LICENSE and upstream text, not wheel identity | Generic native references only; version NOT_IDENTIFIED | Preserve relevant copyright/permission notice | Which source/patchset applies; corresponding notices absent from reviewed wheel inventory | PENDING |
| Rust crates | 39 acquired upstream SPDX declarations per platform | Embedded SBOM; not full per-crate text inventory | Mixed build/proc-macro/runtime declarations; not all proven linked | Chosen MIT/Apache/BSD terms; Unicode/LLVM additional clauses as applicable | Actual incorporated set, chosen alternatives and per-component notices | PENDING |

Package text hashes and paths are retained in the #21/#22 evidence; no old license evidence was rewritten. Absence of a separate NOTICE file is not, by itself, proof of a legal violation; the reviewer must determine whether applicable upstream NOTICE/attribution exists and is required for the intended distribution. Conversely a generic Apache text does not establish attribution completeness. No binaries are redistributed here.

Rust alternatives must be chosen deliberately: self_cell's Apache-2.0 OR GPL-2.0-only does not automatically require GPL; target-lexicon's Apache-2.0 WITH LLVM-exception and unicode-ident's conjunctive Unicode-3.0 requirement need component-specific review. The 12 build/proc-macro candidates per platform in #22 are not confirmed deployed components. Obtain actual linkage/build inventory before excluding or counting them as incorporated.

Closure checklist per relevant component: exact identity/source/patchset; chosen applicable license; license/copyright/NOTICE hashes and provenance; whether incorporated or build-only and evidence for that determination; intended distribution/use; resulting notice bundle; competent reviewer rationale; independent approval reference and date. Security risk acceptance cannot waive legal obligations. Responsible compliance reviewer and independent approval are PENDING for every row.

Effective decisions, named owners, independent reviewers, signatures and approval evidence remain **PENDING**. **DEPENDENCY_APPROVAL_REQUIRED**; **PILOT_BLOCKED**, all eight operational gates PENDING. This dossier does not authorize installation, locks, runtime provisioning, adapter implementation or pilot execution.
