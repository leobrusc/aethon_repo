# Prioritized remediation and decisions

This plan applies to new maintained environments. Historical scientific
environments are not patched in place; their original six manifests, exact pins
and PR #1 environment evidence remain immutable and verifiable.

| Priority | Attack surface and decision | Verification |
| --- | --- | --- |
| P0 | Replace Transformers 4.46.3/tokenizers 0.20 in the maintained profile with 5.22.1/0.23.3. Preserve original pin pair for historical reproduction. | Complete regression suite and CLI; strict dependency queries; actual target-model inference NOT_RUN |
| P0 | Replace historical torch 2.12 with official CPU 2.15.0 or CUDA 13.0 2.14.1. Do not infer binary safety from an unrecognized local-version suffix. | Official index, exact wheel URL/SHA-256, PEP 610 install receipt, runtime version, native + upstream queries |
| P0 | Upgrade Accelerate 1.13 to 1.15, datasets 4.8.5 to 5.1 and sentence-transformers 5.5 to 6.2 for model/checkpoint/data paths. | Research locks and audits; dedicated CPU installation; GPU inference NOT_RUN |
| P0 | Upgrade setuptools 81 to 84.2.1. Install external dependencies binary-only with mandatory hashes; only local reviewed AETHON source is built. | Locked build tools, sdist/wheel build, editable install, CI |
| P1 | Upgrade Pillow to 13, urllib3 to 2.8, aiohttp to 3.14.5, multidict to 7.2.1, filelock to 4.2.7, anyio to 4.16 and certifi to 2026.10.23. | Platform-specific transitive locks and strict scanner queries |
| P1 | Use fsspec 2026.7 (security floor 2026.6) instead of incompatible floor 2026.9. datasets 5.1 limits fsspec to <=2026.7. | Resolver compatibility and current vulnerability query, without overriding upstream metadata |
| P1 | Preserve numerical versions numpy 2.2.6, pandas 2.3.3, scipy 1.15.3 and scikit-learn 1.7.2 to reduce scientific migration risk. | Existing scientific tests, historical byte hashes, B3/B4 reanalysis; no historical recomputation |
| P2 | Quarantine historical vulnerable runtime; review remaining model sources, GPU binaries and future advisories separately. | FAIL/NOT_RUN/NOT_AUDITED remain visible; no blanket risk approval |

The initial attempts with fsspec >=2026.9 and torch 2.15/CUDA 13.0 failed
resolution. The official cu130 index has no torch 2.15 artifact, so that profile
uses the available 2.14.1 release, which is later than the recorded torch advisory's
2.13 fix. These were dependency compatibility failures, not suppressed findings.

The alias matrix retains every original occurrence. Vendor severity/CVSS values
are preserved; missing values remain UNKNOWN. The listed code paths establish
potential exposure, not a completed exploit demonstration. An advisory with no
fixed-version event is not silently assigned a fix: see the residual report.

Future dependency changes regenerate locks with uv 0.13.7, create new isolated
environments, repeat audits and compatibility checks, then retain the previous
locks in Git. Do not use `pip-audit --fix`, arbitrary overrides, generic ignores,
or historical metric changes to achieve green checks.
