# BENCHMARK STATUS — AETHON

**Data**: 2026-06-24  
**Objetivo**: Status de cada benchmark profile e readiness para publicação.

---

## 1. Resumo Executivo

| Modelo | Config | Status | Rows | Dataset-Limit | Publicável? |
|--------|--------|--------|------|---------------|-------------|
| Phi-3-mini-4k-instruct | `phi3_benchmark.json` | ✅ COMPLETO | 500 | 20 | ❌ |
| Llama-3.2-1B-Instruct | `llama1b_benchmark.json` | ✅ COMPLETO | 500 | 20 | ❌ |
| Llama-3.2-3B-Instruct | `llama3b_benchmark.json` | ✅ COMPLETO | 500 | 20 | ❌ |
| Qwen2.5-3B-Instruct | `qwen3b_benchmark.json` | ✅ COMPLETO | 500 | 20 | ❌ |
| Qwen2.5-7B-Instruct | `qwen7b_benchmark.json` | ⚠️ INTERROMPIDO | 2/500 | 20 | ❌ |
| Llama-2-7b-chat | `llama7b_benchmark.json` | ❌ NÃO INICIADO | 0 | — | ❌ |

**Nenhum resultado é publication-ready.** Todos os runs completados utilizaram `--dataset-limit 20`.

---

## 2. Detalhamento por Profile

### 2.1 Phi-3 Mini (phi3_benchmark)

- **Run ID**: `aethon_20260609T161554Z_c8394f0c`
- **Status**: Concluído em 2026-06-10T03:46 UTC
- **Datasets**: 5 (notinject, prompt_injection_core, jailbreakbench, red_team_attempts, cyberseceval)
- **Condições**: B0, B1, B2, B3, B4
- **Amostras por grupo**: 20
- **Total de rows**: 500
- **AUROC**: Indefinido em todos os grupos (apenas 1 classe por dataset no sample de 20)
- **ASR**: Parcialmente computado (cobertura variável)
- **Latência mediana B0**: ~108–170 s/prompt (inferência local)
- **Artefatos**: master_results.csv, diagnostics.csv, metrics_summary, tables (6 tabelas), readiness_report

### 2.2 Llama-3.2-1B-Instruct (llama1b_benchmark)

- **Run ID**: `aethon_20260610T175233Z_2e1ac7be`
- **Status**: Concluído em 2026-06-10T20:40 UTC
- **Total de rows**: 500
- **Artefatos**: Completos (idêntica estrutura ao phi3)
- **Latência**: Menor que phi3 (1B model)

### 2.3 Llama-3.2-3B-Instruct (llama3b_benchmark)

- **Run ID**: `aethon_20260610T205454Z_9306480f`
- **Status**: Concluído em 2026-06-11T03:59 UTC
- **Total de rows**: 500
- **Artefatos**: Completos

### 2.4 Qwen2.5-3B-Instruct (qwen3b_benchmark)

- **Run ID**: `aethon_20260610T103302Z_e9b68bd2`
- **Status**: Concluído em 2026-06-10T17:18 UTC
- **Total de rows**: 500
- **Artefatos**: Completos

### 2.5 Qwen2.5-7B-Instruct (qwen7b_benchmark)

- **Run ID**: `aethon_20260611T095820Z_da12c73e`
- **Status**: ⚠️ INTERROMPIDO
- **Último checkpoint**: notinject / B0 / prompt 3 de 20 (2 processados)
- **ETA no momento da interrupção**: 1596:15:42 (66.5 dias!)
- **Causa provável**: Inferência local inviável para modelo 7B na máquina utilizada
- **Artefatos**: Apenas progress.json (sem master_results, sem tables)

### 2.6 Llama-2-7b-chat (llama7b_benchmark)

- **Run ID**: Nenhum
- **Status**: ❌ NUNCA INICIADO
- **Diretório**: Não existe em `results/`
- **Artefatos**: Nenhum

---

## 3. Validation Full Matrix (per_model/)

Rodadas de validação com **23 amostras** × **10 datasets** × **5 condições** = ~1,150 rows/modelo.

| Modelo | Rows | Run ID | Tipo |
|--------|------|--------|------|
| `llama-3.2-1b-instruct` | 11,957 | `validation_full_matrix` | DRY_RUN |
| `llama-3.2-3b-instruct` | 9,121 | `validation_full_matrix` | DRY_RUN |
| `llama-2-7b-chat` | 10,482 | `validation_full_matrix` | DRY_RUN |
| `gpt-5.4-nano` | ~1,150 | `validation_full_matrix` | DRY_RUN |
| `gpt-5.4-mini` | ~1,150 | `validation_full_matrix` | DRY_RUN |
| `deepseek-v4-flash` | ~1,150 | `validation_full_matrix` | DRY_RUN |

