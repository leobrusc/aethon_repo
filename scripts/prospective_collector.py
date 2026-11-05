"""Explicit offline preflight or separately authorized local collection. No APIs."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from aethon.pilot_runtime import collect_runtime, inspect_runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["preflight", "collect"])
    for option in ["inventory", "private-root", "run-id", "trust-policy", "trust-policy-sha256", "receipts", "launch"]:
        parser.add_argument("--"+option)
    args = parser.parse_args()
    options = {"inventory_path": args.inventory, "private_root": args.private_root, "run_id": args.run_id,
               "trust_policy": args.trust_policy, "trust_policy_sha256": args.trust_policy_sha256, "receipts": args.receipts}
    try:
        if args.mode == "collect":
            if not args.launch or not all(options.values()): raise PermissionError("Explicit launch and evidence required")
            result = collect_runtime(ROOT, launch_path=args.launch, **options)
        else:
            result, _ = inspect_runtime(ROOT, **options)
        # Gate report contains no inventory, prompt, response, exception text or private paths.
        if "gates" in result:
            result = {k: result[k] for k in ["classification", "executed"]} | {"gates": {k: {"status": v["status"]} for k, v in result["gates"].items()}}
        print(json.dumps(result, indent=2))
        return 2 if result.get("classification") == "PILOT_BLOCKED" or result.get("suspended") else 0
    except (ValueError, PermissionError, OSError, KeyError, TypeError):
        print(json.dumps({"classification": "PILOT_BLOCKED", "reason": "invalid_missing_or_unverifiable_evidence",
                          "executed": False if args.mode == "preflight" else None,
                          "recovery": "inspect_private_journal_before_any_retry" if args.mode == "collect" else None}))
        return 2


if __name__ == "__main__": raise SystemExit(main())
