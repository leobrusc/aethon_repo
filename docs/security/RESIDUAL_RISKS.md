# Residual findings, gaps and risk disposition

| Item | Status | Disposition |
| --- | --- | --- |
| Historical PR #2 environment | FAIL | Original 168/102 scanner occurrences retained; preserve isolated for reproduction, not new untrusted-input processing |
| Maintained locked upstream dependencies | See `validation.json` | Strict queries for every resolved version; no vulnerability suppression or unknown-version exemption |
| Exact torch +cpu/+cu130 catalog identity | NOT_AUDITED | Native skip retained; public-version query is supplementary, not a binary audit |
| Official wheel provenance and installed CPU receipt | See evidence | Exact source/URL/hash/version verified independently of vulnerability catalog |
| CUDA runtime, GPU operators and real model inference | NOT_RUN | Linux CUDA lock resolved and dependency-queried; requires actual target hardware, drivers and reviewed weights |
| Other GPU platforms/backends | NOT_RUN | No portable/GPU Windows or untested CUDA compatibility claim |
| New-stack replication of all published experiments | NOT_RUN | Historical bytes/identities/results preserved; CLI and regression checks do not replace new full experiments |
| Arbitrary pickle/joblib/model repository safety | NOT_AUDITED | Only trusted immutable historical artifacts; hashes establish identity, not harmlessness |
| Complete exploit reachability of every advisory | NOT_RUN | Matrix code paths are potential exposure; absence of a demonstrated exploit is not grounds for ignoring findings |

Some historical records do not provide a fixed-version event, notably
Accelerate CVE-2026-69112 and Transformers CVE-2025-14920/14921/14924/14926/
14927/14928/14929/14930. Their matrix `fixed_versions` remains empty. The updated
versions are separately queried against current advisory data; a successful
query means no current reported match, not proof that a vendor issued a named
patch for every historical record. Missing/UNKNOWN severity or CVSS metadata is
retained as such. Review upstream details before making exploitability claims.

Accepted scope is preservation of historical evidence and use of verified
maintained CPU tooling with the stated controls. No unconditional acceptance of
the historical vulnerabilities, GPU execution gap or unaudited binary content
is implied. Production deployment and any residual risk acceptance need an
explicit maintainer decision based on its threat model; no merge is automated.

Future actions: run reviewed model-weight smoke/inference and CUDA tests on
actual hardware, inspect upstream binary provenance/attestations beyond HTTPS
and hashes, track advisories without fixed-version metadata, and rerun dated
audits as databases change. Never overwrite historical scientific results.
