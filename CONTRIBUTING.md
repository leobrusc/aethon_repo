# Contributing to AETHON

Start from the scientific branch required by your study. Repository modernization
is stacked on `research/jorge-2026-experimental-upgrade` (draft PR #1); keep that
dependency visible when choosing the base of a pull request.

Install Git LFS, run `git lfs pull`, and use maintained Python 3.12.13 profiles
from `docs/security/REPORT.md`. Historical 3.10 environments are isolated under
the documented reproduction procedure. After activating the hashed development
environment, run:

```bash
python -m pre_commit install
python -m ruff check src scripts tests
python -m pytest -q
python scripts/repository_inventory.py verify
python scripts/verify_research_evidence.py --git-tree HEAD
```

Run experiments from the repository root with an editable installation. Datasets
and historical evidence stay outside the Python distribution. Use
the dedicated Linux GPU lock for CUDA. `requirements/historical/pr2/` preserves
the original full environment, including known vulnerabilities; do not reuse it
for new untrusted-input processing. Do not combine CPU and CUDA wheel profiles.

Use semantic, focused commits. Document changes to scientific methods, data,
labels, thresholds, seeds and evaluation populations explicitly. Historical inputs
and outputs are immutable; new experiments use new run IDs and provenance.
Detection metrics concern prompts; ASR concerns responses and requires eligible
denominators, coverage and objective-specific judgments. Report unavailable runs
as NOT_RUN or BLOCKED. A dry run or mock does not establish real model performance.

Before deleting code, check imports, CLI use, dynamic registry entries, serialized
module paths, research protocols and external execution instructions. Record
KEEP/REFACTOR/CONSOLIDATE/REMOVE/ARCHIVE/REVIEW decisions with evidence. REVIEW
items remain intact. Preserve contributors' uncommitted changes.

Do not upload raw private prompts, credentials or generated checkpoints. Run
`python scripts/repository_guard.py --staged` before committing. Existing dataset
files may contain hostile instructions; handle them as untrusted test data.
