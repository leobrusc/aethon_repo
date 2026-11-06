# Storage capability threat model

## Assets

- Run subject, complete immutable configuration and authorization provenance.
- Private prompt/checkpoint/response bytes and evaluation records.
- Pair/case/family identity, slot schedule, all terminal and nonterminal states.
- Hash-chained journal, operation receipts, checkpoint bindings and resource accounting.
- Reviewer votes, adjudication and audit trail.

## Trust boundaries

Untrusted inventory and stored bytes enter the collector/backend boundary. The Python facade enforces domain replay; `StorageBackend` is the sole intended run-persistence I/O boundary. The in-memory implementation is test-only and privileged test hooks can mutate it. Native root bootstrap, OS filesystem semantics, principal/ACL setup, kernel/administrator, external monotonic witness and human gate authorities are separate trust domains.

## Adversaries

1. Malformed inventory or manifest author attempting to change pairing, family quotas or schedule.
2. Storage corruption/replay actor changing objects, checkpoints, events, heads or receipts.
3. Concurrent/reentrant logical writer or stale facade.
4. Process interruption before commit or after commit before acknowledgment.
5. Whole-store rollback actor restoring a coherent old snapshot.
6. Compromised Python interpreter/process or privileged host operator (not contained by this API).

## Findings versus limits

SCI-REV-01 demonstrates a capability-boundary validation defect: pair/family and B3/B4 schedule constraints are not revalidated. Current runtime is disabled, limiting present operational exposure but not removing the prerequisite for a native backend.

Copied/foreign/closed capabilities, malformed IDs, object/checkpoint binding, corrupted journal and logical interruption are exercised by synthetic tests. They do not demonstrate resistance to reflection, monkeypatching, hostile Python code, process compromise, OS-level races, concurrent processes, permission revocation or power loss.

Complete coherent rollback remains a design limitation: hash chains cannot establish freshness if both journal and local witness are restored. A future backend needs an independently administered authenticated monotonic head witness before resume when rollback is in scope.

## Authorization conditions

No synthetic receipt grants SRC-02. Future native open must consume a trusted, independently issued root-object capability, immutable run grant, complete resource budget, expiry/revocation policy and freshness policy. A pathname or prior ACL observation is not a capability. The productive CLI currently refuses collection unconditionally. The eight external gates and operational authorization remain pending.
