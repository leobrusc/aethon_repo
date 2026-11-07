"""Synthetic proof that the module-private issuer token is callable in-process."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, "src")
sys.path.insert(0, "tests")

from aethon.pilot_governance import Authorization, _AUTHORIZATION_ISSUER, _record_issued_authorization
from aethon.pilot_storage import PrivateRunStore
from pilot_memory_backend import MemoryBackend
from test_pilot_collector import setup_run

fixture_function = setup_run.__wrapped__
fixture = fixture_function(Path(tempfile.mkdtemp(prefix="aethon-auth-review-")))
manual = Authorization(**fixture["permission"].__dict__)
backend = MemoryBackend()
_record_issued_authorization(manual, issuer=_AUTHORIZATION_ISSUER)
store = PrivateRunStore(manifest=fixture["manifest"], authorization=manual, backend=backend)
print({
    "manual_object_is_original": manual is fixture["permission"],
    "registered_by_private_api": True,
    "capability_created": store.run_capability is not None,
    "backend_run_count": len(backend._runs),
    "slots": len(store.slots),
})
store.close()
