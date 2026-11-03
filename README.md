# Aethon

**Adaptive Ethical Threat Observatory for Networks**

Repository modernization: see the [audit and validation report](docs/modernization/REPORT.md),
[architecture and CLI migration](docs/ARCHITECTURE.md),
[contribution guide](CONTRIBUTING.md) and [security policy](SECURITY.md).
The June inventory/cleanup plans are archived; their history-rewrite instructions
are superseded.

For maintained CPU development, use Python 3.12.13 and the hashed environment
instructions in [the security remediation report](docs/security/REPORT.md).
Historical Python 3.10/tokenizers pins remain in `requirements/historical/pr2/`;
they are not the default for processing new untrusted inputs.

After installing the appropriate lock and editable package, run from the
repository root:

```bash
git lfs pull
python -m aethon benchmark --help
python -m pytest -q
python scripts/repository_inventory.py verify
```

Existing `python src/...` commands remain supported. The maintained profiles split
CPU, development, research CPU and Linux CUDA, with exact hashes and official
PyTorch wheel URLs. `requirements.txt` contains CPU/research declarations;
reproducible installations use the locks instead. See the
[security report](docs/security/REPORT.md) for current results and the
[modernization dependency audit](docs/modernization/DEPENDENCIES.md) for historical
context. Package installation does not download model weights.

Aethon is an experimental cybersecurity and AI engineering framework for studying how large language models (LLMs) respond to adversarial prompts, especially prompt injection, jailbreak, and red-team inputs. The repository provides a reproducible pipeline for loading security-oriented datasets, applying detection and mitigation logic, executing selected model backends, and recording results for later analysis.

---

## Overview

Modern LLM applications receive input from users, retrieved documents, agents, and external tools. Some inputs intentionally attempt to override instructions, obtain prohibited behavior, or manipulate model output. Aethon treats these inputs as a security testing problem.

The project organizes experiments around four concerns:

| Concern | Purpose |
|---|---|
| Dataset ingestion | Normalize heterogeneous adversarial and benign prompt sources into one evaluation schema. |
| Detection | Identify suspicious input using heuristic rules and an optional supervised classifier. |
| Mitigation and audit | Decide whether an input should be allowed or mitigated, while recording audit metadata. |
| Model evaluation | Run controlled prompt-response experiments against local or API-hosted LLMs. |

Aethon is intended as a research and engineering workbench, not as a production security gateway in its current form.

## Motivation

Prompt injection and jailbreak evaluation is difficult because attack patterns vary significantly across datasets, model families, languages, and deployment settings. A useful security benchmark must therefore support:

- multiple datasets rather than a single narrow attack collection;
- reproducible model and sampling configurations;
- auditable decisions and stored experimental metadata;
- evaluation of both attack detection and false positives on benign inputs;
- extensible backends for local open-weight models and hosted APIs.

For students, the repository demonstrates the transition from a security hypothesis to an executable evaluation pipeline. For researchers, it provides a compact basis for comparative experiments. For practitioners, it highlights practical issues such as sensitive dataset handling, credential management, response logging, and model-dependent behavior.

## Core Features

- Unified dataset loader that normalizes prompt collections to `prompt_id`, `prompt_text`, `label`, and `source`.
- Aggregated `all` dataset alias for experiments across the canonical local benchmark collection.
- Rule-based adversarial prompt detector in `aethon_heuristic.py`.
- TF-IDF and logistic-regression training utilities for supervised detection experiments.
- A combined mitigation and audit component with configurable noisy audit counts.
- Model registry supporting local Hugging Face drivers and remote API drivers.
- JSON experiment outputs and an append-only experiment manifest.
- Statistical analysis helpers, including bootstrap confidence intervals and McNemar comparison support.

## Architecture

Aethon is structured as a pipeline. Each experiment begins with raw prompt data, converts it to a stable internal representation, applies security logic, optionally sends the input to a target model, and records the outcome.

### Main Modules

| Module | Responsibility |
|---|---|
| `src/dataset_loader.py` | Maps each supported dataset format to a common prompt schema and combines datasets through the `all` alias. |
| `src/aethon_heuristic.py` | Applies lightweight regular-expression indicators for suspicious instruction patterns. |
| `src/aethon_ml_pipeline.py` | Trains and loads a text classifier based on TF-IDF features and logistic regression. |
| `src/aethon_full_pipeline.py` | Combines detection decisions with mitigation actions and audit logging. |
| `src/model_registry.py` | Resolves command-line model names into concrete inference drivers. |
| `src/models/` | Implements local Hugging Face and API-based model adapters. |
| `src/run_experiment.py` | Orchestrates the evaluation loop and writes results and run metadata. |
| `src/analysis_utils.py` | Supplies statistical utilities for interpreting experiment outcomes. |
| `src/test_model_loading.py` | Validates driver initialization and optional live inference availability. |

