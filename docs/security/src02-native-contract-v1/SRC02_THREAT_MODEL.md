# SRC-02 threat model

Status: design specification only. No native backend, root, witness service, ACL, or operational authority is created here.

## Security objectives and trust boundaries

Protected assets are the immutable scientific manifest v2 and its fingerprint; private prompts, generated continuations, and review votes; the B0–B4 slot ledger and linked objects; authorization and retention evidence; the journal/head; and the confidentiality, integrity, and retention of the private run store.

The trust chain is: independently governed provisioner and trust anchors → OS identity/filesystem bootstrap → held root capability → issued run authorization and validated immutable manifest → native backend → private run records. The inventory is untrusted data. It never names filesystem paths or supplies a root capability. The collector process is trusted only within its declared OS identity and reviewed immutable runtime. A future witness and post-collection reviewer authority are separate principals.

| Adversary / failure | Assumed capability | Required controls | Limit |
|---|---|---|---|
| Malicious or malformed inventory | Arbitrary bytes, duplicate/extra semantic fields, oversized structures | Canonical manifest v2 validation before capability mint; bounded parse; structured IDs; no path interpretation | Cannot establish human semantic correctness by structure alone |
| Non-privileged concurrent process | Read/write attempts, races, links, rename, lock contention within its OS rights | Exclusive collector identity; held directory handles; no-follow/beneath resolution; no-replace writes; OS lease; private DACL/mode | Existing handles, administrator rights, or same identity may defeat access separation |
| Filesystem-input attacker | Controls names/links/reparse entries and can race permitted directories | Handle/descriptor-relative complete boundary; reject link/mount escapes; identity checks at use | Does not defeat a privileged kernel or malicious filesystem implementation |
| Concurrent directory/ACL modifier | Rename/replace ancestor or change permissions where authorized | Trusted non-writable ancestors; held handles; revalidate identity and security policy; stop on policy change | ACL revocation semantics for already-open handles are OS-specific; fail closed but cannot promise instantaneous revocation |
| Corruption/truncation/media fault | Partial writes, missing records, bit rot, I/O errors | Hashes, sequence/CAS, redundant commit records as designed, durable ordering, strict recovery | Hashes detect mismatch, not malicious coherent replacement or all hardware faults |
| Process crash / power loss | Stop at any transaction boundary | Three-valued commit result, recovery protocol, flush evidence for supported stack; never retry uncertain inference | Durability is limited to certified OS/filesystem/device combinations |
| Snapshot/whole-store rollback | Restores internally valid old bytes | Independently administered monotonic witness checked before resume | No local hash chain detects a coherent full rollback; witness compromise/rollback remains a trust risk |
| Collector process compromise | Arbitrary operations under collector OS identity | Minimize privileges, immutable runtime, private store, egress control, separate approval keys and witness | Native storage cannot make a compromised authorized process honest |
| Administrator/kernel/host compromise | Alters code, handles, memory, ACLs, storage or witness client | Organizational separation, measured/controlled deployment, external witness where required | Out of technical guarantee; explicitly NOT mitigated by Python or filesystem API alone |

## Non-goals and release invariant

No guarantee is claimed against a compromised kernel, administrator controlling all trust domains, malicious storage firmware, or arbitrary code execution in the collector process. No automatic restart is permitted when root identity, policy, authorization, witness freshness, or commit disposition is uncertain. Scientific protocol, B0–B4, thresholds, rubric, manifest v2 and fingerprint formula remain frozen.

## Evidence references

- `SRC02_STORAGE_DECISION.md` (PR #19, `7431d7b423bc6fc34d1db51c12794742481f8428`): selected C + A/B architecture and original trust assumptions.
- `docs/science/storage-capabilities-v1/STORAGE_CAPABILITY_API.md`: synthetic API, structured IDs, immutable binding and volatile receipt contract.
- `docs/science/storage-capabilities-v1/NATIVE_BACKEND_REQUIREMENTS.md`: per-platform prerequisites.
- `docs/science/storage-capability-review-v1/NATIVE_INTERFACE_GAP_ANALYSIS.md`: current contract gaps.
- `docs/science/authorization-final-review-v1/SRC02_NATIVE_DESIGN_READINESS.md`: unresolved readiness items after AUTH-REV-01 closure.

Current disposition stays `SRC-02 NOT_AUTHORIZED`, `DEPENDENCY_APPROVAL_REQUIRED`, `PILOT_BLOCKED`; eight gates `PENDING`.
