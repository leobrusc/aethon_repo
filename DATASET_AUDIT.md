# DATASET AUDIT — AETHON

**Data**: 2026-06-24  
**Local**: `datasets/`

---

## 1. Inventário de Datasets Canônicos

| # | Arquivo | Tamanho | Formato | Rows | Label | Alias no Loader |
|---|---------|---------|---------|------|-------|-----------------|
| 1 | `hf_prompt-injections_train.parquet` | 40 KB | Parquet | ~662 | 0/1 | `prompt_injections_train` |
| 2 | `hf_prompt-injections_test.parquet` | 11 KB | Parquet | ~165 | 0/1 | `prompt_injections_test` |
| 3 | `hf_red_team_attempts.jsonl` | 55 MB | JSONL (JSON-array) | 38,961 | 1 (adversarial) | `red_team_attempts` |
| 4 | `kaggle_red_team_prompts.json` | 160 KB | JSON | ~500 | 1 (adversarial) | `kaggle_redteam` |
| 5 | `advbench_harmful_behaviors.csv` | 83 KB | CSV | ~520 | 1 (adversarial) | `advbench_harmful` |
| 6 | `jailbreakbench_behaviors.jsonl` | 60 KB | JSONL | 200 | 0/1 (100+100) | `jailbreakbench_behaviors` |
| 7 | `wildjailbreak_eval.jsonl` | 1.8 MB | JSONL | ~1,800 | 1 (adversarial) | `wildjailbreak_eval` |
| 8 | `neuralchemy_prompt_injection_core.jsonl` | 2.2 MB | JSONL | 6,274 | 0/1 (3736+2538) | `prompt_injection_core` |
| 9 | `notinject.jsonl` | 67 KB | JSONL | 339 | 0 (benign-only) | `notinject` |
| 10 | `cyberseceval_prompt_injection.json` | 199 KB | JSON | 251 | 1 (adversarial) | `cyberseceval_prompt_injection` |

---

## 2. Datasets de Backup/Oficial (não incluídos no benchmark)

| Arquivo | Tamanho | Notas |
|---------|---------|-------|
| `hf_red_team_attempts.official.jsonl` | 55 MB | Cópia oficial para validação de hash |
| `red_team_attempts.official.jsonl.gz` | 15 MB | Versão comprimida original |
| `hf_red_team_attempts.local_backup_20260519160418.json` | 55 MB | Backup local pré-conversão |

Todos ignorados pelo `.gitignore` e excluídos do alias `all` no loader.

---

## 3. Integridade dos Arquivos

| Dataset | Existe | Tamanho OK | Formato Validado | LFS Status |
|---------|--------|-----------|-----------------|------------|
| `hf_prompt-injections_train.parquet` | ✅ | ✅ (40 KB) | ✅ Parquet | N/A (não .jsonl) |
| `hf_prompt-injections_test.parquet` | ✅ | ✅ (11 KB) | ✅ Parquet | N/A |
| `hf_red_team_attempts.jsonl` | ✅ | ✅ (55 MB) | ✅ JSONL (verified) | ⚠️ **BLOB REGULAR** |
| `kaggle_red_team_prompts.json` | ✅ | ✅ (160 KB) | ✅ JSON | N/A |
| `advbench_harmful_behaviors.csv` | ✅ | ✅ (83 KB) | ✅ CSV | N/A |
| `jailbreakbench_behaviors.jsonl` | ✅ | ✅ (60 KB) | ✅ JSONL | ✅ LFS tracked |
| `wildjailbreak_eval.jsonl` | ✅ | ✅ (1.8 MB) | ✅ JSONL | ✅ LFS tracked |
| `neuralchemy_prompt_injection_core.jsonl` | ✅ | ✅ (2.2 MB) | ✅ JSONL | ✅ LFS tracked |
| `notinject.jsonl` | ✅ | ✅ (67 KB) | ✅ JSONL | ✅ LFS tracked |
| `cyberseceval_prompt_injection.json` | ✅ | ✅ (199 KB) | ✅ JSON | N/A |

---

## 4. Matriz Dataset × Benchmark Profile

### Benchmark dedicado (5 datasets selecionados):

| Dataset | Rows | Benchmark Configs | Classe | AUROC Computável? |
|---------|------|-------------------|--------|-------------------|
| `notinject` | 339 | Todos os 6 dedicados | Benign-only (0) | ❌ Sozinho não |
| `prompt_injection_core` | 6,274 | Todos os 6 dedicados | Mixed (0/1) | ✅ Sim |
| `jailbreakbench_behaviors` | 200 | Todos os 6 dedicados | Mixed (0/1) | ✅ Sim |
| `red_team_attempts` | 38,961 | Todos os 6 dedicados | Adversarial-only (1) | ❌ Sozinho não |
| `cyberseceval_prompt_injection` | 251 | Todos os 6 dedicados | Adversarial-only (1) | ❌ Sozinho não |

**Total por profile**: 46,025 rows × 5 condições = **230,125 prompt-condition evaluations**

### Full matrix (benchmark_full.json) — 10 datasets:

Adiciona: `prompt_injections_train`, `prompt_injections_test`, `kaggle_redteam`, `advbench_harmful`, `wildjailbreak_eval`

---

## 5. Distribuição de Classes

| Dataset | Positivos (adversarial) | Negativos (benign) | ASR Elegível? |
|---------|------------------------|-------------------|---------------|
| `notinject` | 0 | 339 | ❌ |
| `prompt_injection_core` | 3,736 | 2,538 | ❌ (não é jailbreak/red-team) |
| `jailbreakbench_behaviors` | 100 | 100 | ✅ |
| `red_team_attempts` | 38,961 | 0 | ✅ |
| `cyberseceval_prompt_injection` | 251 | 0 | ✅ |

**AUROC Publication-Ready**: Apenas `prompt_injection_core` e `jailbreakbench_behaviors` permitem AUROC independente.  
**ASR Publication-Ready**: `jailbreakbench_behaviors`, `red_team_attempts`, `cyberseceval_prompt_injection`.

---

## 6. Problema Crítico: hf_red_team_attempts.jsonl

### Diagnóstico

- **Tamanho**: 55,487,878 bytes (55 MB)
- **Conteúdo**: JSON-array JSONL (verificado — dados reais, não pointer)
- **Git LFS filter configurado**: Sim (`.gitattributes: *.jsonl filter=lfs`)
- **Listado em `git lfs ls-files`**: ❌ **NÃO**
- **Commit original**: `f440b36` ("Liberando mais arquivos para consulta do Professor Jorge")
- **LFS adicionado em**: `f506432` (commit posterior)

### Causa Raiz

O arquivo foi commitado como blob regular ANTES da configuração do LFS. O Git LFS não retroativamente converte blobs existentes. Resultado: 55 MB de dados brutos permanecem no histórico do repositório indefinidamente.

### Impacto

- Clone do repositório sempre baixa 55 MB extras (incluído no packfile)
- GitHub pode recusar pushes futuros se o repo exceder limites de tamanho
- Ineficiente para colaboradores

### Resolução

Ver `GITHUB_CLEANUP_PLAN.md` para procedimento de migração.

---

## 7. Recomendações

1. **Prioridade ALTA**: Executar `git lfs migrate` para mover `hf_red_team_attempts.jsonl` para LFS no histórico
2. **Documentação**: O `datasets/SOURCES.md` deve ser atualizado com hashes SHA-256 dos datasets
3. **Validação CI**: Adicionar teste automatizado que verifica existência e tamanho mínimo dos 10 datasets canônicos
