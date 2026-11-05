# Native backend implementation and validation plan

Scope: proposed verifier B and storage C+A/B, against the architecture documents.
Current state: **PILOT_BLOCKED; native prototype NOT_RUN**. This plan is not
approval to install dependencies, elevate a process, provision storage or run models.

## Work packages and concrete prerequisites

1. **Supply-chain proposal:** select an exact maintained Ed25519 library release,
   OS-specific artifact hashes, Python ABI/runtime, native linkage and SBOM. Obtain
   specific approval before changing declarations/locks. Do not use a floating
   distro package or development documentation version as the runtime pin.
2. **Verifier implementation:** narrow in-process API, strict Ed25519 encoding,
   no fallback, preserved canonical receipt/gate semantics; approved immutable
   runtime bootstrap and isolated imports. Validate dependency identity through
   installation and load, not a receipt-time hash race.
3. **Storage interface:** replace all pathname persistence with opaque run/object
   capabilities, exact root binding, transaction IDs, no-clobber publication,
   durable head CAS and recoverable errors. Do not enable the old check-only hook.
4. **Independent native adapters:** Linux dirfd/openat2 and Windows handle-relative
   operations, each with defined minimum OS/filesystem/ABI support and rejection
   of unsupported cases. Review native wrapper ownership/lifetime/error handling.
5. **Deployment and freshness:** approved isolated principal, immutable runtime,
   pre-provisioned encrypted private root, root/ancestor ACL receipts, no egress,
   retention/backups and independently administered head witness. Nothing here
   provisions those controls or creates signing/private production keys.
6. **Integration review:** connect only after adapter conformance, deterministic
   synthetic B0–B4/ledger regression and independent security review. Keep production
   disabled behind verified evidence until all gates and explicit launch consent.

## Platform matrix and evidence rules

| Environment | This review | Future acceptance |
| --- | --- | --- |
| Windows maintained Python 3.12 | Synthetic current/history suite and preservation PASS | Actual supported Windows/NTFS/build, restricted account and handle/DACL/error traces |
| Linux GitHub CI of #18 | All three overall jobs SUCCESS; Linux job covered #18 | New adapter-specific tests on native supported local filesystem with exact runtime |
| Ubuntu WSL Linux/Python 3.14.4 | Read-only capability inventory only | Not a substitute for approved Python 3.12 environment or native filesystem certification |
| Missing crypto/runtime packages | No installation or lock change | Approved exact artifacts available offline before any backend test |

An unavailable system, privilege, filesystem, power-loss test or dependency is
NOT_RUN/NOT_AUDITED, never a simulated native PASS. Mocked interleavings supplement,
not replace, real kernel behavior. A skipped native test blocks that platform's
claim. Keep Windows/Linux evidence and any WSL/DrvFS evidence separately labeled.

## Adversarial acceptance matrix

| ID | Synthetic setup / interleaving | Required result |
| --- | --- | --- |
| V01 | Valid/invalid Ed25519 vectors, wrong key, altered canonical bytes, malformed key/signature, unsupported provider | Exact valid only; all other cases deny, no subprocess/fallback |
| V02 | Replace/import-shadow Python package, extension or native dependency before bootstrap | Refuse unapproved runtime; no valid gate result |
| V03 | Mutable tool-path replacement/rename while verifying; external executable canary | In-process backend never consults/executes it; old native path remains unavailable |
| V04 | Policy+pin mismatch, key aliases, role confusion, expired/cross-run receipt, signed rejection | No authorization; distinct verified keys and independent pin retained |
| S01 | Replace root between observation/acquisition; foreign subject, volume/file ID or inode | Reject foreign root before private writes; no recovery via old pathname |
| S02 | Rename root/ancestor after holding capability using a second synthetic actor | No access to replacement; explicit custody-loss policy; recorded object identity unchanged or safely stopped |
| S03 | Swap symlink/junction/reparse/mount and use traversal, absolute path, device/ADS/hard-link tricks | Escape denied for every operation; no silent path normalization/downgrade |
| S04 | Change root/child/ancestor owner/mode/DACL and attempt access from another identity | Demonstrate actual OS isolation; revocation behavior matches declared control-plane policy |
| S05 | Existing conflicting write/delete/mapped handles, descriptor/handle leakage and reuse | Refuse unsafe acquisition or contain access; no inherited capability to an unapproved child |
| S06 | Interrupt before/after exclusive temp creation, write, file sync, publication, directory/metadata commit, journal commit and acknowledgment | No partial accepted artifact or overwrite; accepted receipt corresponds to defined durable state |
| S07 | Two writers, same ID/same bytes, same ID/different bytes, stale expected journal sequence | Idempotent same result; collision/concurrency rejected; no lost accepted commit |
| S08 | Crash after inference intent, after response publication, during voting and adjudication | No uncertain inference retry; reconcile durable result; no duplicate votes or invented review completion |
| S09 | Replay/copy checkpoint from foreign run/config/root; corrupt objects or journal gap | Refuse, preserve original artifacts and require explicit recovery disposition |
| S10 | Restore complete valid old snapshot of journal+objects | Independent head detects stale state or resume stays blocked; chain/fsync alone not accepted as proof |
| S11 | Attempt parent/child/native egress in an approved isolated synthetic test host | OS denies traffic and supplies evidence; do not contact an external production endpoint |
| S12 | Retention expiry, access revocation, private backup/snapshot and deletion exercise | Stop writes/reads per policy; erasure claim limited to actually evidenced media/backups |
| R01 | 4/4/4 families, exact 12 pairs/24 cases/120 slots and every failure/missing state | Complete structured accounting, no exclusion of absent observations |
| R02 | Change model/template/context/parameters/defense score before B4 reuse | Refuse reuse or suspend; identical source reused without another independent draw |
| R03 | One/unassigned/aliased evaluator, foreign case/response/rubric/span, conflict without distinct adjudicator | No SCIENTIFIC_REVIEW_COMPLETE until exact authenticated quorum/evidence policy |

Use benign synthetic executable canaries and generated dummy keys only. No real
malicious binary, live inference, private research inventory, external target or
paid operation is needed. Native ACL/account/firewall fixtures require separate
authorization on a disposable test system; never modify the user's production
identity or root to make a test pass. In-process HMAC mocks are not Ed25519 proof.

## Recording and pass criteria

Record exact source/runtime/package/kernel/filesystem versions, artifact and SBOM
digests, API flags, returned native errors, object IDs, transaction IDs, canonical
payload hashes, durable sequence/head, OS principal evidence and injected fault
barriers. Exclude keys, prompts/responses and real case identifiers from public
logs/CI. Keep all synthetic originals, failures and later runs under distinct IDs.

Each accepted write must identify its durability level; atomic visibility is not
power-loss durability. Use filesystem/device fault tests to justify the chosen
level. Windowed ACL observations cannot prove instantaneous revocation; an open
capability is not proof of fresh authorization. If complete host/witness rollback
is inside the adversary's power, obtain a truly separate freshness authority or
leave resume blocked. No API or Python interception fixes a compromised kernel.

For release of a backend, every mandatory row must pass on its claimed platform,
with no fallback, no unaccounted slots, no altered frozen scientific contract,
no unauthorized external call and independent sign-off. Verify historical 127/31/
six/9,139/80/five-LFS/five-local controls again before integration. Maintain the
NOT_AUDITED states for independent dataset identity and exact binary advisories
unless new independent evidence actually resolves them.

Potential future classification NATIVE_PROTOTYPE_VALIDATED applies only to the
exact synthetic systems exercised. It never satisfies scientific approval,
private data independence or operational launch authorization by itself.
