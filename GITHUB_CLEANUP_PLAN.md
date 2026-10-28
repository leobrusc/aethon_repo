# GITHUB CLEANUP PLAN — AETHON

**Data**: 2026-06-24  
**Objetivo**: Resolver o problema de LFS e limpar o repositório antes da execução em produção.

---

## 1. Problema Principal

### hf_red_team_attempts.jsonl como blob regular

| Aspecto | Valor |
|---------|-------|
| Arquivo | `datasets/hf_red_team_attempts.jsonl` |
| Tamanho | 55,487,878 bytes (55 MB) |
| Commit de origem | `f440b36` ("Liberando mais arquivos para consulta do Professor Jorge") |
| LFS configurado em | `f506432` (commit posterior) |
| Tracked como LFS? | ❌ NÃO (apesar de `.gitattributes` especificar `*.jsonl filter=lfs`) |
| Listado em `git lfs ls-files`? | ❌ NÃO |
| Conteúdo no HEAD | Dados brutos (JSON-array), não pointer LFS |

**Consequência**: O repositório carrega 55 MB de dados brutos no histórico git permanentemente. Todo clone baixa esse blob desnecessariamente.

---

## 2. Diagnóstico Completo

```
$ git lfs ls-files
4f3a40e85e * datasets/jailbreakbench_behaviors.jsonl      (60 KB) ✅
e7a1b0b9a2 * datasets/neuralchemy_prompt_injection_core.jsonl (2.2 MB) ✅  
e41959c6cd * datasets/notinject.jsonl                      (67 KB) ✅
2e74645416 * datasets/wildjailbreak_eval.jsonl             (1.8 MB) ✅

$ git check-attr filter datasets/hf_red_team_attempts.jsonl
datasets/hf_red_team_attempts.jsonl: filter: lfs   ← configurado mas NÃO migrado
```

O `.gitattributes` marca `*.jsonl` como LFS, mas apenas arquivos commitados APÓS `f506432` foram convertidos. O `hf_red_team_attempts.jsonl` permanece como blob no histórico.

---

## 3. Solução: git lfs migrate

### Opção A: Reescrever histórico (RECOMENDADA para repo com poucos colaboradores)

```bash
# ATENÇÃO: Isso reescreve o histórico do repositório!
# Todos os colaboradores precisarão re-clonar.

# 1. Backup do estado atual
git clone --mirror https://github.com/leobrusc/aethon_repo.git aethon_backup.git

# 2. Executar migração
git lfs migrate import \
  --include="datasets/hf_red_team_attempts.jsonl" \
  --everything

# 3. Verificar que o arquivo agora é um pointer
git show HEAD:datasets/hf_red_team_attempts.jsonl | head -3
# Deve mostrar:
# version https://git-lfs.github.com/spec/v1
# oid sha256:...
# size 55487878

# 4. Verificar redução de tamanho
git count-objects -vH

# 5. Garbage collect
git reflog expire --expire-unreachable=now --all
git gc --prune=now --aggressive

# 6. Force push (DESTRUTIVO - reescreve remote)
git push --force --all
git push --force --tags

# 7. Push LFS objects
git lfs push --all origin
```

**Impacto**:
- Reescreve TODOS os commits a partir de `f440b36`
- Invalida clones existentes de todos os colaboradores
- Reduz pack-size do repo de ~55 MB para ~15 MB

### Opção B: Manter histórico, apenas converter working tree (NÃO resolve o problema)

```bash
# Isso NÃO remove o blob do histórico, apenas converte o arquivo atual
git lfs migrate import --no-rewrite "datasets/hf_red_team_attempts.jsonl"
git add datasets/hf_red_team_attempts.jsonl
git commit -m "Migrate hf_red_team_attempts.jsonl to LFS pointer"
```

**Problema**: O blob de 55 MB permanece no histórico. Clone continua grande.  
**Usar apenas se**: Reescrever histórico não for aceitável.

### Opção C: BFG Repo Cleaner (alternativa à Opção A)

```bash
# Download BFG
# https://rtyley.github.io/bfg-repo-cleaner/

java -jar bfg.jar --convert-to-git-lfs '*.jsonl' --no-blob-protection

git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

---

## 4. Procedimento Recomendado (Passo a Passo)

### Pré-requisitos

- [ ] Confirmar que ninguém mais tem branches ativos no repositório
- [ ] Fazer backup completo (`git clone --mirror`)
- [ ] Ter `git-lfs` instalado e configurado

### Execução

```bash
# No diretório do repo local (limpo, sem uncommitted changes)
cd C:\Users\leolima\Documents\aethon_repo

