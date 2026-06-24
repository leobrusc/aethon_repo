# CLOUD EXECUTION PLAN — AETHON

**Data**: 2026-06-24  
**Objetivo**: Plano de execução dos benchmarks no servidor USP LABIC (máquina `chope`).

---

## 1. Infraestrutura Disponível

| Item | Especificação |
|------|---------------|
| **Gateway** | `ssh pgfn@143.107.183.116 -p 22322` |
| **Máquina** | `chope` |
| **GPU** | NVIDIA RTX A5000 (24 GB VRAM) |
| **RAM** | 126 GB |
| **CUDA** | Disponível |
| **PyTorch** | 2.12.1+cu130 |
| **GitHub SSH** | Configurado (user: `leobrusc`) |
| **HF Token** | Válido |
| **HF Acesso** | Llama 2 ✅, Llama 3.2 ✅, Qwen ✅ |

---

## 2. Estimativa de Runtime na A5000

A RTX A5000 com 24GB VRAM oferece throughput ~50-100x superior ao observado localmente (CPU inference).

### Estimativas baseadas em benchmarks da comunidade

| Modelo | VRAM Requerida | Tokens/s (A5000 FP16) | Est. por Prompt (256 tok) | Est. Full Run |
|--------|---------------|----------------------|--------------------------|---------------|
| Llama-3.2-1B | ~3 GB | ~200 tok/s | ~1.3 s | ~83 horas |
| Llama-3.2-3B | ~7 GB | ~100 tok/s | ~2.6 s | ~166 horas |
| Phi-3-Mini (3.8B) | ~8 GB | ~80 tok/s | ~3.2 s | ~205 horas |
| Qwen2.5-3B | ~7 GB | ~100 tok/s | ~2.6 s | ~166 horas |
| **Qwen2.5-7B** | ~15 GB | ~50 tok/s | ~5.1 s | **~326 horas (13.6 dias)** |
| **Llama-2-7B** | ~14 GB | ~55 tok/s | ~4.7 s | **~300 horas (12.5 dias)** |

**Nota**: Estimativas conservadoras. B2-B4 bloqueiam prompts adversariais antes da inferência, reduzindo tempo real em ~60-70% para datasets adversarial-only.

### Estimativa ajustada (com blocking B2-B4)

Para os benchmarks dedicados (5 datasets, 5 condições):
- `notinject` (339 rows): Toda inferência ocorre (benign)
- `prompt_injection_core` (6,274 rows): ~60% bloqueado em B2-B4
- `jailbreakbench_behaviors` (200 rows): ~50% bloqueado em B2-B4
- `red_team_attempts` (38,961 rows): ~90% bloqueado em B2-B4
- `cyberseceval_prompt_injection` (251 rows): ~90% bloqueado em B2-B4

| Modelo | B0 (full inference) | B1 (partial block) | B2-B4 (heavy block) | Total Estimado |
|--------|--------------------|--------------------|---------------------|----------------|
| **Qwen2.5-7B** | ~65 h | ~55 h | ~30 h × 3 = 90 h | **~210 horas (8.7 dias)** |
| **Llama-2-7B** | ~60 h | ~50 h | ~27 h × 3 = 81 h | **~191 horas (8.0 dias)** |

---

## 3. Priorização de Execução

### Prioridade 1: Modelos 7B no servidor USP (OBRIGATÓRIOS)

Estes modelos são **inviáveis localmente** e devem rodar EXCLUSIVAMENTE no servidor:

| # | Modelo | Config | Estimativa A5000 |
|---|--------|--------|-----------------|
| 1 | `qwen2.5-7b-instruct` | `configs/qwen7b_benchmark.json` | ~8.7 dias |
| 2 | `llama-2-7b-chat` | `configs/llama7b_benchmark.json` | ~8.0 dias |

### Prioridade 2: Modelos 3B no servidor USP (RECOMENDADO)

Embora teoricamente possíveis localmente, levariam meses. No servidor: dias.

| # | Modelo | Config | Estimativa A5000 |
|---|--------|--------|-----------------|
| 3 | `qwen2.5-3b-instruct` | `configs/qwen3b_benchmark.json` | ~5.5 dias |
| 4 | `llama-3.2-3b-instruct` | `configs/llama3b_benchmark.json` | ~5.5 dias |
| 5 | `phi-3-mini-4k-instruct` | `configs/phi3_benchmark.json` | ~6.8 dias |

### Prioridade 3: Modelo 1B (pode ser local ou servidor)

| # | Modelo | Config | Estimativa A5000 | Estimativa Local (GPU) |
|---|--------|--------|-----------------|----------------------|
| 6 | `llama-3.2-1b-instruct` | `configs/llama1b_benchmark.json` | ~2.8 dias | ~32 dias (CPU only) |

---

## 4. Ordem de Execução Recomendada

```
Servidor USP (sequencial, 1 GPU):

1. [DIA 1-9]   Qwen2.5-7B   → configs/qwen7b_benchmark.json
2. [DIA 9-17]  Llama-2-7B   → configs/llama7b_benchmark.json
3. [DIA 17-23] Llama-3.2-3B → configs/llama3b_benchmark.json
4. [DIA 23-29] Qwen2.5-3B   → configs/qwen3b_benchmark.json
5. [DIA 29-36] Phi-3-Mini   → configs/phi3_benchmark.json
6. [DIA 36-39] Llama-3.2-1B → configs/llama1b_benchmark.json

Total estimado: ~39 dias (sequencial, 1 GPU)
```

### Alternativa: Execução paralela (se disponível 2ª máquina)

