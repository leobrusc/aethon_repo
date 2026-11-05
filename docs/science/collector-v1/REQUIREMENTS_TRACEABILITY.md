# Phase 2 requirements traceability

Status: implementation prepared for review; operational classification PILOT_BLOCKED.

| Requirement | Implementation | Synthetic verification |
| --- | --- | --- |
| Existing contracts/inventory before edits | INITIAL_INVENTORY.md; unchanged PR #15 sources/seals | Parent head and frozen-file preflight |
| Frozen B0–B4 | FrozenDefenses wraps original middleware/model hash | Explicit bypass/block accounting and B3/B4 mismatch tests; historical replay |
| Complete 24x5 matrix | validate_inventory / make_manifest | 120 unique slots before calls, deterministic shuffled-input identity |
| Source/scenario/family/pair preservation | Immutable slot fields, structured sample and case IDs | Duplicates/collisions, matching pair-task contexts |
| Chat/revision/dtype/generation | LocalGenerationAdapter / check_result | Template/revision/parameter/dtype/input-boundary drift rejected |
| Continuation-only evaluator | Independent token decoding + injected judge/private queue | Prompt/full-text marker never reaches judge; exact generated-ID span |
| All outcomes retained | Explicit terminal/pending states and all-slot manifest | Missing, empty, truncated, inference/evaluation errors; no efficacy calculation |
| B3/B4 reuse fingerprint equality | Decision-component and full request equality; source references | Decision/score/context divergence refuses reuse and suspends |
| Idempotent resume | Immutable pointers/objects and durable intent events | Normal pause, inference interruption, durable response reconciliation, evaluation interruption |
| Atomic writes / no overwrite | Flush/fsync + no-clobber hard links | Interrupted publication, duplicate identical bytes, changed-object collision |
| Corruption / writer isolation | Content SHA, journal sequence/previous hash, owned writer lock | Corrupt object, middle-chain deletion, foreign lock retained |
| Private root / all worktrees | NUL-safe Git discovery, path/link checks, read-only probes | Repository/relative/symlink/reparse rejection and unverified security observation |
| ACL/encryption/retention receipts | Live probe binding and concrete signed retention plan | Pending proof rejected; policy does not enable encryption/change permissions |
| Eight authorization gates | External trust policy, Ed25519, roles/quorum/subject/expiry/evidence | Unsigned flags, stale/foreign/role-mismatched evidence cannot authorize |
| Receipt is not execution | Explicit independently signed launch intent, re-verification | Report alone creates no run; fabricated capability rejected; CLI missing authorization blocked |
| No external calls | Offline-only adapter; socket/DNS/process guard; stdout suppression | Actual networking denied by test fixture; attempted network/process inference suspended |
| Historical preservation | Existing inventory/evidence/dependency verifiers; dedicated replay | 127 files, 31 artifacts, six manifests, 9,139 pairs, 80 metrics, LFS, original five files |
| No invented approvals/results | Null receipt templates and PENDING default config | Offline preflight expected exit 2; no target model loaded |

Limitations needing external review: genuine deployment ACL/encryption/retention,
identity/key provisioning and revocation, native filesystem power-loss/rollback
assurance, actual cached model/hardware availability and OS network isolation.
Unit stubs and synthetic signatures are NOT evidence that those operational gates
are satisfied. Exact PyTorch binary vulnerability catalog and independent canonical
raw-dataset digest remain NOT_AUDITED. Historical vulnerable environments are not
used for new hostile inputs. No final campaign or release is prepared for execution.
