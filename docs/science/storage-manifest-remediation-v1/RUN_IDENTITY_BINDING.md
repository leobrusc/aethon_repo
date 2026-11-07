# Run identity binding

## Preserved formula

Schema v2 deliberately preserves the existing formula exactly:

```text
fingerprint([subject, config, validated_rows, retention, order])
```

`validated_rows` are the sorted rows returned by the shared inventory validator, including the existing derived `sample_id`, `raw_sha256`, and `normalized_sha256` fields. `order` is the exact seeded agenda. The formula was not replaced with a hash of slots.

## Verifiable inputs

1. `subject.inventory_sha256` is the SHA-256 of the exact external inventory bytes that the independent inventory gate reviewed. Those exact bytes are carried in `inventory_source_b64`; the backend base decodes them and requires the digest to match the authorized subject.
2. Parsed rows are validated and sorted independently of `make_manifest()`. The subject must already be authorized by the issued `Authorization`; the manifest cannot replace the subject or its inventory digest.
3. The canonical `inventory_sha256` field is recomputed from validated rows and is distinct from the raw-file digest in the subject.
4. Config is checked against `subject.protocol_sha256`; retention is checked against custodian, deletion date and plan digest copied from the signed private-storage receipt claims.
5. Slots, rubric mapping, provenance and exact agenda are regenerated and compared structurally with the manifest.
6. The old run-fingerprint formula is recomputed from those verified values. A changed pair, family, context, config, retention or order either fails projection/authentication or changes the expected fingerprint.
7. The outer canonical manifest digest and complete backend/budget binding continue to scope every stored object, checkpoint and journal event.

There is no self-referential field: `run_fingerprint` is excluded from its input list. `authorization_provenance` is added by the facade and included in the complete manifest binding, while the preserved legacy formula already includes the authorized subject (including receipts digest and raw inventory digest).

## Agenda policy

The v1 producer shuffled sorted pair IDs with `random.Random(config.generation.seed)`, sorted the two rows in each pair by sample ID, shuffled B0–B4 independently for each row, then moved B4 immediately after B3. The v2 validator uses the same algorithm and requires exact equality, not just B3-before-B4. This freezes both determinism and the B3/B4 prerequisite.

## Versioning and impact

The manifest schema changes from `aethon.pilot-run.v1` to `aethon.pilot-run.v2` and adds `run_identity_algorithm` plus `inventory_source_b64`; `Authorization` carries retention claims internally. Existing receipts and historical manifests are untouched and are not migrated. Updating implementation hashes changes the config fingerprint and therefore invalidates previous pilot authorization by design. All eight gates remain pending.