# 1. Confirmar status limpo
git status
# Output: nothing to commit, working tree clean

# 2. Executar migrate
git lfs migrate import \
  --include="datasets/hf_red_team_attempts.jsonl" \
  --everything

# 3. Verificar resultado
git lfs ls-files
# Deve agora listar 5 arquivos incluindo hf_red_team_attempts.jsonl

git show HEAD:datasets/hf_red_team_attempts.jsonl | Select-Object -First 3
# Deve mostrar pointer LFS

git count-objects -vH
# size-pack deve ser significativamente menor

# 4. Garbage collect
git reflog expire --expire-unreachable=now --all
git gc --prune=now --aggressive

# 5. Force push
git push --force --all
git push --force --tags
git lfs push --all origin
```

### Pós-execução

- [ ] Verificar no GitHub que o arquivo aparece como "Stored with Git LFS"
- [ ] Re-clonar em outra pasta para verificar tamanho
- [ ] Atualizar clone no servidor USP: `rm -rf aethon_repo && git clone ...`
- [ ] Documentar a migração no changelog

---

## 5. Arquivos Residuais na Raiz

Arquivos que existem localmente mas são ignorados pelo `.gitignore`:

| Arquivo | Tamanho | Ação |
|---------|---------|------|
| `pd` | 0 bytes | Deletar manualmente |
| `json` | 0 bytes | Deletar manualmente |
| `package-lock.json` | 90 bytes | Deletar manualmente |
| `test_llamas.py` | 367 bytes | Deletar manualmente |
| `.Rhistory` | 0 bytes | Deletar manualmente |
| `__pycache__/` | ~600 bytes | Deletar manualmente |
| `experiment_manifest.json` | 2.8 KB | Artefato de runtime (ignorado) |

Comando de limpeza:

```powershell
# Local (PowerShell)
Remove-Item pd, json, package-lock.json, test_llamas.py, .Rhistory -ErrorAction SilentlyContinue
Remove-Item -Recurse __pycache__ -ErrorAction SilentlyContinue
```

Estes arquivos NÃO estão no git (são ignorados), então não requerem commit.

---

## 6. Datasets de Backup

Datasets de backup/oficial em `datasets/` que são ignorados pelo `.gitignore`:

| Arquivo | Tamanho | Status |
|---------|---------|--------|
| `hf_red_team_attempts.official.jsonl` | 55 MB | Ignorado pelo .gitignore |
| `red_team_attempts.official.jsonl.gz` | 15 MB | Ignorado pelo .gitignore |
| `hf_red_team_attempts.local_backup_20260519160418.json` | 55 MB | Ignorado pelo .gitignore |

Ação: **Manter** localmente para referência, mas NÃO adicionar ao git. Já corretamente ignorados.

---

## 7. Recomendações de Manutenção Futura

1. **Nunca commitar arquivos >1 MB sem LFS** — o `.gitattributes` já cobre `*.jsonl`, mas considerar adicionar:
   ```
   *.parquet filter=lfs diff=lfs merge=lfs -text
   *.csv filter=lfs diff=lfs merge=lfs -text
   *.pkl filter=lfs diff=lfs merge=lfs -text
   ```

2. **CI check**: Adicionar pre-commit hook que bloqueia arquivos >5 MB não-LFS:
   ```bash
   # .git/hooks/pre-commit
   git diff --cached --name-only | while read file; do
     size=$(git cat-file -s :0:"$file" 2>/dev/null || echo 0)
     if [ "$size" -gt 5242880 ]; then
       echo "ERROR: $file is $(($size/1048576))MB. Use Git LFS."
       exit 1
     fi
   done
   ```

3. **Documentar SHA-256** dos datasets canônicos em `datasets/SOURCES.md` para verificação de integridade pós-clone.

---

## 8. Cronograma de Cleanup

| Passo | Tempo | Dependência |
|-------|-------|-------------|
| Backup mirror | 5 min | Nenhuma |
| `git lfs migrate` | 2-5 min | Backup |
| Verificação local | 2 min | Migrate |
| Force push | 1-2 min | Verificação |
| LFS push | 2-5 min (upload 55MB) | Force push |
| Re-clone verificação | 2 min | LFS push |
| Cleanup servidor USP | 2 min | Force push |

**Total**: ~20 minutos

**EXECUTAR ANTES de começar benchmarks no servidor USP** para evitar download desnecessário de 55 MB de blob ineficiente.
