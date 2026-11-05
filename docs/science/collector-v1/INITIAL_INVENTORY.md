# Phase 2 initial inventory — before implementation

Engineering anchor: `9ed55709add0fc45f63847a0394315863faa0876`.
Science parent: `1c6fc01edef58cc1565a7c233c7a23722a4d72a1` (draft #15).
New branch/worktree: `science/prospective-collector-v1`, `.worktrees/prospective-collector`.
Remote main and #15 were checked at these anchors. Original checkout remains at
544c363 with its two modified and three untracked files. No existing worktree or
branch was moved. No receipt, signature, reviewer or execution authorization exists.

| Existing component | Interface/evidence | Gap / implementation boundary |
| --- | --- | --- |
| Five docs/science documents | Frozen v1 hypotheses, target, 24 cases/120 slots | New implementation supplement; retain original seals |
| configs/science/pilot_v1.json | Eight pending receipt gates, frozen-file hashes | File/hash flags alone do not authenticate review or authorize execution |
| target_v1.json | Exact Llama/model/tokenizer revision, six asset hashes, FP32/template | Fresh runtime asset/precision/hardware verification still required |
| aethon.prospective | Identity/preflight/continuation review, 17 tests | No complete collector; no independent redecoding; no durable run journal |
| generation.v1 / precision.v1 | Structured IDs/continuation, explicit dtype, local-only weights | Adapter must supply messages, independently re-decode generated interval, bind effective input and settings |
| research_e2e.run_pairs | B0/B3, injected driver, private checkpoints | No full B0–B4 matrix/chat forwarding; own-root-only storage check; mutable run marker |
| BenchmarkMiddleware | B0 bypass; B1 L1; B2 L2; B3 L1 OR L2; B4 same decision + DP count | Wrap unchanged implementation and verified detector hash; never reinterpret labels |
| Historical evidence | 127 scientific hashes, 31 evidence payloads, six manifests, 9,139 pairs, 80 metric values | Revalidate without rewriting any historical artifact |
| 161-test science suite | Software tests only, no approved pilot | Extend using synthetic drivers/inventories only |

The request's shorthand B3 “post-response” / B4 “calibrated cascade” conflicts
with its instruction to preserve the frozen operational definitions. Implementation
uses the frozen table above and does not move B3 after generation or change B4.
A separate scientific protocol would be required to adopt those new meanings.

Planned interfaces: signed governance receipts bound to an independently pinned
trust policy and exact run subject; live read-only storage probes; append-only
private journal and content hashes; local generation/defense adapters; collector
with complete 120-slot planning and crash reconciliation; offline preflight CLI.
Receipt identity, technical verification, human/scientific review and operational
authorization remain separate. Default launch state stays PILOT_BLOCKED.

No production ACL/directory will be created in this task. All storage, interruption,
signature and model-interface tests use temporary synthetic fixtures. No ASR or
efficacy estimate will be calculated from them; no target model will be loaded.
