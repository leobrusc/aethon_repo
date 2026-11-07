"""Independent review reproductions; acceptance here documents a PR #25 gap.

These tests intentionally pass only while the current backend incorrectly
accepts the malformed manifests described in STORAGE_SECURITY_REVIEW.md.
They are not contract acceptance tests and must become rejection tests when
the backend validation is remediated.
"""
import copy

from aethon.pilot_storage import PrivateRunStore
from pilot_memory_backend import MemoryBackend
from test_pilot_collector import setup_run


def test_review_repro_accepts_invalid_pair_and_family_quotas(setup_run):
    manifest = copy.deepcopy(setup_run["manifest"])
    original_run_fingerprint = manifest["run_fingerprint"]
    for slot in manifest["slots"]:
        slot["pair_id"] = "one-pair-for-every-case"
        slot["family_id"] = "unrecognized-family"

    # A trusted inventory validator would reject this before manifest creation;
    # open_run is itself the capability boundary receiving that manifest.
    store = PrivateRunStore(manifest=manifest, authorization=setup_run["permission"], backend=MemoryBackend())
    assert len({slot["pair_id"] for slot in store.manifest["slots"]}) == 1
    assert {slot["family_id"] for slot in store.manifest["slots"]} == {"unrecognized-family"}
    assert store.manifest["run_fingerprint"] == original_run_fingerprint
    store.close()


def test_review_repro_accepts_b4_before_b3_in_frozen_schedule(setup_run):
    manifest = copy.deepcopy(setup_run["manifest"])
    original_run_fingerprint = manifest["run_fingerprint"]
    slots = {slot["slot_id"]: slot for slot in manifest["slots"]}
    b4 = [slot_id for slot_id in manifest["schedule"] if slots[slot_id]["condition"] == "B4"]
    rest = [slot_id for slot_id in manifest["schedule"] if slots[slot_id]["condition"] != "B4"]
    manifest["schedule"] = b4 + rest

    store = PrivateRunStore(manifest=manifest, authorization=setup_run["permission"], backend=MemoryBackend())
    assert store.manifest["run_fingerprint"] == original_run_fingerprint
    positions = {slot_id: index for index, slot_id in enumerate(store.manifest["schedule"])}
    for sample_id in {slot["sample_id"] for slot in store.manifest["slots"]}:
        arms = {slot["condition"]: slot["slot_id"] for slot in store.manifest["slots"] if slot["sample_id"] == sample_id}
        assert positions[arms["B4"]] < positions[arms["B3"]]
    store.close()
