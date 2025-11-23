# AETHON — Adaptive Ethical Threat Observatory for Networks  
**Leonardo Bruscagini — 2025**

Repositório oficial dos experimentos, pipelines e scripts utilizados no desenvolvimento do framework **AETHON**, submetido ao *5th IEEE International Conference on AI in Cybersecurity (ICAIC 2025)*.

AETHON é um framework modular para **detecção, mitigação e auditoria adaptativa de ataques a LLMs**, com três versões complementares:

- **AETHON-Heuristic** — Regras linguísticas, padrões estruturais e sinais de ataque.  
- **AETHON-ML** — Classificador supervisionado (TF-IDF + LR / SBERT + LR).  
- **AETHON-Full** — Mitigação adaptativa + auditoria contínua + privacidade diferencial.

---

# 📁 Estrutura do Repositório

aethon_repo/
├── datasets/ # datasets brutos (não versionados)
│ └── prepared/ # train/val/test + masked_preview.csv seguro
├── docs/ # drafts: architecture, validation, results
├── notebooks/ # 03_benchmark_multi_model.ipynb e outros
├── results/ # saídas experimentais (ignored no Git)
├── scripts/ # SLURM jobs e utilitários
├── src/
│ ├── models/ # drivers das LLMs HF & OpenAI
│ ├── aethon_*.py # heurística / ML / full mitigation
│ ├── dataset_loader.py
│ ├── run_experiment.py # pipeline principal
│ ├── run_experiment_chunk.py # usado por SLURM array
│ ├── analysis_utils.py
│ └── prepare_datasets.py
├── experiment_manifest.json # log de execuções (ignored)
├── requirements.txt
└── README.md


---

# 🚀 Como Executar Localmente (WSL / Linux)

### Criar ambiente
```bash
cd ~/Documentos/aethon_repo
python3 -m venv aethon_env
source aethon_env/bin/activate
pip install -r requirements.txt

#	Preparar datasets

python src/prepare_datasets.py

Teste rápido (Phi-2 local)

python src/run_experiment.py --model phi-2 --dataset prompt_injections_train --dry-run --limit 5

#	Testar todos os drivers

python src/test_model_loading.py

#	Para testar OpenAI (consome tokens):

export OPENAI_API_KEY="sk-XXXX"
python src/test_model_loading.py --allow-openai

☁️ Execução no Cluster (SLURM)
Enviar job em array (Mistral / LLaMA)

sbatch --export=MODEL=mistral-7b,DATASET=hf_prompt-injections_train,CHUNKS=10 scripts/run_aethon_array.slurm

O SLURM divide o dataset em fatias (start..end) e cada tarefa executa
src/run_experiment_chunk.py.

🔐 Segurança

⚠️ Nunca commitar chaves (OPENAI_API_KEY).
Já está protegido no .gitignore.

Use apenas:

export OPENAI_API_KEY="sk-xxxx"

Datasets brutos, manifest e resultados também estão ignorados (privacidade e confidencialidade).
# aethon_repo
