# Acquired artifact integrity

| Wheel | Bytes | Expected = observed = PyPI SHA-256 | Integrity | Provenance |
|---|---:|---|---|---|
| `cryptography-50.0.2-cp311-abi3-win_amd64.whl` | 3824692 | `7afa5a6602a9f29af1f3a2965f831bae7c9d5d597b7cbb716d41ab3b7d89879c` | PASS | PARTIALLY_VERIFIED |
| `cryptography-50.0.2-cp311-abi3-manylinux_2_28_x86_64.whl` | 4753050 | `4061c0079120205fb760c58acab6443e217307dcf05e3702cf970e0689972856` | PASS | PARTIALLY_VERIFIED |
| `cffi-2.1.1-cp312-cp312-win_amd64.whl` | 185919 | `f53e442b08449d42821fa4a4fba000095af9f62742a500f978a9f557ec44339a` | PASS | MISSING |
| `cffi-2.1.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | 221822 | `c1453022f490d2459a11819d83ad1d586e9ff65a12ac3e705ffebd46d3685dcf` | PASS | MISSING |
| `pycparser-3.12-py3-none-any.whl` | 62600 | `a076f3f489b39b43ed13563a1dafe42447445bec2e294154ec5c57fcdda4c85e` | PASS | MISSING |

All five artifacts passed exact frozen allowlist, official JSON digest/size/URL and local byte checks. Five archives passed bounded ZIP/CRC/RECORD, filename, distribution/version, tags and member consistency checks. RECORD establishes internal consistency, not authenticity. No wheel code was executed/imported.

Installation: **DEPENDENCY_APPROVAL_REQUIRED**. Prospective execution: **PILOT_BLOCKED**; all eight operational gates remain PENDING.
