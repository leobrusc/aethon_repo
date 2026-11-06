# License compliance matrix

| Component | Declared license | Text found | Origin | Potential obligation | Missing evidence |
|---|---|---|---|---|---|
| cryptography | Apache-2.0 OR BSD-3-Clause | Three acquired license texts; both platforms identical | Acquired METADATA/licenses | Preserve chosen-license notices and applicable attribution | Third-party closure/NOTICE and license-choice review pending |
| cffi | MIT-0 | Acquired LICENSE matches pinned upstream commit | Wheel and python-cffi/cffi v2.1.1 | MIT-0 package text; incorporated code has separate terms | libffi exact version/notice not established |
| pycparser | BSD-3-Clause | Acquired LICENSE matches pinned release commit | Wheel and eliben/pycparser release_v3.12 | Retain notices/disclaimer in redistribution; no endorsement | Maintainer provenance/release-build linkage unsigned |
| OpenSSL 4.0.3 | Apache-2.0 upstream | Exact-tag upstream LICENSE.txt inspected; separate OpenSSL license/NOTICE not found in wheel license inventory | OpenSSL openssl-4.0.3 and acquired embedded SBOM | Applicable Apache attribution and any NOTICE handling | Complete incorporated attribution/notice applicability not established |
| libffi | MIT in upstream/vendored source | Current upstream LICENSE and cffi pinned vendored LICENSE inspected; wheel has only cffi package LICENSE | Source evidence, not exact acquired build | Retain relevant copyright and permission notice | Version/build identity and bundled notices NOT_IDENTIFIED |
| Rust components | 39 acquired upstream SBOM declarations per platform | SPDX expressions found; individual full crate texts/notices not inventoried | Embedded Rust SBOM | Chosen MIT/Apache/BSD etc conditions depend on actual incorporated components | Build/runtime split and third-party texts/attribution incomplete |

The native component inventory contains no standalone NOTICE entry establishing full third-party notice closure. The same generic Apache license text does not prove all attribution obligations satisfied. Rust expressions include self_cell Apache-2.0 OR GPL-2.0-only (alternative choice, not automatic GPL requirement), target-lexicon Apache-2.0 WITH LLVM-exception and unicode-ident (MIT OR Apache-2.0) AND Unicode-3.0. Individual declarations/paths/hashes remain in the parent evidence; the license of a top-level package is not asserted to cover every incorporated component. No binaries are distributed by this review. **COMPLIANCE_REVIEW_PENDING**; no legal approval or finding of legal noncompliance is issued.

**DEPENDENCY_APPROVAL_REQUIRED** remains for installation/locks/runtime/adapter. **PILOT_BLOCKED**, all eight operational gates PENDING. No installation, wheel/native import or execution, inference, runtime change, dependency/lock update or merge occurred.
