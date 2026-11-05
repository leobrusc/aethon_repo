"""Preflight and explicit local launch; default receipts remain PENDING."""
from __future__ import annotations

from datetime import date
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess

from aethon.pilot_collector import Collector, FrozenDefenses, make_manifest, validate_inventory
from aethon.pilot_governance import ReceiptAuthority, authorize, digest, read_external, verify_gates
from aethon.pilot_local import LocalGenerationAdapter, verify_assets
from aethon.pilot_storage import PrivateRunStore, discover_repositories, probe_storage
from aethon.prospective import BASELINE, CONDITIONS, GATES, fingerprint, preflight


def environment_observation():
    versions = {name: importlib.metadata.version(name) for name in ["torch", "transformers", "tokenizers", "numpy", "scikit-learn"]}
    return {"python": platform.python_version(), "system": platform.system(),
            "architecture": platform.machine(), "packages": versions, "cpu_count": os.cpu_count()}


def memory_observation():
    if os.name == "nt":
        import ctypes
        class Memory(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in ["total", "available", "page_total", "page_available", "virtual_total", "virtual_available", "extended"]]
        record = Memory(); record.length = ctypes.sizeof(record)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(record)): raise OSError("Memory observation unavailable")
        return record.total, record.available
    return os.sysconf("SC_PAGE_SIZE")*os.sysconf("SC_PHYS_PAGES"), os.sysconf("SC_PAGE_SIZE")*os.sysconf("SC_AVPHYS_PAGES")


def load_config(root):
    config = json.loads((root/"configs/science/collector_v1.json").read_text(encoding="utf-8"))
    if config["schema"] != "aethon.prospective-collector.v1" or config["baseline"] != BASELINE:
        raise ValueError("Unsupported collector baseline")
    if config["conditions"] != list(CONDITIONS): raise ValueError("Frozen arms changed")
    target = json.loads((root/"configs/science/target_v1.json").read_text())
    if (config["revision"] != target["model_revision"] or config["tokenizer_revision"] != target["tokenizer_revision"]
            or config["template_sha256"] != target["chat_template_sha256"] or config["asset_set_sha256"] != fingerprint(target["assets"])):
        raise ValueError("Frozen target identity changed")
    if fingerprint(config["generation"]) != fingerprint(json.loads((root/"configs/science/pilot_v1.json").read_text())["generation"]):
        raise ValueError("Frozen generation settings changed")
    for name, hashes in config["implementation_files"].items():
        path = (root/name).resolve()
        if root not in path.parents or digest(path.read_bytes()) not in hashes:
            raise ValueError("Collector implementation seal mismatch")
    return config


def inspect_runtime(root, *, inventory_path=None, private_root=None, run_id=None,
                    trust_policy=None, trust_policy_sha256=None, receipts=None):
    """No model loading, no directory creation and no execution capability."""
    root = Path(root).resolve()
    config = load_config(root)
    parent = preflight(json.loads((root/"configs/science/pilot_v1.json").read_text()), root)
    frozen_errors = [b for b in parent["blockers"] if b.startswith("frozen_file:")]
    forbidden = discover_repositories(root)
    if not all([inventory_path, private_root, run_id, trust_policy, trust_policy_sha256, receipts]) or frozen_errors:
        return {"classification": "PILOT_BLOCKED", "frozen_files": "FAIL" if frozen_errors else "PASS",
                "gates": {g: {"status": "PENDING", "reason": "external_evidence_not_supplied"} for g in GATES},
                "executed": False}, None
    raw = read_external(inventory_path, forbidden)
    inventory = json.loads(raw)
    if inventory["schema"] != "aethon.private-inventory.v1" or any(r.get("fixture_only") is not False for r in inventory["rows"]):
        raise ValueError("Real inventory must be independently sealed; public fixtures are ineligible")
    rows = validate_inventory(inventory["rows"])
    environment = environment_observation()
    code = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root):
        raise ValueError("Tracked experimental source must be clean")
    subject = {"baseline": BASELINE, "run_id": run_id, "code_commit": code,
               "inventory_sha256": digest(raw), "protocol_sha256": fingerprint(config),
               "storage_root_sha256": fingerprint(str(Path(private_root).resolve())),
               "environment_sha256": fingerprint(environment), "asset_set_sha256": config["asset_set_sha256"]}
    authority = ReceiptAuthority(trust_policy, trust_policy_sha256, forbidden)
    envelope_data = json.loads(read_external(receipts, forbidden))
    technical = {}
    # Only inspect expensive assets when an authenticated asset receipt is supplied.
    for gate in ["private_storage", "model_assets", "hardware_check"]:
        try:
            receipt = authority.verify(envelope_data[gate], gate, subject)
            claims = receipt["claims"]
            if gate == "private_storage":
                observation = probe_storage(private_root, forbidden, subject)
                if not claims["custodian"] or date.fromisoformat(claims["delete_after"]) <= date.today(): raise ValueError("Retention pending")
                technical[gate] = observation
            elif gate == "model_assets":
                target = json.loads((root/"configs/science/target_v1.json").read_text())
                technical[gate] = verify_assets(claims["snapshot_path"], target)
            else:
                total, free = memory_observation()
                technical[gate] = {"status": "PASS" if total >= 16*1024**3 and free >= 12*1024**3 and (os.cpu_count() or 0) >= 4 else "PENDING",
                                   "environment_sha256": fingerprint(environment), "memory_total_bytes": total,
                                   "memory_available_bytes": free, "native_network_isolation": "HUMAN_PLATFORM_RECEIPT_REQUIRED"}
        except (ValueError, KeyError, OSError):
            technical[gate] = {"status": "PENDING"}
    report = verify_gates(authority, envelope_data, subject, technical)
    return report, {"config": config, "subject": subject, "rows": rows, "authority": authority,
                    "envelopes": envelope_data, "technical": technical, "forbidden": forbidden}


def collect_runtime(root, *, launch_path, **kwargs):
    report, context = inspect_runtime(root, **kwargs)
    if report["classification"] != "READY_FOR_PILOT_REVIEW": raise PermissionError("Pilot remains blocked")
    launch = json.loads(read_external(launch_path, context["forbidden"]))
    permission = authorize(context["authority"], context["envelopes"], context["subject"], launch, context["technical"])
    storage = context["envelopes"]["private_storage"]["payload"]["claims"]
    retention = {"custodian": storage["custodian"], "delete_after": storage["delete_after"], "retention_plan_sha256": storage["retention_plan_sha256"]}
    manifest = make_manifest(context["rows"], context["config"], context["subject"], retention)
    store = PrivateRunStore(kwargs["private_root"], manifest, permission, context["forbidden"], context["technical"]["private_storage"])
    if store.suspended or store.summary()["accounting_complete"]: return store.summary()
    target = json.loads((Path(root)/"configs/science/target_v1.json").read_text())
    snapshot = context["envelopes"]["model_assets"]["payload"]["claims"]["snapshot_path"]
    # All 120 slots are durable before any model/classifier initialization.
    def factory():
        driver = LocalGenerationAdapter(snapshot, target, context["config"])
        defenses = FrozenDefenses(Path(root)/"src/models/aethon_tfidf_lr_revision.pkl", context["config"]["detector_sha256"])
        return driver, defenses
    # The collector acquires its writer lock before any model initialization.
    return Collector(store, context["rows"], context["config"], None, None, judge=None, factory=factory).run()
