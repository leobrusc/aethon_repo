# AETHON repository modernization — 2026-11-03

## Scope and initial diagnosis

Initial checkout: `research/jorge-2026-experimental-upgrade`, HEAD
`544c363c19a08574d30e7e2c064a78ce1bdfb601`, synchronized with origin after
`git fetch origin --prune`. Origin is `https://github.com/leobrusc/aethon_repo.git`.
There were 49 reachable commits and no tags. Main local/remote:
`2964556`. Local revision branch: `66644cc`, ahead 12/behind 1 versus remote
`6ec4b81`; it was not changed. The research branch contains the revision work
and its merge plus integrity, nested validation, baseline and DP evidence absent
from main. PR #1 is open/draft, research -> revision, head `544c363`.

The main checkout has preexisting edits to `src/close_harness.py` and
`tests/test_harness_closure.py` plus two validated backups and a patch. All five
remain outside modernization commits; their hashes are recorded in
`preserved-local-state.json`. No stash/reset/clean was used. Work was isolated in
`.worktrees/modernization`, branch `refactor/repository-modernization-2026`.
The original checkout retains its branch. Ignored datasets, results, weights,
caches and environments in that checkout were not removed or published.

The draft modernization PR targets the research branch, so its diff is restricted
to repository work and preserves PR #1 as an explicit dependency. Targeting main
now would mix the scientific study and its review with maintenance. After PR #1
merges, the maintainer can retarget without rewriting its scientific commits.
No merge, force push, remote branch deletion or history rewrite is authorized.

## Inventory, references and decisions

`file-decisions.csv` inventories **all 232 initially tracked files**, with paths,
classification, rationale, SHA-256 and size. `import-graph.json` records AST imports
for all tracked Python modules and tests. It is a reference graph, not proof of
unreachability. Entry-point review includes `run_*.py`, `research_*.py`, the
`model_registry.LazyDriver` dynamic imports, CLI documentation, tests, dataset
normalizers, historical model paths and `scripts/`. There was no Python packaging,
CI workflow, pre-commit configuration or contributor/security policy at the base.

The June inventory and cleanup plan were checked against the October research
report. Their four-test/clean-main observations are obsolete. The cleanup plan
recommended force pushes and history migration, incompatible with this task.
Both originals are archived byte-for-byte; root links now lead to current guidance.

| Classification | Decision and evidence |
| --- | --- |
| KEEP | All datasets, historical results, metadata, manifests, model binaries, source protocols, configs and regression coverage |
| REFACTOR | Legacy source stays compatible; additive installed CLI, explicit packaging and separated environment declarations |
| CONSOLIDATE | Requirements share two included runtime lists and one developer list; no duplicate runtime constraints; no independent research script proved redundant |
| REMOVE | Exactly `.Rhistory`, `json`, `pd`: each tracked, zero bytes, no content or behavior; names already ignored as session/scratch files |
| ARCHIVE | Original `INVENTORY_REPORT.md` and `GITHUB_CLEANUP_PLAN.md` -> `docs/archive/2026-06/`; root paths retain navigation |
| REVIEW | Historical plans, diagnostic scripts, unused-looking optional packages, local backups and checkpoints: external scientific use or uniqueness not disproven; preserved |

The ignored tree includes `.hf_cache/`, `venv/`, Python/pytest caches,
`datasets/*.official*`, a timestamped red-team backup, local model pickles,
`examples/`, generated smoke/diagnostic/model runs and private error text.
Caches are regenerable, but they remain outside the modernization worktree;
blanket cleanup would unnecessarily touch the user's environment. Local results
and backup datasets could contain unique evidence and are not deletion candidates.
The root `experiment_manifest.json` and historical `results/` are tracked despite
ignore patterns: they are preserved. No file was judged removable solely from
static absence of references.

## Architecture before and after

Before: flat `src/*.py`, packages `benchmark`, `loaders`, `baselines`, lazily
imported model drivers, mixed root plans, no installed namespace or CI.

After: `src/aethon/` provides a lazy command namespace and installed `aethon`
entry point. Existing modules, scientific protocols and artifact paths remain
stable. `pyproject.toml` explicitly includes 34 legacy modules and required
packages; distributions contain code, not scientific datasets/model binaries.
`docs/ARCHITECTURE.md` describes responsibilities and maps all seven commands.
`configs/` and protocol documents already describe experiments; no empty or
artificial `experiments/` tree was introduced.

L1 heuristic, L2 classifier and L3 noisy auditing remain unchanged. B0–B4
semantics and the distinction between prompt detection and response ASR remain
unchanged. No production scientific source was rewritten. Diagnostic scripts
remain available for external scientific use. The one existing test corrected
here writes its readiness fixture under pytest's temporary directory, avoiding
dependence on a generated local folder. The user's version of that file in the
original checkout remains intact.

## Scientific preservation and LFS

