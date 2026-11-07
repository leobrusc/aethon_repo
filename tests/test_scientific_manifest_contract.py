"""Synthetic acceptance/rejection coverage for schema v2 capability issuance."""
import base64
import copy

import pytest

from aethon.pilot_collector import make_manifest, validate_inventory
from aethon.pilot_governance import canonical, digest
from aethon.pilot_storage import CorruptCheckpoint, PrivateRunStore
from aethon.pilot_storage_backend import ResourceBudget, ValidatedRunManifest
from aethon.pilot_scientific_manifest import FROZEN_FAMILIES, validate_manifest_document
from pilot_memory_backend import MemoryBackend
from test_pilot_collector import setup_run, synthetic_rows


def _pair_groups(rows):
    groups = {}
    for row in rows:
        groups.setdefault(row["pair_id"], []).append(row)
    return groups


@pytest.mark.parametrize("counts", [(12, 0, 0), (5, 4, 3), (6, 3, 3)])
def test_inventory_rejects_noncanonical_family_pair_quotas(counts):
    rows = synthetic_rows()
    pairs = list(_pair_groups(rows).values())
    labels = [family for family, count in zip(FROZEN_FAMILIES, counts) for _ in range(count)]
    for pair, family in zip(pairs, labels):
        for row in pair:
            row["family_id"] = family
    with pytest.raises(ValueError):
        validate_inventory(rows)


@pytest.mark.parametrize("mutation", ["unknown-family", "incomplete-pair", "two-attacks", "two-controls",
                                       "mixed-pair-family", "context-drift", "duplicate-identity",
                                       "unknown-field", "sample-id-drift"])
def test_inventory_rejects_invalid_pair_and_identity_contracts(mutation):
    rows = synthetic_rows()
    groups = _pair_groups(rows)
    first_pair = next(iter(groups.values()))
    if mutation == "unknown-family":
        for row in first_pair: row["family_id"] = "instruction_override"
    elif mutation == "incomplete-pair":
        rows.remove(first_pair[0])
    elif mutation == "two-attacks":
        first_pair[0]["label"] = 1
    elif mutation == "two-controls":
        first_pair[1]["label"] = 0
        first_pair[1]["attack_objective"] = None
        first_pair[1]["attack_rubric_id"] = None
    elif mutation == "mixed-pair-family":
        first_pair[0]["family_id"] = FROZEN_FAMILIES[1]
    elif mutation == "context-drift":
        first_pair[0]["system_prompt"] += " changed"
    elif mutation == "duplicate-identity":
        first_pair[0]["source_row_id"] = first_pair[1]["source_row_id"]
    elif mutation == "unknown-field":
        first_pair[0]["new_semantic_flag"] = True
    elif mutation == "sample-id-drift":
        first_pair[0]["sample_id"] = "0" * 64
    with pytest.raises(ValueError):
        validate_inventory(rows)


def test_manifest_builder_rejects_unknown_inventory_envelope_field(setup_run):
    from aethon.pilot_collector import make_manifest
    subject = copy.deepcopy(setup_run["subject"])
    source = {"schema": "aethon.private-inventory.v1", "rows": setup_run["rows"],
              "semantic_mode": "unreviewed"}
    raw = canonical(source)
    subject["inventory_sha256"] = digest(raw)
    with pytest.raises(ValueError):
        make_manifest(setup_run["rows"], setup_run["config"], subject,
                      setup_run["manifest"]["retention"], raw)


@pytest.mark.parametrize("mutation", ["family_projection", "pair_projection", "slot_id", "duplicate_condition",
                                       "schedule", "stale_fingerprint", "inventory_digest", "extra_manifest_field"])
def test_backend_rejects_tampered_manifest_before_state_creation(setup_run, mutation):
    manifest = copy.deepcopy(setup_run["manifest"])
    if mutation == "family_projection":
        manifest["slots"][0]["family_id"] = "unknown-family"
    elif mutation == "pair_projection":
        manifest["slots"][0]["pair_id"] = "one-pair-for-all"
    elif mutation == "slot_id":
        manifest["slots"][0]["slot_id"] = "0" * 64
    elif mutation == "duplicate_condition":
        manifest["slots"][0]["condition"] = manifest["slots"][1]["condition"]
        from aethon.prospective import case_identity
        manifest["slots"][0]["slot_id"] = case_identity(
            manifest["slots"][0]["sample_id"], manifest["config"]["revision"],
            manifest["slots"][0]["condition"], 0, manifest["subject"]["protocol_sha256"])
    elif mutation == "schedule":
        by_slot = {slot["slot_id"]: slot for slot in manifest["slots"]}
        b4 = [key for key in manifest["schedule"] if by_slot[key]["condition"] == "B4"]
        rest = [key for key in manifest["schedule"] if by_slot[key]["condition"] != "B4"]
        manifest["schedule"] = b4 + rest
    elif mutation == "stale_fingerprint":
        manifest["run_fingerprint"] = "f" * 64
    elif mutation == "inventory_digest":
        raw = base64.b64decode(manifest["inventory_source_b64"])
        altered = raw.replace(b"synthetic authorized task", b"synthetic alternate task", 1)
        manifest["inventory_source_b64"] = base64.b64encode(altered).decode("ascii")
    elif mutation == "extra_manifest_field":
        manifest["scientific_override"] = True

    backend = MemoryBackend()
    with pytest.raises(CorruptCheckpoint):
        PrivateRunStore(manifest=manifest, authorization=setup_run["permission"], backend=backend)
    assert backend._runs == {}
    assert backend._handles == {}


