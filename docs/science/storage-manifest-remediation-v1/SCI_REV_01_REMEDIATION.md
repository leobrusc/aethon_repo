# SCI-REV-01 remediation report

## Cause

PR #25 checked the 120 slot identities and condition set, but trusted caller-supplied `pair_id` and `family_id`, accepted any schedule permutation, and accepted any 64-hex `run_fingerprint`. The capability boundary did not have the raw inventory rows needed to recompute the original fingerprint formula or independently validate the paired design.

## Correction

- Added `pilot_scientific_manifest.py`, a backend-independent validator shared by manifest construction and storage capability issuance.
- Changed schema to `aethon.pilot-run.v2`; the exact authorized raw inventory bytes travel in the private manifest. The validator binds them to the signed subject digest, validates the canonical 12-pair/4-4-4 design, recomputes sample identities and all slots, and regenerates the exact seeded schedule.
- Preserved the original run fingerprint formula and recompute it from the recovered validated rows, config, retention and schedule.
- Converted `StorageBackend` to a template-method base that validates before `_open_validated_run`; subclass override of `open_run` is rejected. It supplies an immutable validated-manifest token only after authorization and content checks. The facade accepts only this base type.
- Tightened issued `Authorization` tracking to object identity, preventing an equal-value dataclass clone from being treated as a grant.
- Bound retention custodian/date/plan hash into internal `Authorization` from existing signed receipt claims. Receipt formats did not change.
- Kept `collect_runtime` blocked. No native backend or production selector was added.

## Historical reproduction handling

The two PR #26 reproduction tests are preserved byte for byte at `tests/historical/test_storage_capability_review_reproductions.py.txt`; SHA-256 is recorded in `MANIFEST_ADVERSARIAL_TESTS.md`. Their former vulnerable expectation was “malformed manifest accepted.” New active tests require rejection before any backend run state or capability exists. The old source was not edited to appear green.

## Results

Validation is recorded in `SCIENTIFIC_INTEGRITY_VALIDATION.md`. The disposition is limited to SCI-REV-01. It does not authorize SRC-02, establish native durability/confinement, or satisfy any operational gate.