`scientific-integrity.json` records **127** protected files before cleanup:
canonical datasets/source documentation, all tracked results, configs,
`src/models/` artifacts/drivers, curated PR #1 evidence and the root manifest.
Both observed Windows checkout hashes and canonical Git payload hashes are kept.
Git autocrlf makes many existing checkout bytes differ from Linux blobs; verification
accepts only those two explicitly recorded representations, never arbitrary
normalization. It also verifies committed payloads and resolves LFS pointers to
their SHA-256 identities. No historical evidence or input was regenerated.

`scripts/verify_research_evidence.py --git-tree HEAD` independently validates the
31 curated evidence hashes. All 9,139 historical prompt identities, labels,
splits and B3/B4 records remain in the unchanged source/results artifacts.
The existing historical comparison script rechecks paired B3/B4 decisions without
new inference. Nested validation, baseline smoke, DP and NOT_RUN evidence from
PR #1 remain intact; no metric or historical result was edited.

The red-team file is still a **55,487,878-byte regular Git blob at base HEAD**,
object `5d02c5b4407123da98258738c7742bcc655ef16e`, originating in `f440b36`.
`.gitattributes` already applies LFS to JSONL, but that blob predated the rule.
Only this file is renormalized into an LFS pointer in a new commit. Its hydrated
hash is checked against the pre-cleanup baseline. The original JSON-array bytes
are preserved despite the historical `.jsonl` extension. The other four LFS
datasets remain unchanged.

The 55 MB historical blob remains reachable and old clones do not shrink.
Removing it requires separately authorized history rewriting, a recoverable
mirror and contributor coordination; none is performed here. There is no
`git lfs migrate --everything`, force push or destructive garbage collection.

## Dependencies, governance and security

See `DEPENDENCIES.md`: all 21 previous declarations and both exact pins remain
available in the full installation. Ten optional declarations are separated from
the CPU development default. Direct dependencies torch/huggingface-hub/pyarrow
are made explicit. **Dependencies removed: none**; missing evidence of optional
or external use prevents safe deletion. This is an environment-scope reduction,
not a claim of a smaller full GPU environment.

Ruff checks syntax and correctness without mass-formatting scientific code.
Pre-commit runs Ruff and a staged Git-blob guard. The guard checks new/modified
blobs above 5 MiB and recognizable credential formats without printing matches.
It reads Git object bytes so hydrated LFS data is not mistaken for large Git blobs.
It is a heuristic and does not establish absence of secrets. Historical hostile
corpora are preserved; no unrestricted corpus-wide content publication is needed.

GitHub Actions run offline CPU tests, integrity, CLI and changed-blob checks;
dependency audit is a separate blocking job with no blanket ignores. Actions are
pinned to verified upstream tag SHAs, use read-only contents permission and do
not persist checkout credentials. No `pull_request_target`, evaluation secrets,
cloud access or untrusted response execution is introduced. Dependabot covers
pip and Actions. CONTRIBUTING, SECURITY, AGENTS and a PR template define the
minimum workflow. CITATION metadata uses the README title and verified Git
author Leonardo Bruscagini; no DOI, publication venue, release date or license
was invented. A license decision remains with the maintainer.

The existing full Windows environment audit found **168 advisories in 14 packages**.
`dependency-audit.json` keeps IDs, versions, aliases and fixes; the verbose raw
response remains ignored under `results/modernization/`, with its hash recorded.
No vulnerable dependency was silently ignored or scientific runtime upgraded.
CI is red on dependency findings (102 entries in four resolved CPU packages),
while offline quality/integrity passes on GitHub. Addressing them needs a separately validated
runtime/model compatibility migration. A clean security bill is not claimed.

## Validation record and limits

The original dirty checkout passed **106 tests** before changes, including four
uncommitted harness tests. The committed scientific base has **102 tests**.
In the isolated checkout, one of those depended on an ignored generated directory
and failed with FileNotFoundError. It now uses `tmp_path`. All 102 tracked tests
and nine new dispatch/guard regression cases pass: **111 passed**, one expected
mock-download warning. The four user-only tests are deliberately outside the PR.

Ruff and the 127-file scientific verification passed locally. Curated evidence
verification passed for all 31 artifacts. Build, installed entry points, full
dependency resolution, publication and final checks are recorded in
`VALIDATION.md` after execution. The observed dependency environment is archived
in `validation-environment.txt`; it is not a portable GPU lock.

Publication completed in [draft PR #2](https://github.com/leobrusc/aethon_repo/pull/2).
Both GitHub push/PR runs at code commit `ed64d78` passed all 111 offline tests,
Ruff, CLI and hash guards. Full remote outcomes and scanner coverage limitations
are recorded in `VALIDATION.md`. Fresh CPU dependency dry resolution succeeded
with 99 install candidates. Git LFS fsck and upload succeeded.

The local installation smoke uses a separate editable environment reusing the
existing scientific site-packages. A complete clean GPU environment, real model
inference, gated weights, target API calls, human response evaluation and cloud
execution are NOT_RUN. CPU mocks and `--help` do not count as experiments.
Full baseline/LLM/GCP runs remain pending exactly as in the research report.

Future work: independently validate security upgrades and a portable CPU/GPU
lock, define a license, audit semantic dataset overlap, execute the pending
prospective and response-level studies, and separately validate deeper source
moves if justified. None of these is represented as completed here.