### Execution Flow

```text
Dataset files
    |
    v
dataset_loader.py  -> normalized prompts: prompt_id, prompt_text, label, source
    |
    v
aethon_heuristic.py + optional ML classifier
    |
    v
aethon_full_pipeline.py  -> allow / mitigate decision + audit metadata
    |
    v
model_registry.py -> selected model driver -> LLM inference (unless --dry-run)
    |
    v
results/<model>/<dataset>/*.json + experiment_manifest.json
```

### Component Interactions

1. `run_experiment.py` loads a named dataset, such as `prompt_injection_core`, or the combined `all` set.
2. The loader handles Parquet, CSV, JSON, and JSONL inputs and emits a standard dataframe.
3. For every prompt, the heuristic detector generates a preliminary security flag.
4. `AethonFull` creates an action decision and audit entry. Its ML component is available when a trained model path is supplied.
5. Unless the run uses `--dry-run`, a registered driver sends the prompt to the requested LLM.
6. The runner saves the prompt excerpt, label, detection result, mitigation decision, response, and run metadata.

### Data Processing Pipeline

The local dataset collection includes prompt injection benchmarks, red-team conversations, jailbreak behavior sets, adversarial harmful prompts, and benign hard negatives. Supported canonical aliases are documented in [`datasets/SOURCES.md`](datasets/SOURCES.md).

The combined loader currently makes the following engineering choices:

- source-specific fields such as `text`, `prompt`, `transcript`, and `Goal` are mapped into `prompt_text`;
- source labels are normalized to binary values (`0` benign, `1` adversarial);
- datasets without a benign class and designed as attack collections are labeled adversarial by default;
- `notinject` is included as benign hard-negative data to measure over-blocking risk;
- backup downloads and compressed archives are not included in the `all` alias.

Because these datasets contain adversarial instructions, they should be handled as security test artifacts and not copied into logs, issue reports, or public examples without review.

## Repository Structure

```text
.
|-- datasets/
|   |-- SOURCES.md
|   |-- *.parquet, *.json, *.jsonl, *.csv
|-- results/
|   |-- <model>/<dataset>/*.json
|   `-- model_load_check.json
|-- src/
|   |-- models/
|   |   |-- deepseek_driver.py
|   |   |-- hf_causal_driver.py
|   |   |-- openai_driver.py
|   |   `-- ...
|   |-- aethon_full_pipeline.py
|   |-- aethon_heuristic.py
|   |-- aethon_ml_pipeline.py
|   |-- analysis_utils.py
|   |-- dataset_loader.py
|   |-- model_registry.py
|   |-- run_experiment.py
|   `-- test_model_loading.py
|-- EXPERIMENT_FLOW.md
|-- experiment_manifest.json
|-- requirements.txt
`-- README.md
```

## Installation

### Clone the Repository

```bash
git clone https://github.com/leobrusc/aethon_repo.git
cd aethon_repo
```

### Windows PowerShell

```powershell
# Run with a Python 3.12.13 controller; see docs/security/REPORT.md.
python -m pip install --isolated --require-hashes --only-binary=:all: -r requirements/environments/bootstrap.lock
python scripts/install_security_environment.py requirements/environments/dev-windows-py312.lock .venv-dev
.\.venv-dev\Scripts\Activate.ps1
```

### Linux

```bash
# Run with a Python 3.12.13 controller; macOS has no validated lock yet.
python -m pip install --isolated --require-hashes --only-binary=:all: -r requirements/environments/bootstrap.lock
python scripts/install_security_environment.py requirements/environments/dev-linux-py312.lock .venv-dev
source .venv-dev/bin/activate
```

Some Hugging Face models require model-license acceptance and an authenticated token. Hosted APIs require provider credentials. Credentials must be supplied through environment variables or a local `.env` file and must never be committed.

```bash
# OpenAI
export OPENAI_API_KEY="your-key"

# DeepSeek
export DEEPSEEK_API_KEY="your-key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"  # or an OpenAI-compatible USP endpoint

# Hugging Face gated models
export HF_TOKEN="your-token"
```

