# Scientific manifest contract — v2

## Trust boundary

`StorageBackend.open_run()` is now a non-overridable template method on the shared `StorageBackend` base class. It bounds and canonicalizes the manifest, calls `validate_manifest_document()`, verifies the exact issued `Authorization` object and signed retention claims, and only then calls a backend-specific `_open_validated_run()` with an immutable `ValidatedRunManifest`. Authorization issuance is tracked by object identity, so a dataclass clone with equal fields is not an issued grant. A subclass that overrides `open_run()` is rejected at class creation. `PrivateRunStore` rejects duck-typed backends. This is an application-code boundary, not protection against hostile Python reflection or a compromised process.

No backend may issue a `RunCapability` from raw manifest bytes. Native backends must subclass this base and implement `_open_validated_run`; they remain unimplemented and production collection stays disabled.

## Schema

`aethon.pilot-run.v2` is the first supported capability manifest. Its exact top-level fields are: schema, run identity algorithm, run ID, subject, config, retention, canonical inventory digest, base64 exact source inventory bytes, review-rubric projection, initial slots, schedule, schedule policy, provenance, run fingerprint, and authorization provenance. Unknown or missing top-level fields are rejected. Inventory JSON must be `aethon.private-inventory.v1` with exactly `schema` and `rows`; each row has a closed versioned field set. Unknown row fields fail closed pending a schema review.

The exact inventory file bytes are carried base64-encoded inside the private run manifest. The validator checks their SHA-256 against the subject authorized by the independent inventory receipt, parses duplicate-free JSON, validates all 24 rows, and checks that the derived projection is the one represented by the slots. This duplicates private prompt/task data in the private manifest; the existing manifest byte quota applies and an oversized inventory is rejected. The field must never be emitted to public logs or CI artifacts.

## Frozen scientific invariants

- 24 distinct `sample_id` values, each recomputed from namespace, source ID, source row ID and exact prompt bytes.
- 12 distinct pairs; exactly two rows per pair; one integer label 0 and one 1; matching family and paired system prompt, legitimate objective and task rubric.
- Exactly four pairs in each canonical family: `instruction-override`, `synthetic-disclosure`, `answer-contamination`.
- Unique source and scenario identities; supplied sample hashes must agree with source fields; no unknown row fields.
- Exactly five slots per sample, conditions B0–B4 once each, replicate 0, pending initial state, exact canonical `slot_id`, individual fingerprint, all projected identity fields and generation contract equal to the validated source/config.
- Exactly 120 unique slots and a 120-entry agenda with no missing/extra IDs.
- Exact frozen schedule `seeded_pairs_arms_b4_after_b3`, regenerated from the config seed using the existing pair order, per-case arm shuffle and B4-after-B3 operation. A mere topological ordering is insufficient; any agenda drift is rejected.
- Review-rubric and provenance projections must exactly match validated rows, subject and config.

Structural checks do not replace human semantic review of whether a row is correctly classified as an attack/control or family.

## Compatibility

Historical `pilot-run.v1` manifests cannot be reopened under this contract. No automatic migration is provided. Existing receipt JSON formats, gate meanings, B0–B4 algorithms, generation settings, thresholds, labels and datasets are unchanged. `Authorization` gains internal, non-receipt fields derived from the already signed private-storage claims: custodian, deletion date and retention-plan SHA-256. New authorization objects bind exact manifest retention. Updated implementation seals change the collector config fingerprint, so old authorization cannot be reused; fresh evidence would be required in any future independently approved run.