def test_original_stale_run_fingerprint_reproductions_are_now_rejected(setup_run):
    for mode in ("quotas", "schedule"):
        manifest = copy.deepcopy(setup_run["manifest"])
        original = manifest["run_fingerprint"]
        if mode == "quotas":
            manifest["slots"][0]["pair_id"] = "forged-pair"
            manifest["slots"][0]["family_id"] = "forged-family"
        else:
            manifest["schedule"] = list(reversed(manifest["schedule"]))
        assert manifest["run_fingerprint"] == original
        with pytest.raises(CorruptCheckpoint):
            PrivateRunStore(manifest=manifest, authorization=setup_run["permission"], backend=MemoryBackend())


def test_schema_v2_preserves_historical_run_fingerprint_formula(setup_run):
    manifest = setup_run["manifest"]
    rows = validate_inventory(setup_run["rows"])
    assert manifest["schema"] == "aethon.pilot-run.v2"
    assert manifest["run_identity_algorithm"] == "fingerprint-v1:[subject,config,validated_rows,retention,order]"
    assert manifest["run_fingerprint"] == setup_run["manifest"]["run_fingerprint"]
    assert manifest["run_fingerprint"] == __import__("aethon.prospective", fromlist=["fingerprint"]).fingerprint(
        [manifest["subject"], manifest["config"], rows, manifest["retention"], manifest["schedule"]])
    store = setup_run["store"]()
    validated = store.manifest
    validate_manifest_document(validated)
    assert len(validated["slots"]) == 120
    assert {slot["condition"] for slot in validated["slots"]} == {"B0", "B1", "B2", "B3", "B4"}
    store.close()


def test_reopen_identical_validated_manifest_is_idempotent(setup_run):
    first = setup_run["store"]()
    second = setup_run["store"]()
    assert first.run_capability is not second.run_capability
    assert first.binding_sha256 == second.binding_sha256
    assert second.sequence == 0 and len(second.slots) == 120
    first.close()
    second.close()


def test_reopen_with_unapproved_retention_is_rejected_without_mutating_run(setup_run):
    from aethon.pilot_collector import make_manifest
    first = setup_run["store"]()
    retention = {"custodian": "SYNTHETIC-CUSTODIAN", "delete_after": "2099-02-01"}
    changed = make_manifest(setup_run["rows"], setup_run["config"], setup_run["subject"], retention,
                            setup_run["inventory_raw"])
    with pytest.raises(PermissionError, match="signed private-storage approval"):
        PrivateRunStore(manifest=changed, authorization=setup_run["permission"], backend=setup_run["backend"])
    assert setup_run["backend"].inspect(first.run_capability)["manifest"] == first._manifest_raw
    first.close()


def test_backend_base_open_run_cannot_be_overridden_or_forged():
    from aethon.pilot_storage_backend import StorageBackend

    with pytest.raises(TypeError, match="open_run is final"):
        class BypassBackend(StorageBackend):
            def open_run(self, *args, **kwargs):
                return object()

    class NonCooperativeMixin:
        def __init_subclass__(cls, **kwargs):
            pass

    with pytest.raises(TypeError, match="open_run is final"):
        class MixinBypass(NonCooperativeMixin, StorageBackend):
            def open_run(self, *args, **kwargs):
                return object()

    with pytest.raises(TypeError, match="issued only"):
        ValidatedRunManifest(b"{}")
    from aethon.pilot_scientific_manifest import validate_manifest_document
    with pytest.raises(AttributeError, match="immutable"):
        object.__new__(ValidatedRunManifest)._canonical_bytes = b"{}"


def test_equal_but_reconstructed_authorization_cannot_mint_capability(setup_run):
    from dataclasses import replace
    original = setup_run["permission"]
    clone = replace(original)
    assert clone == original
    with pytest.raises(PermissionError, match="Expired or foreign"):
        clone.check(setup_run["subject"])
    backend = MemoryBackend()
    with pytest.raises(PermissionError, match="Expired or foreign"):
        backend.open_run(clone, canonical(setup_run["manifest"]), ResourceBudget())
    assert backend._runs == {} and backend._handles == {}


def test_runtime_collection_remains_fail_closed(setup_run):
    from aethon.pilot_runtime import collect_runtime
    with pytest.raises(PermissionError, match="Native capability storage unavailable"):
        collect_runtime(None, launch_path="synthetic")
