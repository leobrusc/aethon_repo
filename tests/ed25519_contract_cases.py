"""Prepared provider acceptance corpus. No provider import or crypto implementation.

Only an explicitly approved future adapter may be supplied to run acceptance.
The current phase tests this harness's rejection behavior, NOT Ed25519 correctness.
"""
import base64
import json
from pathlib import Path

PREFIX = bytes.fromhex("302a300506032b6570032100")


def public_vectors():
    path = Path(__file__).parent/"fixtures/ed25519_public_vectors.json"
    return json.loads(path.read_text())["vectors"]


def pem(raw):
    return b"-----BEGIN PUBLIC KEY-----\n"+base64.b64encode(PREFIX+raw)+b"\n-----END PUBLIC KEY-----\n"


def acceptance_cases():
    first, second = public_vectors()
    key = pem(bytes.fromhex(first["public_key_hex"]))
    message = bytes.fromhex(first["message_hex"])
    signature = bytes.fromhex(first["signature_hex"])
    for vector in [first, second]:
        yield vector["id"], pem(bytes.fromhex(vector["public_key_hex"])), bytes.fromhex(vector["message_hex"]), bytes.fromhex(vector["signature_hex"]), "VALID"
    yield "wrong-key", pem(bytes.fromhex(second["public_key_hex"])), message, signature, "INVALID"
    yield "modified-message", key, message+b"x", signature, "INVALID"
    yield "invalid-signature", key, message, b"\x00"*64, "INVALID"
    yield "truncated-signature", key, message, signature[:-1], "INVALID"
    yield "oversized-signature", key, message, signature+b"x", "INVALID"
    yield "raw-key-not-spki", bytes.fromhex(first["public_key_hex"]), message, signature, "INVALID"
    yield "malformed-key", b"not a public key", message, signature, "INVALID"
    yield "alternative-algorithm", key.replace(base64.b64encode(PREFIX+bytes.fromhex(first["public_key_hex"])), base64.b64encode(bytes.fromhex("302a300506032b6571032100")+bytes.fromhex(first["public_key_hex"]))), message, signature, "INVALID"


def run_approved_provider_acceptance(verify):
    """No discovery/import/fallback; require an explicit callable from later approval."""
    for name, key, message, signature, expected in acceptance_cases():
        result = verify(key, message, signature)
        if result == "UNSUPPORTED": raise RuntimeError("Provider unavailable; cryptographic acceptance NOT_RUN")
        assert type(result) is str and result in {"VALID", "INVALID"}, name
        assert result == expected, name


def illustrative_boolean_bridge(result):
    """Test-only specification of the future bool boundary; not production code."""
    if result == "UNSUPPORTED": raise PermissionError("Provider unavailable")
    if type(result) is not str or result not in {"VALID", "INVALID"}: raise ValueError("Unexpected verifier result")
    return result == "VALID"
