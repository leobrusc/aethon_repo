# AETHON pre-merge audit

Audit snapshot: 2026-11-05. Repository `leobrusc/aethon_repo`; refs were fetched
with `git fetch origin --prune`. No merge or remote ref update was made. PR #4
checks refer to exact head `147747cf855dbacbb221f2074908dde1b0c77860`.

## Git inventory

| Ref / PR | SHA | Base SHA | Ahead / behind | GitHub state |
| --- | --- | --- | ---: | --- |
| `origin/main` | `29645563bd64a67aae2482ab6c87bd5e32fecb11` | — | — | unchanged |
| #1 `research/jorge-2026-experimental-upgrade` | `544c363c19a08574d30e7e2c064a78ce1bdfb601` | revision `6ec4b8156a62e79c7a5337343858bc684861f2aa` | 20 / 0 | OPEN, draft, MERGEABLE |
| #2 `refactor/repository-modernization-2026` | `a6090ae3030ef52f333fe14380839df4a7d879eb` | research `544c363` | 7 / 0 | OPEN, draft, MERGEABLE |
| #3 `security/dependency-hardening-2026` | `3ca7eaff5dc91701ecf7ea0dabdf7f185700a035` | modernization `a6090ae` | 5 / 0 | OPEN, draft, MERGEABLE |
| #4 `validation/experimental-readiness-2026` | `147747cf855dbacbb221f2074908dde1b0c77860` | security `3ca7eaf` | 8 / 0 | OPEN, draft, MERGEABLE |

Each base is an ancestor of its head. `origin/main` is an ancestor of PR #4:
60 commits ahead, zero behind. `git merge-tree --write-tree` for those refs
produced a tree with no conflicts. GitHub marked all four PRs mergeable when
queried. Recheck exact refs at merge time because concurrent pushes can change
them.

The PR heads' source commits are nested, but a GitHub merge commit written only
to a PR's current target branch is not automatically inherited by its child
source branch. The existing scientific merge commit already in the research
history is present; hypothetical merge commits for the current open PRs do not
yet exist. See [the corrected strategy comparison](INTEGRATION_PLAN.md).

The main-to-final diff has 384 paths: 360 added, 21 modified and three deleted;
127,882 insertions and 39,570 deletions. PR #4 against its direct base changes
123 files, with 14,134 insertions and 7 deletions. The three files deleted from
main are empty `.Rhistory`, `json` and `pd` placeholders. There are no renames.
The large textual reduction includes replacement of canonical JSONL copies by
LFS pointers. It is not a dataset purge.

All five canonical JSONL files are LFS-tracked. `hf_red_team_attempts.jsonl`
uses LFS OID `1b197f9c836ce9a927f7d82f8c48c27439ad713ddcf2958a87faa7f09be2effd`;
the other four OIDs are available from `git lfs ls-files --long`. LFS payload
identity and PR4 scientific integrity checks passed. The largest ordinary
tracked result inspected is the 6,718,635-byte historical prompt-level CSV; it
is scientific evidence, not a temporary. Trusted detector pickles and all six
historical manifests are present and hash-checked. No >100 MB Git blob was found.

The original checkout remains at `544c363` on the research branch with five
pre-existing user changes. Existing modernization, security and validation
worktrees remain at their recorded SHAs. This audit uses its own clean worktree;
the original dirty checkout is not part of the proposed integration.

## Consolidated review and checks

| Area | State | Findings |
| --- | --- | --- |
| Architecture, CLI, dynamic imports | PASS | Installable `src/aethon/` namespace and legacy module paths coexist; lazy registry remains. Historical HF driver can be explicitly selected. |
| Scientific code and historical outputs | PASS | L1/L2/L3 and B0–B4 retained. 127 protected files, 31 evidence files, six historical manifests and 9,139 paired records verified. No historical result change found. |
| Precision and output contracts | PASS, scoped | Explicit dtype, unsupported-configuration rejection and observed parameter/forward state; token boundary separates prompt, continuation and legacy full text. Ambiguous full-text local drivers are excluded from ASR. |
| Bounded real model inference | PASS | Llama 1B FP32 in both stacks; Qwen 3B BF16 CPU in maintained stack. Three Llama inputs match IDs/continuation/stop reason across stacks. This is no statistical/scientific equivalence claim. |
| Dependencies and wheel provenance | PASS, scoped | On 2026-11-05, seven upstream advisory queries were refreshed against existing locks: 0 findings and 0 scanner skips. No installs or lock changes. Historical vulnerable runtime remains restricted to reproduction. |
| Exact PyTorch binary coverage | NOT_AUDITED | Build-specific scanner skips remain visible. Hashes establish identity, not binary safety. |
| GitHub Actions | PASS | `contents: read`; checkout, setup-python and upload-artifact actions pinned to full SHAs; no `pull_request_target`. Both push and PR workflows pass on the exact PR4 SHA. |
| Secrets and large-file guard | PASS | Repository guard passed; no secret finding. Real inference used fixed public-authored smoke inputs. |
| Datasets and generated files | PASS | Canonical datasets tracked with LFS and payload hashes verified. Three removed files are empty placeholders. |
| Citation and licensing | REVIEW | `CITATION.cff` has basic citation fields but no version, release date, DOI or license. No LICENSE/LICENCE/COPYING file. Resolve ownership and license before a tagged release or redistribution. |
| Prospective science and GPU | NOT_RUN | No NVIDIA execution, independent ASR campaign, semantic-overlap review or powered equivalence study. Smoke runs establish operation only. |

The aggregate `git diff --check origin/main...head` emits whitespace diagnostics
from inherited CRLF-preserved lock/evidence files and historical SVG/text. The
direct PR4 diff passes scoped guard and whitespace checks; CI repository guards
pass. Do not bulk-normalize protected bytes to suppress inherited diagnostics.

Exact checks for `147747c`:

| Check | State | Evidence |
| --- | --- | --- |
| GitHub PR workflow | PASS | [Run 41706951671](https://github.com/leobrusc/aethon_repo/actions/runs/41706951671): Linux CPU, Windows CPU and research/GPU-audit jobs all successful |
| GitHub push workflow | PASS | [Run 41706937393](https://github.com/leobrusc/aethon_repo/actions/runs/41706937393): all jobs successful |
| Maintained tests, Ruff, pip check | PASS | 141 passed; lint clean; no broken requirements |
| Historical contract tests | PASS | 18 passed in existing historical interpreter, no environment update |
| Integrity and paired replay | PASS | 127 + 31 + six manifests; 9,139 pairs and B0–B4 replay in both stacks, zero mismatches |
| Build, isolated install, CLI | PASS | Wheel, target install, seven CLI help checks and bounded dry-run |
| Upstream security queries | PASS | Seven refreshed 2026-11-05 lock queries, zero matched findings/skips, no suppressions; raw reports and hashes in `evidence/security-audits/` |
| Exact PyTorch binary audit | NOT_AUDITED | Native scanner skips retained |
| CUDA and final scientific campaign | NOT_RUN | No NVIDIA device; prospective protocol gates remain open |

There is no identified engineering integration blocker. Decision:
**READY_FOR_REVIEW**. This is neither merge approval nor authorization for a final
scientific campaign. Obtain maintainer review of residual vulnerability scope
and license ownership before distribution.
