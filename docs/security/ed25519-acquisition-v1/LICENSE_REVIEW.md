# License review

Acquired METADATA and actual LICENSE texts agree: cryptography `Apache-2.0 OR BSD-3-Clause` (LICENSE, LICENSE.APACHE, LICENSE.BSD); cffi `MIT-0`; pycparser `BSD-3-Clause`. Individual member hashes and sizes are preserved in the static evidence. Both platform variants carry matching package license bytes.

cryptography embeds upstream Rust CycloneDX declarations for 39 components, including build/proc-macro dependencies; expressions include MIT, Apache-2.0, BSD-3-Clause, Unicode-3.0, Apache-2.0 WITH LLVM-exception and the choice Apache-2.0 OR GPL-2.0-only for self_cell. These are upstream declarations in acquired bytes, not independent legal certification or proof each crate is linked. Its separate OpenSSL 4.0.3 SBOM has no license entry. OpenSSL upstream declares Apache-2.0; incorporated notices still require review. cffi's MIT-0 package license does not by itself establish the license/notice completeness of embedded libffi (version unknown).

BSD binary redistribution requires notice/disclaimer preservation; Apache redistribution and NOTICE conditions apply as relevant; optional-license choices must be documented before distribution. pycparser text contains copyright 2008–2027; recorded verbatim as publisher metadata, without inference of authenticity from its date. No binaries are redistributed by this PR. Third-party notice completeness and distribution compatibility remain PENDING legal/governance review; this is not a formal legal opinion.

Installation: **DEPENDENCY_APPROVAL_REQUIRED**. Prospective execution: **PILOT_BLOCKED**; all eight operational gates remain PENDING.