PowerShell equivalents:

```powershell
$env:OPENAI_API_KEY="your-key"
$env:DEEPSEEK_API_KEY="your-key"
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
$env:HF_TOKEN="your-token"
```

## Usage

### Inspect Available Datasets

`dataset_loader.py` exposes individual aliases and a combined benchmark alias:

```python
from src.dataset_loader import load_dataset

combined = load_dataset("all")
print(combined.shape)
print(combined["source"].value_counts())
```

### Run a Detection-Only Evaluation

A dry run executes dataset loading and Aethon decision logic without making an LLM inference request:

```powershell
.\venv\Scripts\python.exe src\run_experiment.py --model gpt-4o-mini --dataset all --dry-run --limit 20
```

```bash
python src/run_experiment.py --model gpt-4o-mini --dataset all --dry-run --limit 20
```

### Run an LLM Evaluation

After configuring the appropriate provider credentials:

```bash
python src/run_experiment.py \
  --model gpt-5.4-nano \
  --dataset prompt_injection_core \
  --temp 0.2 \
  --seed 42 \
  --condition B0 \
  --limit 25
```

Important command-line options:

| Option | Description |
|---|---|
| `--model` | Registered model key, for example `gpt-4o-mini`, `gpt-5.4-nano`, or `llama-3.2-1b-instruct`. |
| `--dataset` | Canonical dataset alias, including `all`. |
| `--temp` | Inference sampling temperature. |
| `--seed` | Experimental metadata seed. |
| `--condition` | Condition label recorded for the run. |
| `--aethon-epsilon` | Privacy-noise parameter used by the audit component. |
| `--limit` | Restricts the number of examples for smoke tests. |
| `--dry-run` | Skips model inference while exercising detection and output generation. |

### Supported Model Backends

| Registry Key | Provider / Backend | Credential Requirement |
|---|---|---|
| `gpt-4o-mini` | OpenAI API | `OPENAI_API_KEY` |
| `gpt-5.4-nano` | OpenAI API | `OPENAI_API_KEY` |
| `gpt-5.4-mini` | OpenAI API | `OPENAI_API_KEY` |
| `deepseek-v4-flash` | DeepSeek OpenAI-compatible API | `DEEPSEEK_API_KEY` |
| `phi-2` | Hugging Face local model | Model download/cache |
| `phi-3-mini-4k-instruct` | Hugging Face open-weight local model (`microsoft/Phi-3-mini-4k-instruct`) | Model download/cache |
| `qwen2.5-3b-instruct` | Hugging Face open-weight local model (`Qwen/Qwen2.5-3B-Instruct`) | Model download/cache |
| `qwen2.5-7b-instruct` | Hugging Face open-weight local model (`Qwen/Qwen2.5-7B-Instruct`) | Model download/cache |
| `tinyllama-1.1b-chat` | Hugging Face open-weight local model (`TinyLlama/TinyLlama-1.1B-Chat-v1.0`) | Model download/cache |
| `mistral-7b` | Hugging Face local model | Model download/cache |
| `llama3-8b` | Hugging Face gated model | HF access/token |
| `llama-2-7b-chat` | Hugging Face gated model | HF access/token |
| `llama-3.2-1b-instruct` | Hugging Face gated model | HF access/token |
| `llama-3.2-3b-instruct` | Hugging Face gated model | HF access/token |

The benchmark registry also accepts the exact Hugging Face IDs for the open-weight fallback models above. Output files use the canonical registry keys so per-model CSV names remain stable.

### Outputs

Each execution creates:

```text
results/<model>/<dataset>/<run_id>.json
experiment_manifest.json
```

Result records include the normalized prompt identifier, a prompt excerpt, the source label, heuristic decision, mitigation decision, model response, and run metadata. Since responses and excerpts may contain sensitive adversarial content, experimental artifacts require controlled handling.

### Reproducible Benchmark Pipeline

The publication-oriented benchmark runner is `src/run_benchmark.py`. It preserves the original lightweight middleware design while adding full-dataset execution, model batching, ablation support, per-prompt timing, resumable CSV persistence, formal ASR evaluation, metric summaries, and paper-ready tables.

Supported ablations:

