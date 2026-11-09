# Safety Counterexample Regression

## Historical cases

The PR #36 files and reports remain byte-for-byte unchanged. `tests/test_src02_dedup_audit.py` asserts the old vulnerable outcomes; it is retained as a historical reproduction and excluded from default pytest collection with a documented `pytest.ini` ignore. It can still be run against PR #35's historical worktree. It is not an acceptance test for the corrected relation.

The PR #36 response-less trace now rejects at `persist_object`: after prepare and durable intent, there is no dispatch authorization, possible-dispatch marker, observed continuation, digest verification, or durable response. The state remains with no object and no head publication.

The PR #36 unavailable-witness trace now leaves `recovery_blocked=true`, witness query `UNAVAILABLE`, no witness acknowledgment, and no response acknowledgment. Recovery and new inference remain prohibited until the witness is restored and a fresh bound response is validated and reconciled.

The PR #34 false snapshot remains rejected. The epoch-7 stale writer is rejected after epoch-8 transfer with unchanged head. No native backend was exercised.

## Acceptance tests

The updated `tests/test_src02_safety_model.py` covers missing dispatch/response/durability, response binding and digest changes, uncertain retry, typed persistence/administrative operations, witness authentication/freshness/binding/conflict cases, timeout before/after remote commit, and lease transfer races. Test fixtures are synthetic; no ASR or scientific efficacy is estimated.