```
GPU A:                           GPU B:
1. Qwen2.5-7B (9 dias)          1. Llama-2-7B (8 dias)
2. Llama-3.2-3B (5.5 dias)      2. Qwen2.5-3B (5.5 dias)
3. Phi-3-Mini (6.8 dias)        3. Llama-3.2-1B (2.8 dias)

Total: ~21 dias (paralelo)
```

---

## 5. Procedimento de Setup no Servidor

### 5.1 Acesso e Clone

```bash
# 1. Conectar via gateway
ssh pgfn@143.107.183.116 -p 22322

# 2. Acessar máquina chope
ssh chope

# 3. Clone (ou pull se já existir)
cd ~/workspace
git clone git@github.com:leobrusc/aethon_repo.git
cd aethon_repo

# 4. Pull LFS files
git lfs pull
```

### 5.2 Ambiente Python

```bash
# Verificar CUDA
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"

# Criar venv
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Verificar acesso HF
huggingface-cli whoami
```

### 5.3 Validação Rápida

```bash
# Dry-run validation
python src/run_benchmark.py \
  --config configs/qwen7b_benchmark.json \
  --fast-validation --dry-run

# Timing probe (5 prompts, apenas B0)
python src/run_benchmark.py \
  --config configs/qwen7b_benchmark.json \
  --dataset-limit 5 --condition-filter B0
```

### 5.4 Execução Full (com screen/tmux)

```bash
# Usar screen para persistir sessão
screen -S aethon_qwen7b

# Executar benchmark completo
python src/run_benchmark.py --config configs/qwen7b_benchmark.json

# Detach: Ctrl+A, D
# Reattach: screen -r aethon_qwen7b
```

### 5.5 Monitoramento

```bash
# Em outra sessão
watch -n 60 cat results/qwen7b_benchmark/aggregated/progress.json

# Verificar GPU utilization
nvidia-smi -l 5

# Verificar disk space
df -h
du -sh results/
```

### 5.6 Resume após Interrupção

```bash
# O benchmark já está configurado com resume: true
# Basta re-executar o mesmo comando:
python src/run_benchmark.py --config configs/qwen7b_benchmark.json --resume

# Ou com run-id explícito:
python src/run_benchmark.py \
  --config configs/qwen7b_benchmark.json \
  --run-id aethon_20260611T095820Z_da12c73e \
  --resume
```

---

## 6. Configuração Específica para Modelos Gated

```bash
# Configurar HF Token
export HF_TOKEN="<token>"

# Verificar acesso a modelos gated
python -c "
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained('meta-llama/Llama-2-7b-chat-hf')
print('Llama-2 OK')
tok = AutoTokenizer.from_pretrained('meta-llama/Llama-3.2-1B-Instruct')
print('Llama-3.2 OK')
tok = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct')
print('Qwen OK')
"
```

---

## 7. Requisitos de Espaço em Disco

| Item | Tamanho Estimado |
|------|-----------------|
| Repositório + datasets | ~200 MB |
| HF model cache (Qwen 7B) | ~14 GB |
| HF model cache (Llama 2 7B) | ~14 GB |
| HF model cache (todos os 6 modelos) | ~50 GB |
| Resultados por modelo (CSV) | ~500 MB |
| Total resultados (6 modelos) | ~3 GB |
| **Total estimado** | **~67 GB** |

Com 126 GB RAM e espaço em disco adequado, não deve haver restrição.

---

## 8. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Queda de conexão SSH | Perda de progresso | screen/tmux + resume mode |
| Disco cheio | Crash | Monitorar `du -sh` + limpar cache se necessário |
| OOM GPU | Crash no 7B | FP16 padrão cabe nos 24GB; se necessário, ativar 4-bit quantization |
| Timeout HF download | Falha no start | Pré-download com `huggingface-cli download` |
| Manutenção do servidor | Interrupção | Resume mode + progress.json |
| Token HF expirado | Falha no acesso gated | Verificar `huggingface-cli whoami` antes |

---

## 9. Modelos API (Execução Local)

Os modelos API não requerem GPU e podem rodar em qualquer máquina com internet:

```bash
# Local (após configurar credenciais)
export OPENAI_API_KEY="..."
export DEEPSEEK_API_KEY="..."

python src/run_benchmark.py \
  --models gpt-5.4-nano gpt-5.4-mini deepseek-v4-flash \
  --datasets notinject prompt_injection_core jailbreakbench_behaviors red_team_attempts cyberseceval_prompt_injection \
  --conditions B0 B1 B2 B3 B4 \
  --ml-model-path src/models/aethon_tfidf_lr.pkl \
  --asr-judge-type rule
```

**Estimativa API** (46,025 prompts × 5 condições × 3 modelos = 690,375 calls):
- Rate-limited: ~2-5 dias dependendo do tier
- Custo estimado: GPT-5.4-nano/mini são geralmente baratos (~$0.10-0.50/1M input tokens)

---

## 10. Checklist Pré-Execução

- [ ] Resolver LFS issue antes de clonar no servidor (ver GITHUB_CLEANUP_PLAN.md)
- [ ] Verificar espaço em disco no servidor (>70 GB livres)
- [ ] Confirmar token HF válido e acesso aos modelos gated
- [ ] Executar dry-run validation em cada config
- [ ] Executar timing probe (5 prompts) para calibrar estimativas reais na A5000
- [ ] Configurar screen/tmux
- [ ] Configurar monitoramento (progress.json, nvidia-smi)
- [ ] Informar administrador do LABIC sobre uso prolongado da GPU (~39 dias)
