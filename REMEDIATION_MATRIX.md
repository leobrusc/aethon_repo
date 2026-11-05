# Remediation and coverage matrix

Status: **REMEDIATION_REQUIRED; PILOT_BLOCKED**. No production fixes in this PR.

| ID | Severity / type | Reproduction | Required correction | Residual / prerequisite |
| --- | --- | --- | --- | --- |
| SRC-01 | High conditional defect | test_src01_replaced_verifier_is_used_without_revalidating_pin | Bind executable identity through invocation; verified immutable tool/ancestor deployment | Attacker needs write/rename to tool; launcher simulated; loader/OS trust remains |
| SRC-02 | High conditional defect | test_src02_replaced_storage_root_accepts_stale_observation | Compare signed probed file identity with live root; safe handles/ancestor ACLs | Attacker needs ancestor mutation; native ACL/encryption enforcement NOT_AUDITED |
| SCI-01 | Medium scientific contract gap | test_sci01_family_allocation_is_not_enforced | Exact frozen names and four matched pairs per family | Human semantic family review still required |
| SCI-02 | Medium evaluation contract gap | test_sci02_unassigned_judge_is_persisted_as_completed | Signed assignment membership; case/rubric/response binding; two votes and adjudication | Injected callback required; CLI judge=None mitigates default route |
| LIMIT-01 | Declared trust limitation | test_limitation_system_dispatch_is_not_an_os_sandbox | Native egress containment, reviewed subprocess policy | Local exit-only child proves dispatch escape, not actual network egress |
| LIMIT-02 | Declared design limitation | test_limitation_complete_empty_journal_rollback_has_no_anchor | Trusted external monotonic anchor or explicit accepted rollback threat boundary | Full valid snapshot rollback needs storage write access |
| CONTROL-01 | Expected rejection | test_control_foreign_subject_receipt_replay_rejected | Preserve subject binding | Independent key custody remains external |
| CONTROL-02 | Expected rejection | test_control_attacker_policy_rejected_by_independent_pin | Preserve independently obtained policy hash | Attacker control of both pin and policy is outside trust root |
| CONTROL-03 | Expected rejection | test_control_role_substitution_rejected | Preserve gate/kind/role checks | Human role assignment remains external |

Additional existing-suite coverage: 120 slots/idempotence; partial resume and
uncertain inference; atomic interruption; journal corruption/gaps; foreign run
objects and pointers; duplicate IDs; B3/B4 context/decision/score drift; missing,
truncated and failed generation; failed/interrupted evaluation; prompt echo;
template/revision/parameter/dtype/config drift; repository/worktree boundaries;
symlink/reparse rejection with platform fallback; unsigned, expired, wrong-role,
aliased-key and incomplete authorization; socket and Popen denial. Existing tests
are regression evidence, not independent native containment certification.

Native junction races, ACL revocation, encryption, deletion, power-loss durability,
model execution hardware and complete OS egress: NOT_AUDITED/NOT_RUN. No production
provisioning, network probe or real inference was performed. Technical/human/
scientific/operational evidence remain distinct; all eight actual gates PENDING.
