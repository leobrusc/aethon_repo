# Visão Geral do Fluxo (End-to-End)

## 1. Preparação

- Datasets já preparados em:

/home/leonardo/Documentos/aethon_repo/datasets/prepared/{train,val,test}.csv

- Loader unificado (`src/dataset_loader.py`) normaliza colunas:
- `prompt_id`
- `prompt_text`
- `label`
- Script `src/prepare_datasets.py` gera `masked_preview.csv` para revisão (apenas hashes/excertos).

---

## 2. Orquestrador

- `src/run_experiment.py` executa por prompt:
- Heurística → (opcional) **AETHON-ML** → Mitigação (**AETHON-Full**) → Chamada ao modelo (local HF ou OpenAI API) → Salvar resposta e metadados.
- Suporta `--dry-run` (apenas heurística).
- Grava **manifest**.

---

## 3. Condições Experimentais

Para cada combinação:

- **Modelos**: Phi-2, Mistral-7B, LLaMA-3-8B, GPT-4o-mini  
- **Condições**:  
- B0 (none)  
- B1 (regex)  
- B2 (context filter)  
- B3 (post-validation)  
- AETHON-Heuristic  
- AETHON-ML  
- AETHON-Full  
- **Temperaturas**: 0.2 e 0.7  
- **Seeds**: 42, 2024, 7  
- **Epsilons AETHON-Full**: {0.5, 1.2, 2.5}

---

## 4. Saída

- Arquivos JSON por run:

results/{model}{dataset}{condition}_seed{S}_temp{T}.json

- Manifesto:
- `experiment_manifest.json` (append por run)  
- Contém custo estimado, tokens, runtime, node_id.
- Exportações:
- CSV/LaTeX em `results/tables/` para inclusão no paper.

