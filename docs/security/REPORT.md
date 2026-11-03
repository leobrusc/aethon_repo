# Security remediation and dependency hardening — 2026-11-03

Base: PR #2, commit `a6090ae3030ef52f333fe14380839df4a7d879eb`.
Work is isolated in branch `security/dependency-hardening-2026`, dependent on
`refactor/repository-modernization-2026`. The original dirty scientific checkout
and PR #2 worktree remain untouched. No merge, force push or history rewrite.

## Findings and analytical normalization

Inputs: `docs/modernization/dependency-audit.json` and the actual failed GitHub
Actions security logs from run
[41670595461](https://github.com/leobrusc/aethon_repo/actions/runs/41670595461).
The original report and all scientific artifacts are preserved, not rewritten
to conceal findings. `scripts/security_matrix.py` uses transitive alias components
across PYSEC/CVE/GHSA identifiers; it never supplies exclusions to a scanner.

The original **168 Windows + 102 Linux CI occurrences = 270 entries** normalize
to **132 package/vulnerability groups (132 distinct identities)**. Every scanner
ID, version and source occurrence is retained in the JSON. Original-input hashes
are recorded, and enrichment comes from OSV records plus the GitHub Advisory API
when a CVE is only an alias. No occurrence is discarded from scanner evidence.

- [Complete CSV matrix](vulnerability-matrix.csv): package, versions, canonical
  vulnerability and aliases, severity/CVSS vectors, priority, exploitation surface,
  affected AETHON paths, upstream fixes, compatibility and technical decision.
- [JSON matrix](vulnerability-matrix.json): same analysis plus every original
  occurrence and metadata source. Severity absent upstream remains UNKNOWN.
- [Prioritized remediation](REMEDIATION_PLAN.md): P0 model/serialization/file/build
  paths precede P1 network, image and cache processing.

Potential reachability was checked against actual imports, dynamic driver loading,
model `from_pretrained`, snapshot downloads, optional research packages, and
trusted pickle/joblib use. A package-level path is not proof that every reported
advisory is exploitable through the public AETHON CLI. All affected maintained
dependencies were upgraded rather than suppressing alerts based on that uncertainty.

## Maintained environment boundaries

Maintained profiles use Python **3.12.13** and uv **0.13.7** for resolution.
The old Python 3.10/tokenizers 0.20 environment is retained separately, not
advertised as a safe default. Existing commands and scientific algorithms remain
unchanged; only dependency declarations, tooling, tests and controls change.

| Profile | Exact locks | Purpose and limits |
| --- | --- | --- |
| CPU | `cpu-{windows,linux}-py312.lock` | Core detection, canonical local datasets, reporting/API clients; no optional research stack |
| Development | `dev-{windows,linux}-py312.lock` | CPU plus tests, Ruff, pre-commit, scanner and build tooling |
| Research CPU | `research-{windows,linux}-py312.lock` | CPU plus modern HF datasets, Accelerate, sentence-transformers, DP/research tools |
| GPU | `gpu-linux-py312.lock` | Research plus bitsandbytes and official torch 2.14.1+cu130; CUDA execution NOT_RUN |

The seven complete transitive locks include hashes and official direct PyTorch
wheel URLs. The small `bootstrap.lock` pins/hashes pip and uv. Roots in
`requirements-*.txt` describe intent; use locks for reproducible installation.
Do not mix CPU/CUDA builds. There is no GPU Windows validation claim.
Numerical scientific versions remain fixed at the previously observed versions.

For an activated Python 3.12.13 controller environment with pip, from the root:

```bash
python -m pip install --isolated --require-hashes --only-binary=:all: -r requirements/environments/bootstrap.lock
python scripts/install_security_environment.py requirements/environments/dev-linux-py312.lock .venv-dev
.venv-dev/bin/python -m pytest -q
.venv-dev/bin/python scripts/audit_security_environment.py requirements/environments/dev-linux-py312.lock --installed
```

On Windows use the `dev-windows` lock and `.venv-dev/Scripts/python.exe`.
The installer only manages its marked `.venv-*` folders inside this worktree;
it refuses unrelated existing or historical environments. It installs external
binary distributions with hashes before building only the local editable project.
Research/CPU profiles are installed in separate directories with the same helper.
An audit controller can verify them via `--installed --target-python <interpreter>`.

Regenerate locks with `scripts/resolve_security_environments.py --profile <name>
--platform <windows|linux>`. It verifies uv's version, forbids external source
builds during resolution, checks the official torch index/hash and records the
exact artifact ledger. Regeneration contacts indexes; current locks remain the
auditable resolution, not a claim that future resolutions will remain identical.

## Historical reproducibility and compatibility

`requirements/historical/pr2/` retains six original manifests byte-for-byte,
including tokenizers==0.20.0, sentencepiece==0.2.2 and the old build constraints.
`historical-dependency-hashes.json` and
`scripts/verify_historical_dependencies.py` verify these snapshots. The historical
wrapper's relative includes remain valid. PR #1's observed environment manifest
and all original datasets/results/configs remain in their original paths.

Historical environments still contain known vulnerabilities (FAIL). Preserve
them only for controlled reproduction with trusted artifacts and restricted
network/input exposure. Their preservation is not a security approval or
authorization to process new hostile data with old vulnerable libraries.

All original 111 tests run against the maintained stack. Four additional tests
cover alias transitivity, explicit torch artifact coverage, scanner skips and
scanner errors. The final suite has **115 tests**. Historical metrics, labels,
seeds, thresholds and outputs are never changed to accommodate dependencies.
No production scientific source file was refactored to force compatibility.

## PyTorch source, version and audit coverage

`torch-artifacts.json` binds each platform/profile to an official HTTPS index,
the index-response hash, exact wheel filename/URL/SHA-256 and upstream version.
CPU uses 2.15.0+cpu; Linux CUDA 13.0 uses 2.14.1+cu130 because 2.15 is absent from
that official backend. An upstream PyPI version alone does not identify a binary.

The audit helper validates installed versions and absence of undeclared packages,
the imported torch build, CPU/CUDA runtime fields and its PEP 610 URL/hash receipt.
An initial uv installation omitted the receipt's archive hash even with hash
checking; maintained installation therefore uses pip with mandatory hashes,
which retains that verifiable receipt. An incomplete receipt fails the control.

Native `pip-audit` output is retained unchanged, including skips for the local
AETHON project and +cpu/+cu build identities. Native mode inventories all skips
instead of aborting on the first unknown. A **separate strict query** covers every
locked dependency and the corresponding public torch upstream version. It fails
on findings, missing coverage or scanner errors. There are no advisory ignores.
Installed version drift, undeclared packages and incorrect receipts also fail.

The distinction is explicit: upstream advisory query PASS does **not** establish
an audit of the exact CPU/CUDA binary. Its exact catalog status remains
NOT_AUDITED. Official source/hash and CPU compatibility can independently PASS;
CUDA execution remains NOT_RUN without hardware. This is documented evidence of
coverage, not a claim of binary safety.

## Validation and residual risk

Executed checks and raw scanner evidence are collected in `validation.json` and
the `evidence/` directory after final verification. CI runs on Windows and Linux,
installs CPU/development separately, validates research CPU separately and audits
the CUDA dependency lock without pretending to execute GPU inference. Actions
retain read-only permissions, pinned SHAs, offline model mode and scoped audit
artifacts; private prompts/responses are never uploaded as evidence.

Status meanings:

- **PASS:** the named check actually ran and met its criteria.
- **FAIL:** known findings, dependency incompatibility, drift or a failed check.
- **NOT_RUN:** a runtime/experiment/installation has not been performed.
- **NOT_AUDITED:** the scanner/catalog or available evidence does not cover it.

Residual dispositions are in `RESIDUAL_RISKS.md`. A missing fix event, an unknown
binary or an unexecuted GPU run is not silently accepted as safe. There is no
blanket risk acceptance or production-security certification.

Primary technical sources: [PyTorch official distributions](https://pytorch.org/get-started/previous-versions/),
[Transformers model loading](https://huggingface.co/docs/transformers/models),
[pip-audit](https://github.com/pypa/pip-audit). Advisory-specific sources are
included per row in the consolidated matrix.
