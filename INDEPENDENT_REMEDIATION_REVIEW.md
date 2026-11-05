# Independent remediation review of PR #18

Verdict: **ARCHITECTURE_READY; PILOT_BLOCKED**. This means that the reviewed
remediation, target architecture and validation plan are documented with supporting
software evidence. It does not mean NATIVE_PROTOTYPE_VALIDATED, closure of SRC-01/02,
validated production deployment or permission to execute a pilot.

## Scope and recovery

Reviewed HEAD: `be5827af4345f44e6083ed3b7c84692a7772f113` (#18). Historical
reproduction HEAD: `355e07d9bb20200df953628d49f20368d6439e54` (#17).
Scientific #15 `1c6fc01edef58cc1565a7c233c7a23722a4d72a1` and collector #16
`aa6d171d82961aa297808c24ac602076abf47883` remain unchanged, open/draft and
correctly dependent. Observed origin/main is engineering baseline
`9ed55709add0fc45f63847a0394315863faa0876`; local main remains its preexisting
`2964556` and was not checked out or changed. The original dirty research checkout
and its five files remain preserved by hash. Existing worktrees were retained.

Review branch: `review/native-security-architecture-v1`, worktree
`.worktrees/native-security-review`, derived exactly from #18. All four #17 reports
and all four remediation reports were read; the #17-to-#18 functional diff includes
the collector, governance, runtime, storage, identity and review modules, source
seals and changed/new tests. This branch adds no changes to those production files,
manifests, original review tests, archived demonstrations, dependencies or locks.

## Reproduction and acceptance evidence

Run `native-review-20261105T184211Z`, maintained Windows Python 3.12 environment:

Commands, expected exit codes, raw output hashes, CI snapshot, platform inventory,
disposition and reproduction driver are retained under
`docs/science/native-security-v1/evidence/`, indexed by `index.json`. No fixture
directories, generated private keys or response objects are published.

| Check | Result and interpretation |
| --- | --- |
| Original #17 reproduction suite at exact #17 HEAD | PASS: nine tests; vulnerable acceptance was reproduced, not approved |
| Current suite at #18 production source plus four new review tests | PASS: 253 tests, one expected mocked-download warning, zero skips |
| Ruff / pip check | PASS |
| Current preflight | Expected exit 2; PILOT_BLOCKED; all eight real gates PENDING |
| Python network audit, both test sessions | PASS: zero connection/DNS audit events; no native egress certification |
| 127 protected files / 31 indexed artifacts / six historical manifests | PASS |
| Historical B3/B4 pairs / published metric comparison | PASS: 9,139 pairs, zero label/decision differences; all 80 values match |
| Git LFS | PASS: fsck and five hydrated SHA-256 payload identities |
| Five original local files | PASS: all original hashes preserved |
| Whitespace and publication guards | PASS; scoped staged/committed checks recorded with publication evidence |
| Native backend prototype | NOT_RUN; selected dependency/profile is not approved/available |

Historical tests ran in the existing clean #17 worktree with newly identified
synthetic temporary directories and logs, not against current fixtures. The two
archived canonical test payloads were compared to git show at #17 and to their
stored SHA-256 values before execution. The independent-review test hash is
`82ae38a051f93666a02ef0da4c897aa05ed9409a50f066b224f11770b1094dbd`;
the original collector test hash is
`c747d64d87d67826c9bcb3ad0ab7d48878ad0f673d176a1587993fc187e54825`.
No archived assertions or earlier results were overwritten.

The four new tests independently assert: complete structured identities and 4/4/4
allocation; collection completion without scientific completion; two conflicting
votes followed only by the designated adjudicator; B4 review resolving through its
verified B3 source rather than fabricating another independent observation. They
reuse documented synthetic scaffolding, not production keys or reviewers.

## Finding reassessment

| Finding | Historical behavior | Current evidence | Disposition |
| --- | --- | --- | --- |
| SRC-01 | Replaced verifier accepted controlled launcher success | No pathname invocation; replacement/identity/dependency failure and unchanged tool all deny production execution | Contained by denial, native capability NOT_AUDITED |
| SRC-02 | New root accepted under stale observation | Exact authorized probe/subject/object identity required; stale root rejected before creation; no native backend means no production writes | Contained by denial, native capability NOT_AUDITED |
| SCI-01 | One family accepted all 12 pairs | Exact canonical families and four matched pairs each enforced; unknown, incomplete, duplicate and skewed inventories rejected | Original structural defect remains corrected |
| SCI-02 | One unassigned callback judgment marked completed | Callback output rejected; assigned distinct-key signed votes bind slot/case/response/rubric/span, two votes and distinct adjudication required | Original callback/quorum defect remains corrected in synthetic contract tests |

No new demonstrated bypass of the defined authorization boundary was found in this
review. This is a bounded conclusion, not a proof of absence of bugs. Native
interfaces are intentionally absent, and injected test verifiers/confinement remain
trusted application code outside the CLI. Their synthetic success cannot authorize
a real run. The check(root) seam must not be promoted as a native I/O backend.

Scientific distinctions remain intact: B0 bypass; B1 L1; B2 historical L2; B3 L1 OR
L2 before generation; B4 same decision plus noisy audit. All arms share the exact
inventory; IDs preserve 12 task pairs/24 cases/120 slots. B3/B4 require compatible
input/configuration and decision fingerprints; a reused response is dependent.
Only decoded generated continuation reaches evaluation. Missing/truncated/error
slots remain accounted, and no synthetic ASR or efficacy statistic is computed.
Two assigned keys do not themselves prove independent people or correct judgments;
semantic membership, blinding and truthful rubrics remain human gates.

## CI and actual platform scope

[CI #42085443533](https://github.com/leobrusc/aethon_repo/actions/runs/42085443533)
associated with exact #18 HEAD completed SUCCESS. Jobs:
research-and-gpu-audit `127449166279`, cpu-development (windows) `127449166597`,
cpu-development (linux) `127449166716` all completed/success. The initial observation
was in_progress; the later completed snapshot is archived with query-head binding.
That CI exercised #18, not a native backend or a new production environment.

Local Windows validation used the maintained hashed Python 3.12 environment.
Read-only Ubuntu WSL inventory found Linux kernel
`6.18.33.2-microsoft-standard-WSL2`, Python 3.14.4, dir_fd/O_NOFOLLOW capabilities
and a distro cryptography package, but no pytest/numpy/pandas/sklearn. Windows has
no installed cryptography/PyNaCl in the maintained environment, and no such package
declarations were found in current requirements. No Linux suite was installed or
executed locally and no distro package was adopted as an AETHON dependency.
The WSL query initially required sandbox escalation; it did not install, provision
or reconfigure the distribution. Linux CI results and local WSL capability inventory
are explicitly different kinds of evidence.

## Residuals and recommendation

Post-expiry human-review authorization is still an explicit future workflow;
the run capability cannot silently be renewed in an immutable run. Review evidence
files must remain available for replay. Global scientific sign-off/complete
denominator reporting is not furnished by per-response review completion. Error-rate
denominator clarification is still pending. These constraints remain documented;
they are not silently treated as native closure or new scientific findings.

Independent raw-dataset canonical identity, exact PyTorch binary vulnerability
coverage, OS egress, actual ACL/encryption/retention deployment, native junction
races, crash durability and full rollback freshness remain NOT_AUDITED where not
independently evidenced. No final holdout is established by these software tests.

Approve an explicit dependency/profile proposal and implement the native storage
API described in the decision documents under a new review. Obtain per-OS evidence
and independent deployment receipts before changing fail-closed defaults. The eight
gates remain PENDING: independent_inventory, semantic_review, rubric_review,
reviewer_assignment, private_storage, model_assets, hardware_check,
execution_authorization. Separate explicit operational authorization remains required.
