# Authorization issuer CI and preservation evidence

## CI and source equivalence

- CI run: `42398791189`.
- Linux: SUCCESS, 408 passed, one warning.
- Windows: SUCCESS, 408 passed, one warning.
- Research/GPU audit: SUCCESS; GPU inference `NOT_RUN`.
- Tested implementation: `803451e2045e73de103e8f4ddd8c2ea47d06a9a6`.
- Final reviewed HEAD: `8f851d2ad5ae7e886c58a1081f18c0d2dc284b55`.
- The diff after the tested implementation commit changes only
  `AUTH_ISSUER_ADVERSARIAL_TESTS.md` and `AUTH_ISSUER_VALIDATION.md`; no code,
  tests, config, or locks differ.

## Recalculated in this independent review

- Scientific inventory: PASS, 127 protected files against recorded base
  `544c363c19a08574d30e7e2c064a78ce1bdfb601`.
- The six historical evidence manifests were included in that 127-file hash
  verification: `docs/research_2026_evidence/dp/manifest.json`,
  `integrity/manifest.json`, `promptguard/manifest.json`,
  `nested/manifest.json`, `protectai_smoke/manifest.json`, and
  `docs/validation/evidence/protectai-current-manifest.json`.

Current SHA-256 values independently recalculated in the review worktree:

| Manifest | SHA-256 |
|---|---|
| `docs/research_2026_evidence/dp/manifest.json` | `c68278d53090c9018f2277ed5b6752b2a69da55b03881b75bf36766865da8e3d` |
| `docs/research_2026_evidence/integrity/manifest.json` | `500b77a4b3487c13903ef0457a4ef60134f886acb6d826f44d132c3b8aa21dc6` |
| `docs/research_2026_evidence/promptguard/manifest.json` | `3a5f6fa677f17297d0f3d856f4e94e986d35331403bbbe040500c8db314ca8d2` |
| `docs/research_2026_evidence/nested/manifest.json` | `10396786da2ba56ca6e413a8ef3f257a561efbed6e687f57bcb6765c34c3a4d6` |
| `docs/research_2026_evidence/protectai_smoke/manifest.json` | `77247b37f7c2288406cb6d526f048e4954bf40273c64bc9e68830b65acc37cee` |
| `docs/validation/evidence/protectai-current-manifest.json` | `68b6ee149bf42703c4b597353000f6dd2badd32a037bcbb23b6a3630fc1244b5` |
- Research evidence: PASS, 31 artifact hashes.
- Git LFS: PASS, `git lfs fsck`; `git lfs ls-files` lists five payloads.
- Publication guard: PASS.
- Ruff on reviewed governance, storage, review, runtime, and test files: PASS.
- `pip check`: PASS, no broken requirements.
- Historical private issuer proof: source hash in PR #30 independently
  rechecked as `abe4426c99ae52332a5ae6799d55a74a8dafabda5784bff2d1d6cf099ebddc4a`;
  vulnerable and corrected executions are recorded in the independent review.
- CI's preserved-history step reanalyzed B3/B4 pairing: `n_paired=9139`,
  `decision_mismatches=0`, source SHA-256
  `66130f23a92ea05fca856c808a4049245a31d0f6c530bbba517473be389e7a15`.
- CI separately confirmed six dependency manifests preserved from
  `a6090ae3030ef52f333fe14380839df4a7d879eb`; these are distinct from the six
  historical evidence manifests listed above.
- CI deterministic replay reported PASS for 9,139 reference rows, 25
  comparisons, and no mismatches; no new LLM detector inference was performed.

## Reused prior evidence and limits

- The 80 historical metric-value comparison is reused, not recomputed in this
  independent authorization review. Prior validation receipt
  `docs/science/remediation-v1/validation/summary.json` has SHA-256
  `a4c7fab61d0f70469b0faa1960bf1c0519c01012711ab07fbd63cce1fcf49342` and records
  80 metrics checked, historical B3/B4 mismatches zero, and the five local files
  preserved. This receipt is historical evidence, not a fresh metric replay.
- The five LFS payloads were not individually rehashed by this review; current
  `git lfs fsck` passed over the worktree and prior preservation receipts record
  the five payload verification.
- Five preexisting local files were left untouched: review changes are in a
  separate worktree. The original checkout still shows its two modified files
  and three untracked files; they were not staged or changed here.
- Local pytest printed twelve pass markers for the focused authorization file,
  but the process did not terminate cleanly and was interrupted (exit 1). That
  attempt is incomplete, not a local suite PASS. Cross-platform CI is the clean
  full-suite evidence.
- No changes were made to main, locks, dependencies, manifests, datasets,
  thresholds, model assets, or experiment results.
