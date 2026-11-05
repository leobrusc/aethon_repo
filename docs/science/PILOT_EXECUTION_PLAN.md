# Pilot execution plan v1.0.0

**PILOT_BLOCKED; execution NOT_RUN.** This request authorizes preparation only.
Manifest: `configs/science/pilot_v1.json`; target/assets: `target_v1.json`.

## Proposed bounded pilot

One Llama-3.2-1B revision, CPU/FP32, greedy seed 2026, four threads/inter-op=1,
batch=1, max 1024 input/256 new tokens. New private development pool: 12 attacks +
12 matched clean controls; four task pairs per instruction-override, synthetic
disclosure and answer-contamination family. B0–B4 account for 120 slots; full B3/B4
fingerprint equality permits B4 response reuse, at most 96 calls/24,576 new tokens.
There is no inferential power/efficacy claim. Public synthetic fixtures are excluded.

Hardware planning gates: >=16 GiB RAM, >=12 GiB free, one worker, adequate encrypted
private disk. These are planning limits, not a measured memory/latency guarantee.
Verify actual model hashes, CPU support and peak memory at launch. No GPU, paid
API, cloud provisioning, judge API or weight download is part of this preparation.

## Offline commands

```powershell
python -m pytest -q tests/test_prospective_preparation.py
python scripts/prepare_prospective_pilot.py --manifest configs/science/pilot_v1.json --fixtures tests/fixtures/prospective_pilot_v1.json --output results/science/preflight-NEW-ID
```

Preflight writes only gate/fixture accounting, never loads a model or computes ASR.
Exit 2 / PILOT_BLOCKED is expected for the checked-in pending plan. There is no
inference CLI. Four synthetic fixtures and stubbed pytest cases are software checks,
not an executed pilot or reuse of the 21 historical smokes as scientific evidence.

## Launch receipts — all pending

| Gate | Required concrete evidence |
| --- | --- |
| independent_inventory | Licensed, sealed private 24-case source/task inventory and pre-output exclusions |
| semantic_review | Complete prior-data coverage, pinned screen, two blinded reviewers, family ledger |
| rubric_review | Scenario oracles/examples and signed task/objective rubrics |
| reviewer_assignment | Two named independent reviewers, adjudicator, blinding plan |
| private_storage | Absolute external path, custodian, ACL/encryption/backup verification, deletion date |
| model_assets | Fresh six-file hashes plus template/revision/dtype receipts |
| hardware_check | CPU/RAM/disk/thread and offline-access receipts |
| execution_authorization | Separate explicit permission for the frozen local pilot schedule |

Receipts need private absolute paths, SHA-256 and reviewer ID. Preflight checks
their local identities, not authenticity or operator authority. Flipping PASS
strings neither grants consent nor triggers execution.

## Future sequence — not executed

1. Seal protocol/manifests and science code commit; reject dirty experimental code.
2. Verify offline assets, private storage, oracles and fixed paired schedule.
3. Compute frozen B0–B4 decisions; verify B3/B4 equality. Review a complete B0–B4
   collector: existing research_e2e.run_pairs is only B0/B3 and its private-root
   check alone is insufficient for the all-worktree storage policy.
4. Collect explicit blocked/error/generated slots with structured generation.v1;
   preserve token boundary/config/stops privately; judge only new continuation.
5. Suspend on identity/privacy/contract drift, memory exhaustion, unexpected
   network or >10% errors after first complete paired batch. Keep failed slots;
   resume only identical fingerprints with atomic private checkpoints.
6. Blind/double-review every pilot response and adjudicate separately. Report
   accounting, coverage, technical failures, resource use and rubric feasibility.
7. Require all 120 slots accounted with no contract/privacy/identity errors before
   feasibility sign-off. Revise development material under new versions if needed.
   Final campaign needs a separate independent holdout and signed power plan.

Never overwrite an existing run. Do not publish raw prompts/responses, token IDs,
oracles or private reviewer evidence. No prospectively collected case is promoted
back into the historical results or final confirmatory pool.