| Condition | Meaning |
|---|---|
| `B0` | No defense. |
| `B1` | Regex heuristic only. |
| `B2` | TF-IDF + Logistic Regression only. |
| `B3` | Deterministic OR cascade: heuristic or ML flag triggers mitigation. |
| `B4` | Full cascade plus differentially private noisy audit counters. |

Train the lightweight classifier required for `B2`-`B4`:

```bash
python src/train_detector.py \
  --datasets prompt_injections_train \
  --save-name aethon_tfidf_lr.pkl
```

Run a validation benchmark without external LLM calls:

```bash
python src/run_benchmark.py \
  --models gpt-5.4-nano \
  --datasets notinject cyberseceval_prompt_injection \
  --conditions B0 B1 B2 B3 B4 \
  --ml-model-path src/models/aethon_tfidf_lr.pkl \
  --dry-run \
  --limit 20
```

Run the configured multi-model, full-dataset benchmark:

```bash
python src/run_benchmark.py --config configs/benchmark_full.json
```

`configs/benchmark_full.json` prioritizes the validated benchmark models in this order: Meta Llama 2/3.2, Qwen 2.5, then Phi-3. API-backed models are intentionally omitted from the default full config and are skipped by the runner when their required credential variables are unavailable.

Run only the validated Meta models:

```bash
python src/run_benchmark.py \
  --config configs/benchmark_full.json \
  --llama-only
```

Run only the prioritized non-API benchmark models with ASR evaluation and all ablations:

```bash
python src/run_benchmark.py \
  --open-models-only \
  --all-datasets \
  --conditions B0 B1 B2 B3 B4 \
  --ml-model-path src/models/aethon_tfidf_lr.pkl \
  --asr-judge-type rule
```

Run a fast local validation pass:

```bash
python src/run_benchmark.py \
  --config configs/benchmark_full.json \
  --fast-validation \
  --dry-run
```

Limit each dataset and select a subset of ablations:

```bash
python src/run_benchmark.py \
  --config configs/benchmark_full.json \
  --dataset-limit 20 \
  --condition-filter B0 B3 \
  --dry-run
```

The same command can use exact Hugging Face IDs when preferred:

```bash
python src/run_benchmark.py \
  --models meta-llama/Llama-3.2-1B-Instruct Qwen/Qwen2.5-3B-Instruct microsoft/Phi-3-mini-4k-instruct \
  --datasets jailbreakbench_behaviors cyberseceval_prompt_injection red_team_attempts \
  --conditions B0 B1 B2 B3 B4 \
  --ml-model-path src/models/aethon_tfidf_lr.pkl \
  --asr-judge-type rule
```

Run API-backed models only after credentials are configured:

```bash
python src/run_benchmark.py \
  --models gpt-5.4-nano gpt-5.4-mini deepseek-v4-flash \
  --datasets cyberseceval_prompt_injection \
  --conditions B0 B1 B2 B3 B4 \
  --ml-model-path src/models/aethon_tfidf_lr.pkl \
  --asr-judge-type rule
```

Resume a previously interrupted benchmark:

```bash
python src/run_benchmark.py \
  --config configs/benchmark_full.json \
  --run-id <existing-run-id> \
  --resume
```

Evaluate downstream responses with the default rule-based ASR judge:

```bash
python src/run_benchmark.py \
  --config configs/benchmark_full.json \
  --asr-judge-type rule
```

Optionally select an LLM-as-a-judge after configuring its provider credentials:

```bash
python src/run_benchmark.py \
  --config configs/benchmark_full.json \
  --asr-judge-type llm \
  --asr-judge-model gpt-5.4-mini
```

Benchmark output layout:

```text
results/
|-- aggregated/
|   |-- master_results.csv
|   |-- benchmark_manifest.jsonl
|   |-- failures.csv
|   |-- metrics_summary_<run_id>.csv
|   `-- metrics_summary_<run_id>.json
|-- per_model/
|   `-- <model_name>.csv
`-- tables/<run_id>/
    |-- auroc_per_model.{csv,md,tex}
    |-- fpr_comparison.{csv,md,tex}
    |-- asr_comparison.{csv,md,tex}
    |-- latency_comparison.{csv,md,tex}
    |-- ablation_comparison.{csv,md,tex}
    `-- dataset_comparison.{csv,md,tex}
```

See [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) for the experimental protocol, metadata requirements, and controlled handling guidance for raw prompt/response artifacts. A minimal benign dry-run output is available in [`examples/sample_results/`](examples/sample_results/).

