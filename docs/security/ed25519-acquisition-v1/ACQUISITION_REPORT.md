# Controlled wheel acquisition — Phase 5B

Overall: **SUPPLY_CHAIN_REVIEW_PENDING**. Artifact integrity: **ARTIFACTS_VERIFIED**, 5/5. No artifact rejected.

Authorized source: `b3f7819b94e8710cc4df9e7fb8ab87d5b323fc15` (PR #20); engineering baseline: `9ed55709add0fc45f63847a0394315863faa0876`; architecture PR #19: `7431d7b423bc6fc34d1db51c12794742481f8428`.
Acquisition `ed25519-20261106T135119Z-ba2a4581` used audit commit `f9e1948eb2c2ec8a707cdc429534ba3909a085d7`; exact script hashes, timestamps and custody receipts are indexed in evidence. HTTPS URLs came from official exact-version PyPI JSON; redirects were checked before following. Only the five authorized distribution files were fetched. No sdists, alternative wheels, resolution, installation, build, wheel import, native loading, inference or provisioning occurred.

| Wheel | Bytes | Expected = observed = PyPI SHA-256 | Integrity | Provenance |
|---|---:|---|---|---|
| `cryptography-50.0.2-cp311-abi3-win_amd64.whl` | 3824692 | `7afa5a6602a9f29af1f3a2965f831bae7c9d5d597b7cbb716d41ab3b7d89879c` | PASS | PARTIALLY_VERIFIED |
| `cryptography-50.0.2-cp311-abi3-manylinux_2_28_x86_64.whl` | 4753050 | `4061c0079120205fb760c58acab6443e217307dcf05e3702cf970e0689972856` | PASS | PARTIALLY_VERIFIED |
| `cffi-2.1.1-cp312-cp312-win_amd64.whl` | 185919 | `f53e442b08449d42821fa4a4fba000095af9f62742a500f978a9f557ec44339a` | PASS | MISSING |
| `cffi-2.1.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | 221822 | `c1453022f490d2459a11819d83ad1d586e9ff65a12ac3e705ffebd46d3685dcf` | PASS | MISSING |
| `pycparser-3.12-py3-none-any.whl` | 62600 | `a076f3f489b39b43ed13563a1dafe42447445bec2e294154ec5c57fcdda4c85e` | PASS | MISSING |

The worktree was created from the authorized source. Original dirty checkout, main refs and PR #15–#20 refs were preserved. Preexisting five local files were hash checked, never stashed or overwritten. Historical CI for PR #20: [42093929291](https://github.com/leobrusc/aethon_repo/actions/runs/42093929291), completed SUCCESS on all three jobs (research-and-gpu-audit; Windows CPU; Linux CPU), associated with the authorized PR head. This is distinct from PR #19 CI #42088936881. No new installation-running CI was authorized; this audit uses `[skip ci]`, and its local checks are separately recorded. Required CI checks may remain pending.

Scientific checks passed before/after: 127 protected files, 31 indexed evidence items, six historical manifests, 9,139 paired B3/B4 records, 80 historical metrics (atol 1e-12, rtol 0), five hydrated LFS payloads and five preexisting local files. No lock/dependency or installed-distribution metadata/interpreter hash changed. Independent raw dataset canonical hash remains NOT_AUDITED.

Provenance is partial for two cryptography wheels and missing for three other wheels. Package advisories and declared Rust dependency coverage are version scoped; exact binary vulnerabilities and unidentified libffi remain NOT_AUDITED. See the dedicated reports and validation evidence.

Installation: **DEPENDENCY_APPROVAL_REQUIRED**. Prospective execution: **PILOT_BLOCKED**; all eight operational gates remain PENDING.
