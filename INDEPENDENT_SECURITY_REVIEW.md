# Independent review of PR #16

Verdict: **REMEDIATION_REQUIRED; PILOT_BLOCKED**. Review target is exactly
`aa6d171d82961aa297808c24ac602076abf47883`, dependent on PR #15
`1c6fc01edef58cc1565a7c233c7a23722a4d72a1`; engineering baseline is
`9ed55709add0fc45f63847a0394315863faa0876`. This review adds reproductions and
reports only. It does not repair, authorize or execute the prospective collector.

The seven requested implementation/test files were inspected against the frozen
protocol, rubric, independence audit and pilot plan. Synthetic test infrastructure
from PR #16 is reused, with independent assertions in
`tests/test_independent_security_review.py`. Passing reproduction tests mean the
undesired behavior was observed, not that the finding was fixed.

## Demonstrated findings

### SRC-01 — High, conditional: verifier executable identity is checked only once

Location: `pilot_governance.OpenSSLVerifier.__init__` / `__call__`.
The constructor hashes a pathname; later subprocess invocations execute that
pathname without checking its current identity. Test
`test_src01_replaced_verifier_is_used_without_revalidating_pin` replaces an owned
synthetic tool after construction. A controlled launcher observes the replacement
and returns the two successful tool responses; an arbitrary 64-byte signature is
accepted. No malicious binary was executed and no Ed25519 algorithm break is claimed.

Exploitation requires write/rename access to the verifier file or its parent
between validation and use. Such access does not require control of the Python
process or the independently pinned policy. Impact is loss of receipt-authentication
assurance if this deployment condition exists. Immutable administrator-managed
tool placement and parent ACLs mitigate it, but are not enforced here. Require
verified immutable deployment/handle identity at execution, including dependencies;
re-hashing alone still leaves a race. Residual trust: OS, administrator and loader.

### SRC-02 — High, conditional: stale storage observation accepts a replacement root

Location: `pilot_storage.PrivateRunStore.__init__`, `guard`; integration:
`pilot_runtime.collect_runtime`. The constructor checks observation status and
path hash, then records the *current* directory inode as its new baseline. It does
not compare that identity with the probed identity. Test
`test_src02_replaced_storage_root_accepts_stale_observation` renames an owned root,
creates a distinct inode at the same path, and successfully writes the manifest
using the prior observation and capability. This is an actual filesystem identity
replacement; ACL/encryption observations in the scaffold are synthetic, not a
claim of native ACL exploitation or a successful production authorization.

An actor needs rename/create rights on a writable ancestor during preflight-to-open.
Different ACL inheritance on the replacement can expose private outputs. Existing
post-construction inode checks do not close this initial gap. Bind the probed
device/file identity to the signed observation and require a matching live check
before opening; retain safe directory handles and enforce trusted ancestor ACLs.
Residual races, ACL changes and Windows durability require OS-specific validation.

### SCI-01 — Medium: frozen family allocation is not validated

Location: `pilot_collector.validate_inventory`. The protocol and pilot plan require
four task pairs in each of instruction-override, synthetic-disclosure and
answer-contamination. Test `test_sci01_family_allocation_is_not_enforced` supplies
all 12 otherwise-valid pairs in one family and the validator accepts it. This
does not bypass a conscientious human inventory review; it demonstrates a missing
technical consistency check. Validate the exact frozen family names and four-pair
quotas before constructing slots. Semantic membership still needs independent review.

### SCI-02 — Medium: completed judgment is not bound to reviewer assignment

Location: `pilot_collector.Collector._evaluate`. Test
`test_sci02_unassigned_judge_is_persisted_as_completed` supplies an unregistered
judge ID and an unchecked evidence reference. One definitive judgment is persisted
and the slot becomes completed. Neither signed assignment membership nor the two
independent votes/adjudication contract is enforced by this callback path.
This needs an application-supplied callback; the default CLI passes `judge=None`
and leaves evaluation pending, so it is not a default CLI authorization bypass.
Bind evaluation to assigned identities, rubric version, slot and response hash;
preserve two raw votes and distinct adjudication before marking scientific review
complete. Human correctness and blinding remain external obligations.

## Limitations and controls, separated from defects

- Attacker-selected policy plus attacker-selected pin is an untrusted root, not
  a cryptographic bypass. An independently pinned policy rejects substitution.
- Role/subject substitution is rejected. Original tests additionally cover expired
  receipts, key aliases, dispositions, missing gates and foreign checkpoints.
- `no_external_calls` is explicitly defense in depth, not an OS sandbox. The new
  local-shell `exit 0` test proves `os.system` is outside its interception. It sends
  no network traffic. Native processes/extensions require OS egress enforcement.
- The journal checks internal gaps/checksums, not rollback against an external
  monotonic anchor. Moving all owned synthetic events/objects/pointers aside makes
  the initial empty state acceptable again. This test preserves moved artifacts;
  it does not claim partial rollback is undetected or execute another inference.
  A writable full snapshot can therefore reset accounting. External anchoring or
  a trusted append-only custodian is needed if rollback resistance is required.
- Junction/symlink rejection is covered by the original platform-dependent test
  (which can simulate a link where privileges are absent). Native junction races,
  directory-handle confinement, sudden power loss, ACL revocation, actual encrypted
  production storage, key custody/revocation and firewall enforcement: NOT_AUDITED.
- Exact PyTorch binary vulnerability coverage and independent canonical raw
  dataset digest remain NOT_AUDITED. No inference, weights or services were used.

## CI and release decision

GitHub Actions [42077406746](https://github.com/leobrusc/aethon_repo/actions/runs/42077406746),
queried for the exact examined commit, is completed/success: cpu-development
(linux), cpu-development (windows), research-and-gpu-audit all SUCCESS.
That validates the existing suite, not the absence of these adversarial defects.
Local evidence and preservation checks are indexed in `review-evidence/`.

Run `independent-review-20261105T175758Z`: **214 passed, one expected mocked-download
warning, zero skips** (205 existing plus nine independent checks). Ruff, pip check,
127/31/six integrity verifiers, LFS fsck/five hydrated payload hashes, whitespace,
9,139 paired decisions with zero mismatches, all 80 historical metric values and
five original local-file hashes PASS. Both offline preflights and the deliberately
unauthorized collect invocation returned expected exit 2 with PILOT_BLOCKED;
the latter was a denial test, not a pilot. The Python audit observed zero network
events; child/native egress was not certified. Python 3.12 maintained security
environment was reused without installations or dependency changes. Local audit
service rescans were NOT_RUN to respect the no-external-calls restriction; the
exact-head CI supplies the three successful dependency-audit job results.

Two preliminary test invocations had temporary-directory setup errors (sandbox
access, then missing parent), not assertion failures. The isolated parent was
created and the seven initial reproductions passed before the final nine-test
review/full-suite run. No production directory or permission was provisioned.

All eight production gates remain PENDING: independent_inventory, semantic_review,
rubric_review, reviewer_assignment, private_storage, model_assets, hardware_check,
execution_authorization. No fixture approval is production approval. Close the
findings, independently review remediation, validate OS assumptions, satisfy every
gate and obtain a separate explicit operational launch authorization before pilot.
