# Final independent validation report

## Identity and CI

- PR #27: [fix/storage-manifest-scientific-integrity-v1](https://github.com/leobrusc/aethon_repo/pull/27)
- Reviewed head: `2034aade9b56bf76ff13f4816a5ff9de73a879a6`
- PR #26 finding/base: `26834be1e72f8e6f102a5431019b3f4cad1d4091`
- Independent branch: `review/scientific-manifest-closure-v1`
- CI #42322507843: all three jobs `SUCCESS`; it tested merge ref `d0a44d9524ad1a05267b68d3d16287558090d701`, incorporating the exact reviewed head. Windows and Linux each report 398 passed, 1 warning.

## Validation

| Check | Result |
|---|---|
| Focused manifest and storage contracts | PASS — 76 passed |
| Full suite, local Windows sandbox / Python 3.10.11 | ENVIRONMENT_BLOCKED — 397 passed; legacy OpenSSL subprocess failed creating its Cygwin signal pipe (details in `OPENSSL_ENVIRONMENT_DIAGNOSIS.md`) |
| Full suite, existing approved CI Windows Server 2025 / Python 3.12.10 | PASS — 398 passed |
| Full suite, existing approved CI Linux | PASS — 398 passed |
| Ruff (`--no-cache`) | PASS |
| `pip check` | PASS — no broken requirements |
| Publication guard against #26 | PASS |
| `git diff --check` against #26 | PASS |
| Git LFS | PASS — `git lfs fsck` OK |
| Offline preflight | PASS for fail-closed state — `PILOT_BLOCKED`, `executed=false`, all eight gates `PENDING` (exit 2 expected) |
| Historical integrity | 127, 31, six manifests, 9,139 pairs and LFS/local hashes PASS; 80 metrics reused after exact source hash match; raw dataset hash NOT_AUDITED |
| Original PR #26 reproductions | PASS preservation — file SHA-256 `cb1677420f58268ec310190442e4363f2b37962d0a5fb7451b21b868624151f4`; Git blob ID matches historical source `5df1607ada22ebac330e106b5421e6fa36a13e4e` |

## Classification

**SCI-REV-01 disposition: `SCI_REV_01_CLOSURE_VALIDATED`.** Independent review found no remaining reproducible defect in scientific manifest validation; negative and positive contract tests pass, and cross-platform CI passed the full suite. The local OpenSSL failure is explicitly retained as `ENVIRONMENT_BLOCKED`, not represented as a validator failure or silently omitted. The 80-value metric comparison is reused evidence with the exact source hash revalidated, not a fresh numeric comparison.

**Overall review disposition: `REMEDIATION_REQUIRED` due to AUTH-REV-01.** An unissued subclass can override `Authorization.check()` and obtain a capability for a scientifically valid run. This is a separate authorization bypass, not a regression of SCI-REV-01. Correct it and obtain a new independent review before native backend implementation.

## Linux backend decision

**Do not begin Linux native backend implementation yet.** SCI-REV-01 is closed, but AUTH-REV-01 is a direct blocker. The independent PR #26 review also lists required backend-contract work: explicit root-capability bootstrap, durable commit result states, restart/revocation and freshness semantics, recoverable object/event transactions, post-collection review authorization, and actual resource accounting. Fix AUTH-REV-01, prepare a revised native-storage contract, and obtain independent threat-model sign-off first. Any later Linux prototype must remain nonproduction until SRC-02 is explicitly authorized and native durability/freshness tests are independently reviewed.

`SRC-02 NOT_AUTHORIZED`; `DEPENDENCY_APPROVAL_REQUIRED`; `PILOT_BLOCKED`; all eight operational gates `PENDING`. No inference, installation, privilege change, merge, or backend implementation occurred.
