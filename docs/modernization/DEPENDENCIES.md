# Dependency audit

No existing dependency or fixed version was removed from the full installation.
`requirements.txt` now includes the core and optional research lists. The union
preserves all 21 previous declarations and adds three directly used dependencies
that previously relied on transitive installation: torch, huggingface-hub,
pyarrow (Parquet), and the developer tooling listed separately.

| Group | Declarations and verified paths |
| --- | --- |
| Core scientific | numpy, pandas, scipy, scikit-learn, joblib, statsmodels: detection, grouped selection, statistics, serialization |
| Reporting | matplotlib: research curves; historical rendered outputs preserved |
| Model/baseline runtime | torch, transformers, tokenizers, huggingface-hub: drivers, offline baseline tests, pinned snapshots |
| Data engine | pyarrow: `dataset_loader.py` reads canonical Parquet train/test files |
| API runtime | openai, python-dotenv: lazy API drivers and ASR judge; no real API evaluation in CI |
| Optional GPU/model stack | accelerate, bitsandbytes, sentencepiece, sentence-transformers: retained for HF/GPU/external research paths; no local deletion justified |
| Optional research compatibility | datasets, seaborn, opacus, tiktoken, pyyaml, tqdm: no direct imports found for several; external protocols and transitive/dynamic use not disproven; REVIEW, retained |
| Development | pytest, pytest-cov retained; Ruff, pre-commit, pip-audit and build added for explicit checks |

The direct import graph is `import-graph.json`. Static absence is insufficient to
delete optional research dependencies: `model_registry.py` imports drivers lazily,
HF models select tokenizers/quantization integrations dynamically, and external
notebooks or remote execution may use the full requirements list. Existing
`tokenizers==0.20.0` and `sentencepiece==0.2.2` constraints remain unchanged.
Transformers' compatible version is resolved against the tokenizers constraint;
this is not a new lock for historical experiments.

`pip install -e '.[dev]'` installs the CPU development surface without the ten
optional full-stack declarations. `pip install -e '.[research,dev]'` or the legacy
requirements files request the full environment. This reduces mandatory scope
without removing capabilities. CUDA builds and gated weights remain operator
choices; CPU tests do not validate CUDA execution.

The validation environment is an observation, not a portable lock. Original
scientific environment evidence in `docs/research_2026_evidence/` remains unchanged.
An initial tooling install selected setuptools 84, conflicting with installed
torch 2.12's `<82` requirement; the build backend is now bounded to `>=68,<82`
and local validation corrects that tooling version. No runtime research package
was automatically upgraded to suppress vulnerability findings.

Known vulnerabilities from the actual environment are recorded in
`dependency-audit.json`. The CI audit fails on known advisories; a failing draft
check is evidence requiring review, not permission to change historical runtime
constraints without a validated migration. There are no blanket advisory ignores.

GitHub's clean CPU environment independently reported 102 advisory entries in
four packages; offline tests passed. The scanner skipped the local project and
the exact `torch 2.14.1+cpu` build because they were not catalogued on PyPI.
That build remains NOT_AUDITED by pip-audit; a separate upstream-version and
binary provenance review is pending. Counts can include duplicate advisory IDs
or aliases and are not claims of distinct exploitable vulnerabilities.

Packaging follows [setuptools' pyproject configuration](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html).
Workflows use read-only tokens and full Action SHAs as described in
[GitHub's secure use reference](https://docs.github.com/en/actions/reference/security/secure-use).
