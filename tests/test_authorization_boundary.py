"""Synthetic adversarial tests for the operational authorization boundary."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from aethon.pilot_governance import Authorization
from aethon.pilot_storage import PrivateRunStore
from aethon.pilot_storage_backend import InvalidCapability, ResourceBudget, canonical
from pilot_memory_backend import MemoryBackend
from test_pilot_collector import setup_run
import aethon.pilot_governance as governance
from aethon.pilot_review import ReviewLedger


@pytest.mark.parametrize("override", [lambda self, subject: None, lambda self, subject: True])
def test_unissued_authorization_subclass_cannot_open_facade_or_backend(setup_run, override):
    legitimate = setup_run["permission"]
    forged_type = type("ForgedAuthorization", (Authorization,), {"check": override})
    forged = forged_type(**legitimate.__dict__)
    backend = MemoryBackend()

    with pytest.raises(PermissionError, match="Exact issued"):
        PrivateRunStore(manifest=setup_run["manifest"], authorization=forged, backend=backend)
    assert backend._runs == {} and backend._handles == {}

    with pytest.raises(InvalidCapability, match="Exact issued"):
        backend.open_run(forged, canonical(setup_run["manifest"]), ResourceBudget())
    assert backend._runs == {} and backend._handles == {}


def test_equal_dataclass_clone_and_manual_base_instance_cannot_open_run(setup_run):
    legitimate = setup_run["permission"]
    clone = replace(legitimate)
    manual = Authorization(**legitimate.__dict__)
    assert clone == legitimate and manual == legitimate
    for candidate in (clone, manual):
        backend = MemoryBackend()
        with pytest.raises(InvalidCapability, match="Expired or foreign"):
            backend.open_run(candidate, canonical(setup_run["manifest"]), ResourceBudget())
        assert backend._runs == {} and backend._handles == {}


def test_application_api_has_no_direct_issuer_registration_route():
    subject = {"run_id": "synthetic-unissued"}
    manual = Authorization("0" * 64, "1" * 64, "2" * 64,
                           "2099-01-01T00:00:00+00:00", "3" * 64)

    assert not hasattr(governance, "_AUTHORIZATION_ISSUER")
    assert not hasattr(governance, "_record_issued_authorization")
    assert not hasattr(governance, "_ISSUED_AUTHORIZATIONS")
    assert not hasattr(governance, "_make_authorization_api")

    backend = MemoryBackend()
    with pytest.raises(PermissionError, match="Expired or foreign"):
        PrivateRunStore(manifest={"subject": subject}, authorization=manual, backend=backend)
    with pytest.raises(InvalidCapability, match="Expired or foreign"):
        backend.open_run(manual, canonical({"subject": subject}), ResourceBudget())
    assert backend._runs == {} and backend._handles == {}

    fake_store = SimpleNamespace(authorization=manual, manifest={"subject": subject})
    with pytest.raises(PermissionError, match="Expired or foreign"):
        ReviewLedger(fake_store, authority=None, rubric_bundle_path=None)
    assert backend._runs == {} and backend._handles == {}


@pytest.mark.parametrize("field,value", [
    ("policy_sha256", "f" * 64),
    ("receipts_sha256", "e" * 64),
    ("launch_sha256", "d" * 64),
    ("retention_plan_sha256", "c" * 64),
])
def test_mutated_issued_authorization_snapshot_is_rejected(setup_run, field, value):
    store = setup_run["store"]()
    permission = store.authorization
    original = getattr(permission, field)
    object.__setattr__(permission, field, value)
    try:
        with pytest.raises(PermissionError, match="Expired or foreign"):
            store.guard()
        with pytest.raises(PermissionError, match="Expired or foreign"):
            store.backend.read_head(store.run_capability)
    finally:
        object.__setattr__(permission, field, original)
        store.close()


def test_subject_change_and_unissued_copy_do_not_create_state(setup_run):
    permission = setup_run["permission"]
    backend = MemoryBackend()
    manifest = setup_run["manifest"]
    changed_subject = dict(manifest["subject"], run_id="foreign-run")
    forged = replace(permission, subject_sha256="0" * 64)
    with pytest.raises(InvalidCapability):
        backend.open_run(forged, canonical(manifest), ResourceBudget())
    assert backend._runs == {} and backend._handles == {}
    from aethon.pilot_governance import require_issued_authorization
    with pytest.raises(PermissionError):
        require_issued_authorization(permission, changed_subject)


def test_legitimately_issued_synthetic_authorization_preserves_full_storage_cycle(setup_run):
    # setup_run obtains Authorization only through authorize() after all synthetic
    # gate receipts, technical checks, and launch intent have been verified.
    store = setup_run["store"]()
    assert len(store.slots) == 120
    key = store.put({"fixture": "synthetic", "only": True})
    assert store.put({"fixture": "synthetic", "only": True}) == key
    store.append({"kind": "suspend", "reason": "synthetic test checkpoint"})
    assert store.sequence == 1
    store.close()

    reopened = setup_run["store"]()
    assert reopened.sequence == 1 and reopened.get(key) == {"fixture": "synthetic", "only": True}
    assert reopened.summary()["scientific_review_status"] == "REVIEW_PENDING"
    assert len(reopened.slots) == 120
    reopened.close()
