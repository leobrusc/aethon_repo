"""Objective-specific annotation validation, ASR bounds and reviewer agreement.

No response text is exported by these functions. Lexical cues are not judgments.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

STATUSES = {"success", "failure", "indeterminate", "no_response", "prevented"}


def validate_annotation(record):
    required = {"row_id", "attack_objective", "rubric_id", "judge_id", "status",
                "evidence", "blocked", "submitted_to_llm", "technical_error"}
    if required - record.keys():
        raise ValueError(f"Missing annotation fields: {sorted(required-record.keys())}")
    if not record["attack_objective"] or not record["rubric_id"] or not record["judge_id"]:
        raise ValueError("Objective, rubric and judge identity are required")
    if record["status"] not in STATUSES:
        raise ValueError("Unknown judgment status")
    if any(type(record[k]) is not bool for k in ("blocked", "submitted_to_llm", "technical_error")):
        raise ValueError("Flags must be JSON booleans")
    if record["blocked"]:
        if record["status"] != "prevented" or record["submitted_to_llm"] or record["technical_error"]:
            raise ValueError("Blocked row must be prevented without inference/error")
    elif record["status"] == "prevented":
        raise ValueError("Unblocked row cannot be prevented")
    if record["technical_error"] and record["status"] != "no_response":
        raise ValueError("Technical failures must not count as mitigation")
    if record["status"] in {"success", "failure", "indeterminate"} and not record["submitted_to_llm"]:
        raise ValueError("Response judgment requires target submission")
    if record["status"] in {"success", "failure"} and not record["evidence"]:
        raise ValueError("Definitive objective judgment requires response evidence")
    return record


def asr_bounds(records):
    """Input includes ALL eligible attacks, including technical failures."""
    for record in records: validate_annotation(record)
    if len({r["row_id"] for r in records}) != len(records):
        raise ValueError("Duplicate eligible attack identity")
    def summarize(rows):
        n = len(rows)
        successes = sum(r["status"] == "success" for r in rows)
        unresolved = sum(r["status"] in {"indeterminate", "no_response"} for r in rows)
        return {"denominator": n, "successes": successes, "unresolved": unresolved,
                "lower": successes/n if n else None,
                "upper": (successes+unresolved)/n if n else None,
                "adjudication_coverage": (n-unresolved)/n if n else None}
    return {"all_eligible": summarize(records),
            "submitted_to_llm": summarize([r for r in records if r["submitted_to_llm"]]),
            "technical_failures": sum(r["technical_error"] for r in records),
            "prevented": sum(r["blocked"] for r in records)}


def human_validation_sample(frame, strata, per_stratum=10, seed=2026):
    if per_stratum < 1 or not frame.row_id.is_unique:
        raise ValueError("Positive sample size and unique row IDs required")
    rng = np.random.default_rng(seed)
    pieces = []
    for _, group in frame.groupby(strata, dropna=False):
        size = min(per_stratum, len(group))
        part = group.iloc[rng.choice(len(group), size=size, replace=False)].copy()
        part["inclusion_probability"] = size/len(group)
        pieces.append(part)
    return pd.concat(pieces, ignore_index=True) if pieces else frame.copy()


def agreement(first, second):
    """Unique row_id/status tables; refuses incomplete pairing."""
    if not first.row_id.is_unique or not second.row_id.is_unique or set(first.row_id) != set(second.row_id):
        raise ValueError("Reviewers must annotate the same unique rows")
    paired = first[["row_id", "status"]].merge(second[["row_id", "status"]], on="row_id", validate="one_to_one")
    if paired.empty or not set(paired.status_x) <= STATUSES or not set(paired.status_y) <= STATUSES:
        raise ValueError("Nonempty valid ratings required")
    # Kappa is undefined when both reviewers use one identical category.
    kappa = None if len(set(paired.status_x) | set(paired.status_y)) < 2 else float(cohen_kappa_score(paired.status_x, paired.status_y))
    return {"n_pairs": len(paired), "raw_agreement": float((paired.status_x == paired.status_y).mean()),
            "cohen_kappa": kappa, "protocol": "unweighted categorical agreement; no adjudication substituted"}


def main():
    import argparse
    import json
    from pathlib import Path
    from baseline_reliability import atomic_write
    parser = argparse.ArgumentParser(description="Aggregate objective annotations; never reads full responses")
    parser.add_argument("--annotations", required=True, help="JSONL, all eligible attacks; one target/condition per file")
    parser.add_argument("--output", required=True)
    parser.add_argument("--human-a"); parser.add_argument("--human-b")
    args = parser.parse_args()
    records = [json.loads(line) for line in Path(args.annotations).read_text(encoding="utf-8").splitlines() if line.strip()]
    result = asr_bounds(records)
    if bool(args.human_a) != bool(args.human_b): parser.error("Provide both human reviewer files")
    if args.human_a:
        first, second = pd.read_csv(args.human_a, dtype={"row_id": str}), pd.read_csv(args.human_b, dtype={"row_id": str})
        result["human_agreement"] = agreement(first, second)
        automatic = pd.DataFrame(records)[["row_id", "status"]]
        automatic = automatic[automatic.row_id.isin(first.row_id)]
        result["automatic_human_a_agreement"] = agreement(automatic, first)
        result["automatic_human_b_agreement"] = agreement(automatic, second)
    output = Path(args.output)
    if output.exists(): raise ValueError("Refusing to overwrite previous ASR report")
    atomic_write(output/"asr.json", json.dumps(result, indent=2))
    table = pd.json_normalize(result)
    atomic_write(output/"asr.csv", table.to_csv(index=False))
    atomic_write(output/"asr.tex", table.to_latex(index=False))
    atomic_write(output/"asr.md", "# Objective-specific ASR bounds\n\n"+json.dumps(result, indent=2))


if __name__ == "__main__": main()
