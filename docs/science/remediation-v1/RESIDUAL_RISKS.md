# Residual risks and pending gates

Technical: **REMEDIATION_PARTIAL**. Operational: **PILOT_BLOCKED**.

| Risk / control | Evidence and disposition |
| --- | --- |
| Executable substitution and TOCTOU | Drift checks and unconditional production denial tested; native invocation/loader closure NOT_AUDITED |
| Root/ancestor substitution | Subject/object-bound stale observation rejection tested; production writes denied; handle confinement NOT_AUDITED |
| Windows ACL revocation / junction races | Not certified by stat modes or mocked reparse tests; native deployment NOT_AUDITED |
| Linux dirfd/object execution | Design assessed, not implemented/certified; Linux native execution NOT_RUN locally |
| Independent policy / receipt replay | Independent pin plus role, key, subject, time and hash checks retained; root distribution/key custody/revocation need humans |
| Whole-journal rollback | Hash chain detects corruption/gaps, not full valid snapshot rollback; independent monotonic anchor still absent |
| Subprocess/native egress | Python interception is not sandbox; OS egress verification remains required |
| Failure recovery | Synthetic intent/checkpoint/atomic/review recovery exercised; power-loss durability and hostile filesystem NOT_AUDITED |
| Host compromise | Administrator/kernel/interpreter/native-extension compromise outside application assurance; private encryption is not host protection |
| Scientific review truth | Signed identities and span/hash bindings authenticate provenance, not semantic correctness or reviewer independence/blinding |
| Review authorization lifetime | Ledger access requires the still-active run capability; post-expiry review needs a separately designed authorization workflow, not silent receipt replacement in an immutable run |
| Data independence | Structural quota checks do not certify novelty, semantic independence, licenses or final-holdout sealing |
| Historical raw dataset canonical digest | NOT_AUDITED without an independent trustworthy reference |
| Exact PyTorch binary vulnerability coverage | NOT_AUDITED; no new binary/security coverage claim |
| Future deletion / backups | NOT_AUDITED until performed and evidenced; no unapproved retention task provisioned |

The eight production gates remain **PENDING**: independent_inventory,
semantic_review, rubric_review, reviewer_assignment, private_storage, model_assets,
hardware_check, execution_authorization. Test keys, fixtures and synthetic approvals
are not real receipts. A valid signed receipt does not automatically execute a run.

Required next actions: independent remediation code review; finish and audit native
verifier/storage backends or adopt a separately approved architecture; obtain
real deployment receipts and OS isolation proof; appoint independent human reviewers;
seal a licensed independent pilot inventory and approved rubric/oracle bundle;
then request separate bounded operational authorization. No final campaign,
release, model download or inference is authorized by this change.