For a local or institutional OpenAI-compatible DeepSeek deployment, set `DEEPSEEK_BASE_URL` to the server endpoint before launching the benchmark.

ASR is computed only for adversarial examples from JailbreakBench, CyberSecEval Prompt Injection, and Anthropic red-team attempts. Prompt-level outputs contain `asr_result`, `attack_success`, `judge_reason`, and `asr_judge`; summaries report `asr`, `blocked_asr`, `residual_asr`, `defense_success_rate`, and `asr_evaluation_coverage`. ASR should be reported together with coverage because indeterminate rule-based judgments and dry-run responses are deliberately excluded from rate denominators.

Before a live benchmark starts executing dataset rows, each configured model is initialized once. Models with missing credentials, unavailable Hugging Face weights, gated access failures, or load errors are skipped gracefully and recorded in `results/aggregated/failures.csv`; available models continue through the unchanged CSV, metrics, ASR, table, and manifest pipeline.

During execution the runner prints the active model list, current model, dataset, condition, prompt index, and ETA:

```text
[MODEL] llama-3.2-1b-instruct
[DATASET] notinject
[CONDITION] B0
[PROMPT] 4/20
[ETA] 00:15:42
```

Progress is persisted to `results/aggregated/progress.json` at least every 30 seconds and at condition boundaries. Partial CSV checkpoints are appended every 50 prompts, so interrupted runs can resume from `master_results.csv` using `--resume`.

## Testing

Testing in an LLM security project serves two roles: verifying software correctness and validating experimental trustworthiness. A pipeline that silently skips a dataset, misreads a label, or treats a failed model load as successful can produce misleading security conclusions even if the code appears to run.

### Tests and Validation Workflows Currently Implemented

The repository includes executable validation scripts and a `pytest` suite covering the dataset and benchmark contracts.

| Validation Workflow | File / Command | What It Validates |
|---|---|---|
| Driver availability check | `python src/test_model_loading.py --model <name>` | Confirms a model key is registered and distinguishes skipped API inference, model-load failure, API error, and successful output. |
| Live API smoke test | `python src/test_model_loading.py --model gpt-5.4-nano --allow-api` | Checks credential configuration, provider connectivity, request formatting, and response parsing. This consumes API usage. |
| Dataset/pipeline smoke test | `python src/run_experiment.py --model gpt-4o-mini --dataset all --dry-run --limit 5` | Validates dataset parsing, normalization, heuristic decision execution, result persistence, and manifest logging without paying for inference. |
| Small end-to-end experiment | `python src/run_experiment.py --model <name> --dataset <dataset> --limit 5` | Tests the complete path from adversarial input through detection, LLM response, and recorded result. |
| Benchmark tests | `python -m pytest -q` | Verifies normalized dataset labels, ablation semantics, ASR judges and rates, CSV/table exports, and resumable runs. |

### What the Existing Validation Checks Mean

**Dataset validation** is central to the project because each source uses a different schema and storage format. The loader must correctly:

- parse CSV, Parquet, JSON, and JSONL forms;
- recognize the Anthropic red-team file's JSON-array representation;
- map fields such as `prompt`, `text`, `transcript`, or `Goal` to one prompt column;
- preserve benign examples so false-positive behavior can be measured;
- avoid accidentally including backup copies in aggregate runs.

**Model-driver validation** ensures that the experiment runner does not confuse availability with success. A model is only usable for a real evaluation if it returns an actual inference response; a missing API credential, inaccessible model weight, or gated Hugging Face model is a failed or skipped test, not a successful run.

**Dry-run validation** is the preferred first step for security experiments. It exercises the ingestion, decision, and persistence pipeline without transmitting potentially malicious prompt data to a third-party API and without consuming inference budget.

### Recommended Test Pyramid for Continued Development

The validation scripts are useful smoke tests. The current `tests/` suite establishes a foundation for sustained open-source development and CI/CD.

Implemented test layout:

