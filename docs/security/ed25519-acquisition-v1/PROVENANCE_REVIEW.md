# Provenance review

Two cryptography provenance API responses bind a single filename/SHA-256 subject to the actual acquired bytes. PEP 740 v1 DSSE P-256/SHA-256 signatures verify mathematically with their presented certificate leaf public keys using the preexisting Git OpenSSL 3.5.4. Exact statement bytes, not reserialized JSON, were verified. This tool is audit-only and is not the future SRC-01 production verifier.

Both: **PARTIALLY_VERIFIED / PROVENANCE_NOT_VERIFIED**. Publisher claim: GitHub `pyca/cryptography`, workflow `pypi-publish.yml`; certificate SAN names that workflow at `refs/heads/main`. Certificate issuer claims sigstore-intermediate/sigstore.dev. Validity shown: 2026-09-30 14:43:03–14:53:03 UTC. Transparency log indexes: 3020561492 and 3020563834. These are untrusted claims until independently verified. A currently expired short-lived certificate alone does not invalidate a historical signature.

An independently trusted Fulcio chain/root and Rekor inclusion/checkpoint/identity/time policy were not verified. No trusted complete Sigstore verifier was available; none was installed. Public key possession/signature math does not authenticate publisher identity, certificate chain, timestamp, workflow commit or transparency inclusion. No claim of VERIFIED provenance is made.

cffi Windows, cffi Linux and pycparser: official integrity endpoints returned HTTP 404; **MISSING / PROVENANCE_NOT_VERIFIED**. Exact response hashes are in static-analysis.json. No 404 was converted into approval. No invalid signature or subject mismatch was observed in the available attestations.

References: [PEP 740](https://peps.python.org/pep-0740/), [PyPI Integrity API](https://docs.pypi.org/api/integrity/). Full public evidence structures and private receipt hashes are retained; no private keys were generated.

Installation: **DEPENDENCY_APPROVAL_REQUIRED**. Prospective execution: **PILOT_BLOCKED**; all eight operational gates remain PENDING.
