# INVENTORY REPORT — AETHON

**Data**: 2026-06-24  
**Branch**: `main` (clean, up-to-date with `origin/main`)  
**Commits**: 7 total  
**Remote**: `https://github.com/leobrusc/aethon_repo.git`

---

## 1. Estado do Repositório

```
git status: nothing to commit, working tree clean
git diff: (vazio)
git lfs status: nenhum objeto pendente para push
```

**Commits (cronológico reverso)**:

| Hash | Mensagem |
|------|----------|
| `54be61f` | feat(benchmark): add reproducible profiles and observability |
| `3ab0fb4` | Refactor README into professional English documentation |
| `ecff7c7` | Add adversarial prompt datasets |
| `f506432` | Configuração Git LFS para arquivos grandes |
| `f440b36` | Liberando mais arquivos para consulta do Professor Jorge |
| `57af99c` | first commit |
| `3be7fa7` | Initial commit: AETHON repo structure (drivers, SLURM, notebooks) |

---

## 2. Estrutura de Diretórios

```
aethon_repo/
├── configs/               (7 benchmark configs)
├── datasets/              (10 datasets canônicos + 3 backups/oficiais)
├── docs/                  (REPRODUCIBILITY.md)
├── examples/sample_results/
├── results/               (ignorado pelo .gitignore, artefatos locais)
├── src/
│   ├── benchmark/         (runner, middleware, metrics, asr, config, tables, results)
│   ├── loaders/           (notinject, jailbreakbench, cyberseceval)
│   ├── models/            (drivers: hf_causal, openai, deepseek, phi2, mistral, llama3_8b)
│   ├── run_benchmark.py
│   ├── run_experiment.py
│   ├── dataset_loader.py
│   ├── model_registry.py
│   ├── aethon_heuristic.py
│   ├── aethon_ml_pipeline.py
│   ├── aethon_full_pipeline.py
│   ├── analysis_utils.py
│   ├── train_detector.py
│   └── test_model_loading.py
├── tests/                 (4 test files: dataset_loader, middleware, asr, benchmark_runner)
├── .gitattributes         (*.jsonl → LFS)
├── .gitignore             (comprehensive)
├── README.md              (26 KB, documentação completa)
├── EXPERIMENT_FLOW.md
├── experiment_plan.md
├── expected_runtime_estimates.md
├── requirements.txt
└── requirements-dev.txt
```

---

## 3. Módulos Principais

| Módulo | Função | Status |
|--------|--------|--------|
| `dataset_loader.py` | Normaliza 10+ datasets para schema comum | ✅ Funcional |
| `aethon_heuristic.py` | Detector regex-based (B1) | ✅ Funcional |
| `aethon_ml_pipeline.py` | TF-IDF + LR classifier (B2) | ✅ Funcional |
| `aethon_full_pipeline.py` | Cascade B3/B4 + audit DP | ✅ Funcional |
| `model_registry.py` | Registro de drivers de modelos | ✅ 14 modelos registrados |
| `run_benchmark.py` | Orquestrador de benchmarks | ✅ Funcional |
| `src/benchmark/runner.py` | Engine principal do benchmark | ✅ Funcional |
| `src/benchmark/asr.py` | Attack Success Rate evaluation | ✅ Rule-based + LLM |
| `src/benchmark/metrics.py` | AUROC, FPR, F1, latency | ✅ Funcional |

---

## 4. Modelos Registrados

### Open-weight (Hugging Face)

| Registry Key | HF ID | Parâmetros | Driver |
|---|---|---|---|
| `phi-3-mini-4k-instruct` | `microsoft/Phi-3-mini-4k-instruct` | 3.8B | `hf_causal_driver` |
| `qwen2.5-3b-instruct` | `Qwen/Qwen2.5-3B-Instruct` | 3B | `hf_causal_driver` |
| `qwen2.5-7b-instruct` | `Qwen/Qwen2.5-7B-Instruct` | 7B | `hf_causal_driver` |
| `llama-3.2-1b-instruct` | `meta-llama/Llama-3.2-1B-Instruct` | 1B | `hf_causal_driver` |
| `llama-3.2-3b-instruct` | `meta-llama/Llama-3.2-3B-Instruct` | 3B | `hf_causal_driver` |
| `llama-2-7b-chat` | `meta-llama/Llama-2-7b-chat-hf` | 7B | `hf_causal_driver` |

### API-backed

| Registry Key | Provider | Credential |
|---|---|---|
| `gpt-5.4-nano` | OpenAI | `OPENAI_API_KEY` |
| `gpt-5.4-mini` | OpenAI | `OPENAI_API_KEY` |
| `deepseek-v4-flash` | DeepSeek | `DEEPSEEK_API_KEY` |

---

## 5. Testes

| Suite | Arquivo | Escopo |
|-------|---------|--------|
| Dataset loader | `tests/test_dataset_loader.py` | Normalização, labels |
| Middleware | `tests/test_middleware.py` | B0-B4 decision semantics |
| ASR | `tests/test_asr.py` | Eligibility, judging, metrics |
| Benchmark runner | `tests/test_benchmark_runner.py` | CSV/tables, resume |

Framework: `pytest` (instalado no venv local).

---

## 6. Artefatos de Segurança

- `.env` e credenciais: corretamente ignorados pelo `.gitignore`
- Datasets adversariais: tratados como artefatos de teste de segurança
- Prompts sensíveis: não expostos em logs públicos
- ML model pkl: ignorado pelo `.gitignore` (apenas local)

---

## 7. Problemas Identificados

| # | Severidade | Descrição |
|---|---|---|
| 1 | **ALTA** | `hf_red_team_attempts.jsonl` (55MB) armazenado como blob regular no histórico git |
| 2 | **ALTA** | Nenhum benchmark publication-ready existe (todos usaram `--dataset-limit 20`) |
| 3 | **MÉDIA** | `qwen7b_benchmark` interrompido com ETA de 1596h (inviável local) |
| 4 | **MÉDIA** | `llama7b_benchmark` nunca iniciado |
| 5 | **BAIXA** | Arquivos residuais na raiz: `pd`, `json`, `package-lock.json`, `test_llamas.py` (ignorados pelo .gitignore) |
| 6 | **BAIXA** | `__pycache__/` na raiz do repo (ignorado) |