```text
tests/
|-- test_dataset_loader.py   # normalization and label assumptions for added datasets
|-- test_middleware.py       # B0-B4 decision semantics and noisy audit behavior
|-- test_asr.py              # eligibility, judging outcomes, and ASR metric export
`-- test_benchmark_runner.py # CSV/table generation and resumable execution
```

The standard execution command is:

```bash
python -m pytest -q
```

Useful CI-quality extensions include:

```bash
python -m pytest --cov=src --cov-report=term-missing
python -m ruff check src tests
python -m mypy src
```

`pytest`, `pytest-cov` and Ruff are installed by the hashed development profile;
CI executes regression, integrity and security checks. Static typing remains
optional and is not reported as an executed gate.

### Why Testing Matters in Cybersecurity and AI Engineering

In conventional software, an incorrect parser may cause a feature failure. In security evaluation, the same parser error may invalidate an entire benchmark conclusion. Examples include labeling an adversarial prompt as benign, omitting a large dataset from evaluation, logging a credential by mistake, or accepting an API failure as an LLM refusal.

For this reason, security-oriented testing should combine:

1. **Correctness tests** for parsing, decisions, and stored metadata.
2. **Robustness tests** for malformed inputs, missing credentials, unavailable models, and unexpected response formats.
3. **Regression tests** for previously observed attack patterns and detection failures.
4. **Reproducibility checks** for experiment parameters, dataset versions, and output manifests.
5. **Safety reviews** for whether logged prompts and responses expose harmful or confidential content.

This workflow teaches an important engineering principle: in AI cybersecurity, the experiment harness itself is part of the security boundary.

## Security and Reliability

Aethon evaluates hostile or policy-sensitive text. Development and experimentation should therefore follow conservative operational practices:

- store API keys only in environment variables or untracked `.env` files;
- review datasets and results before publishing or sharing them;
- avoid printing complete attack prompts in logs, documentation, or bug reports;
- start with `--dry-run` and limited samples before sending prompts to hosted APIs;
- distinguish missing-model and API failures from actual safe model refusals;
- record dataset source, model identifier, condition, temperature, and seed for reproducibility;
- use benign hard-negative examples to evaluate over-blocking as well as attack detection.

The current heuristic implementation is intentionally lightweight and should not be treated as a standalone production defense. A reliable deployment would require stronger classifiers, adversarial validation, policy-aware output checks, telemetry controls, and rigorous testing.

## Technologies Used

| Area | Technologies |
|---|---|
| Core language | Python |
| Data processing | pandas, NumPy, Hugging Face `datasets` |
| Machine learning | scikit-learn, sentence-transformers, joblib |
| Local LLM execution | PyTorch, Transformers, Accelerate, bitsandbytes |
| Hosted model APIs | OpenAI Python SDK, OpenAI-compatible DeepSeek API |
| Statistical analysis | SciPy, statsmodels |
| Visualization | Matplotlib, Seaborn |
| Configuration and credentials | python-dotenv, PyYAML |
| Future testing/automation target | pytest, coverage, linting, CI workflows |

## Development Workflow

A maintainable contribution workflow is:

1. Create a feature branch from `main`.
2. Keep commits focused on one behavior or documentation improvement.
3. Run relevant smoke tests locally, starting with dry-run validation for pipeline changes.
4. Add or update tests when behavior changes.
5. Open a pull request describing the threat-model impact, affected datasets/models, and validation evidence.
6. Review generated experiment artifacts carefully before including them in version control.

Suggested branch naming:

```text
feature/add-model-driver
fix/dataset-label-normalization
docs/testing-overview
```

Suggested commit style:

```text
Add CyberSecEval prompt injection dataset support
Fix OpenAI response parsing in model driver
Document dry-run security validation workflow
```

Future CI/CD integration should run formatting/linting, unit tests, mocked integration tests, and restricted smoke tests that do not require secrets. Live provider evaluations should remain explicitly triggered jobs with protected credentials.

## Future Improvements

- Introduce a complete `pytest` suite with coverage reporting and mocked API-driver tests.
- Add CI workflows for static checks, unit tests, and dataset-loader regression validation.
- Implement the documented experimental defense conditions beyond the current baseline path.
- Train and evaluate the ML detector against the expanded multi-source benchmark.
- Measure precision, recall, false-positive rate, refusal behavior, and attack success rate per dataset and model.
- Sanitize stored prompt excerpts and response artifacts by default.
- Add structured configuration files for reproducible experiment matrices.
- Improve device selection, cache configuration, and quantized local-model execution.
- Add result aggregation tables and statistically grounded benchmark reports.

## Authors

**Leonardo Bruscagini**

Research and engineering lead for the Aethon framework.

Contributions, issue reports, and reproducibility improvements are welcome through the repository's standard pull request workflow.

## License

No project-level license file is currently included in this repository.

Before redistributing code or datasets, add an explicit project license and verify the license terms of each upstream dataset and model provider.
