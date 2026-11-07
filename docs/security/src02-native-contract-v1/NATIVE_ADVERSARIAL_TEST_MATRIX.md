# Native adversarial validation matrix

Status vocabulary: `PASS` means the exact supported OS/kernel/filesystem profile passed with preserved logs; `FAIL` is a reproducible violated invariant; `NOT_RUN` means no native implementation/test was performed. This design phase marks all native rows `NOT_RUN`.

| ID | Fault/adversary | Observable acceptance criterion | Profile | Status |
|---|---|---|---|---|
| T01 | `..`, absolute path, device name, ADS | Rejected before I/O; no run/object | Linux + Windows | NOT_RUN |
| T02 | Symlink/magic link/junction/reparse swap | Rejected; no outside object read/write | Linux + Windows | NOT_RUN |
| T03 | Root/ancestor rename or replacement race | Operations stay on held identity or fail closed; never reopen by old path | Linux + Windows | NOT_RUN |
| T04 | Mount/device/volume change | Reject unsupported crossing; no downgrade | Linux + Windows | NOT_RUN |
| T05 | Owner/DACL/mode changes | Policy invalidated; no new commit; active lease stopped at safe boundary | Both | NOT_RUN |
| T06 | Two independent writer processes | One lease holder; stale fencing token cannot append/head-CAS | Both | NOT_RUN |
| T07 | Process death / abandoned lock | Successor gets higher token and recovers before writes | Both | NOT_RUN |
| T08 | No-replace collision / same op different bytes | Exact retry returns same receipt; different intent rejected | Both | NOT_RUN |
| T09 | Short write / disk full / quota exceeded | No durable receipt; no new side effect; uncertain slot preserved if effect began | Both | NOT_RUN |
| T10 | Flush/fsync failure at each barrier | `NOT_COMMITTED` only when proven; else `COMMIT_UNKNOWN`; no inference retry | Both | NOT_RUN |
| T11 | Crash after stage/write/publish/journal/head/witness | Recovery matches state-machine outcomes; no partial scientific completion | Both | NOT_RUN |
| T12 | Restart with stale or absent witness | Resume blocked; no local hash-chain-only acceptance | Both | NOT_RUN |
| T13 | Full coherent old snapshot restore | Witness detects lower/conflicting head and blocks | External witness + both | NOT_RUN |
| T14 | Revocation/expiry during run | New operations rejected; owned handles close; uncertain commit reconciled | Both | NOT_RUN |
| T15 | Object/checkpoint/event/inode/temp quota | Fail closed at exact boundary; counters and OS quota agree within policy | Both | NOT_RUN |
| T16 | Corrupt/truncated journal/checkpoint | Run poisoned; no silent repair or report | Both | NOT_RUN |
| T17 | Unknown inference result after crash | Slot remains `interrupted_unknown`; no automatic second model call | Both | NOT_RUN |
| T18 | Review grant/reviewer alias/replay | Only assigned independent votes accepted; quorum/adjudication enforced | Both | NOT_RUN |
| T19 | Recovery CPU/time/resource exhaustion | No partial accepted state; bounded incomplete recovery receipt | Both | NOT_RUN |

Synthetic tests can validate pure state transitions and canonical bindings. They cannot prove syscall confinement, NTFS/Linux durability, power-loss semantics, ACL revocation, filesystem quota enforcement, or external witness independence. Native results must include build/runtime identity, filesystem/mount configuration, test harness SHA, fault point, raw logs, run IDs and signed result receipt. No native tests were run in Phase 7A.