**Nota**: Estas são rodadas dry-run (sem inferência real). Úteis para validação do pipeline, mas não contêm respostas LLM reais.

---

## 4. Métricas e Problemas Estatísticos

### AUROC

- **Indefinido em TODOS os benchmarks dedicados** com limit=20
- Razão: Com apenas 20 amostras por dataset, datasets single-class (notinject, red_team_attempts, cyberseceval) não têm ambas as classes representadas
- **Solução**: Rodar full-dataset (sem --dataset-limit). O dataset `prompt_injection_core` (6,274 rows mixed) permitirá AUROC mesmo com runs parciais.

### ASR (Attack Success Rate)

- ASR parcialmente computado nos timing probes
- Cobertura: 45-100% dependendo do dataset/condição
- ASR B0: Variável (0.06–0.33) — indica que modelos respondem a alguns ataques
- ASR B2-B4: ~0.0 (middleware bloqueia antes da inferência)
- **Publicável apenas com dataset completo e coverage > 80%**

### Latências Observadas (Local, Timing Probes)

| Modelo | Mediana B0 (s/prompt) | Estimativa Full Run |
|--------|----------------------|---------------------|
| Llama-3.2-1B | ~11–37 s | ~774 horas |
| Llama-3.2-3B | ~25–80 s | ~2,945 horas |
| Phi-3-Mini | ~91–170 s | ~2,945 horas |
| Qwen2.5-3B | ~15–50 s | ~2,945 horas |
| Qwen2.5-7B | ~1,596 h ETA (proibido) | ~7,042 horas |
| Llama-2-7B | N/A local | ~7,042 horas |

**Conclusão**: Modelos 7B são absolutamente inviáveis para execução local. Mesmo modelos 3B levariam meses.

---

## 5. Configuração dos Benchmarks

Todos os configs dedicados são corretamente estruturados:

```json
{
  "models": ["<model>"],
  "datasets": ["notinject", "prompt_injection_core", "jailbreakbench_behaviors", "red_team_attempts", "cyberseceval_prompt_injection"],
  "conditions": ["B0", "B1", "B2", "B3", "B4"],
  "seed": 42,
  "temperature": 0.2,
  "epsilon": 1.2,
  "max_tokens": 256,
  "limit": null,
  "resume": true,
  "generate_tables": true,
  "asr_judge_type": "rule",
  "ml_model_path": "src/models/aethon_tfidf_lr.pkl"
}
```

**Validação**:
- ✅ Seed fixo (42) para reprodutibilidade
- ✅ Temperature baixa (0.2) para determinismo
- ✅ Resume habilitado
- ✅ ASR rule-based (sem custo API)
- ✅ ML model path correto
- ✅ Limit: null (full dataset) — os timing probes usaram `--dataset-limit 20` via CLI override

---

## 6. Capacidades Verificadas do Pipeline

| Feature | Status | Evidência |
|---------|--------|-----------|
| B0-B4 ablations | ✅ | Todos os probes executaram 5 condições |
| ASR rule-based | ✅ | asr_comparison tables geradas |
| Metrics pipeline | ✅ | metrics_summary CSV+JSON gerados |
| Diagnostics | ✅ | diagnostics.csv com class distribution |
| Resume mode | ✅ | Config `resume: true` + progress.json |
| Partial checkpoints | ✅ | master_results.csv incremental |
| Progress tracking | ✅ | progress.json com ETA |
| Table generation | ✅ | 6 tabelas (CSV + MD + TeX) por run |
| Readiness report | ✅ | benchmark_readiness_report.md gerado |
| Per-model CSV | ✅ | CSV isolado por modelo |
| Benchmark manifest | ✅ | JSONL com metadata de cada prompt |

---

## 7. Resultado Necessário para Publicação

| Modelo | Rows Necessários | Status Atual | Gap |
|--------|-----------------|--------------|-----|
| Phi-3-Mini | 230,125 | 500 (0.2%) | 229,625 |
| Qwen2.5-3B | 230,125 | 500 (0.2%) | 229,625 |
| Qwen2.5-7B | 230,125 | 2 (0.0%) | 230,123 |
| Llama-3.2-1B | 230,125 | 500 (0.2%) | 229,625 |
| Llama-3.2-3B | 230,125 | 500 (0.2%) | 229,625 |
| Llama-2-7B | 230,125 | 0 (0%) | 230,125 |

**Total gap**: 1,379,748 prompt-condition evaluations faltantes.
