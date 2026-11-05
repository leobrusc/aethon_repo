# AETHON — consolidação científica de 28/10/2026

## Entrega e diagnóstico inicial

Branch: `research/jorge-2026-experimental-upgrade`. Não houve merge na main,
reescrita de histórico, force push ou migração LFS. O SHA de entrega pode ser
consultado com `git rev-parse HEAD`; cada execução arquiva seu próprio SHA.

HEAD inicial: `66644cc`, na branch científica. A main local/remota estava em
`2964556`. Após fetch, a branch científica tinha 12 commits locais não publicados
e um commit remoto divergente (`6ec4b81`). Ela foi usada como base por conter os
avanços de detecção, calibração, diagnósticos e retomada ausentes na main.

O merge remoto incorporou remoções de artefatos históricos; elas foram corrigidas
no commit `cdd7907`, restaurando os arquivos do HEAD inicial. A comparação
`git diff 66644cc HEAD -- results` ficou vazia. O commit de merge permanece no
histórico; nenhum reset ou rebase foi usado.

Foram preservadas fora dos novos commits as alterações preexistentes em
`src/close_harness.py`, `tests/test_harness_closure.py` e os três auxiliares
`close_harness.validated.backup.py`, `test_harness_closure.validated.backup.py` e
`validated_tpr_auroc_closure.patch`. A árvore permanece modificada por esse trabalho
do usuário. Manifests registram `git_dirty=true`; os runs finais também registram
hashes da implementação relevante. O PR inclui a base científica local previamente
não publicada, mas não inclui essas alterações ainda não commitadas.

Riscos encontrados: treinamento recomendado com dados externos de avaliação;
seleção e estimativa no mesmo OOF; calibração com representação ajustada fora dos
folds de calibração; McNemar genérico contando somente parte das discordâncias;
join estatístico por hash capaz de multiplicar duplicatas; interpretação de strings
JSON como booleanos; denominadores ASR que descartavam julgamentos ausentes;
revisões mutáveis e semântica de classes com fallback silencioso.

## Alterações implementadas e arquivos

O inventário completo está em
[`research_2026_evidence/changed_files.txt`](research_2026_evidence/changed_files.txt).

| Área | Arquivos principais | Mudança |
|---|---|---|
| Integridade | `src/research_integrity.py`, `src/train_detector.py`, README, REPRODUCIBILITY | Identidade por origem/posição e hashes bruto/normalizado; proveniência; duplicatas; seleção restrita ao treino |
| Seleção | `src/research_generalization.py` | Nested CV agrupada; calibração do pipeline inteiro; FPR da decisão OR; modelo versionado e congelado |
| Estatística | `src/analysis_utils.py`, `src/model_selection.py`, `src/research_paired.py` | McNemar exato sobre acertos/erros nas duas classes; pareamento único; bootstrap pareado/agrupado |
| Baselines | `src/baseline_detectors.py`, `src/research_baseline.py` | Revisões imutáveis; classes explícitas; offline por padrão; hashes de pesos/tokenizer; retomada validada |
| Respostas | `src/benchmark/asr.py`, `src/research_response.py`, `src/research_e2e.py` | Booleano JSON estrito; objetivos/rubricas; limites ASR; revisão humana; checkpoints privados |
| Latência/ASR | `src/benchmark/{middleware,detection,metrics,results,runner}.py` | Etapas separadas, percentis, denominadores elegíveis e incerteza explícita |
| DP | `src/research_dp.py` | Simulação reproduzível de utilidade/variância/erro/composição; separada de privacidade do texto |
| Validação | `tests/test_research_*.py`, `pytest.ini` | Testes científicos e de integração; descoberta limitada a tests, preservando backups |
| Protocolo | quatro documentos solicitados, `configs/research_2026/`, este relatório | Seleção autorizada, limites de evidência, configurações e execução futura |
| Evidências | `scripts/{export_research_evidence,compare_research_smoke,validate_research_baseline,validate_historical_decisions}.py` | Exportação permitida, comparação pareada e checagens reais locais |

## Execuções efetivamente concluídas

Evidências públicas sem textos estão em
[`research_2026_evidence/index.json`](research_2026_evidence/index.json), com hashes.
Os diretórios completos locais ficam em `results/research_2026/`, ignorados pelo Git.
`.gitattributes` preserva os bytes das evidências entre Windows/Linux sem alterar
as regras LFS existentes. `scripts/verify_research_evidence.py --git-tree HEAD`
verifica hashes do checkout e dos blobs commitados. Espaços válidos gerados pelo
Matplotlib no SVG são preservados para manter a identidade do artefato.
O inventário de versões observado está em `local-environment.txt`; não é um lock
portável para GPU. Ambiente: Windows, Python 3.10.11, NumPy 2.2.6, pandas 2.3.3,
scikit-learn 1.7.2, transformers 4.46.3 e torch 2.12.0; CPU/hardware nos manifests.

### Auditoria

Run `integrity-final-2026-10-28`: 9.685 registros, sendo 546 de treino e exatamente
9.139 da referência histórica. Foram identificados 201 grupos de duplicatas exatas
e 636 pares aproximados. Entre treino e referência: zero grupos exatos e um par
aproximado. A triagem usa NFKC, colapso de whitespace e TF-IDF char_wb 3–5,
cosseno >= 0,95. Não equivale a auditoria semântica. Nenhuma linha ou label foi
removida, corrigida ou usada para escolher modelos a partir da referência.

Uma primeira versão da busca aproximada foi interrompida por custo excessivo;
a implementação esparsa concluiu a auditoria. Apenas runs concluídos alimentam
as evidências exportadas. Reexecução do run final validou hashes sem recomputar.

### Estudo aninhado restrito ao treino

Run `nested-final-2026-10-28`: cinco candidatos, cinco folds externos e três
internos, todos sobre 546 exemplos (343 benignos/203 adversariais). O agrupamento
impede que duplicatas normalizadas cruzem folds. Sigmoid calibra o pipeline inteiro
com três folds agrupados dentro de cada subconjunto de ajuste. Não houve isotonic.

Predições externas agregadas: TP=175, TN=330, FP=13, FN=28; precision=0,930851,
recall=0,862069, F1=0,895141, FPR=0,037901. Estes resultados estimam a estratégia
de seleção dentro da distribuição autorizada; não são generalização independente.
AUROC/AUPRC são reportadas por fold, pois margens e probabilidades selecionadas
não têm escala global comparável. Brier/ECE só aparecem para modelos probabilísticos.

A seleção final com todo o treino escolheu char_wb 3–5 + LinearSVC, threshold de
margem -0,09982680741311112. O artefato é `research_margin_or_v2026`, não B3.
Modelo local: `results/research_2026/generalization/nested-final-2026-10-28/detector.joblib`,
SHA-256 `4572551cbeb80b0d2e2a8dc0511652fc349459918c49d8cc4d85f11456864787`.
Pesos não são versionados. A execução foi repetida em duas versões do runner;
as predições externas numéricas tiveram o mesmo hash. SVGs podem diferir em
metadados/identificadores de renderização. A retomada do run final validou todos
os hashes, inclusive o modelo, sem reexecutar seleção.

**B3 permanece referência.** Não houve comparação apropriada que justifique
promovê-lo/substituí-lo. F1/FPR acima não podem ser comparados diretamente aos
históricos B3 AUROC 0,6766/F1 0,6617/FPR 0,1887, medidos em outro pool.
Os resultados históricos CharSVM e o over-defense do WildJailbreak continuam
evidência contextual, não foram reapresentados como novas execuções.

### Baselines modernos

ProtectAI: smoke CPU real de 18 prompts (até dois por classe/fonte), sem download,
usando revisão `90c9989b1a342275dd0d1a95aad283c04e075671` já em cache.
SAFE=0/INJECTION=1, probabilidade >= 0,5, limite de 512 tokens; pesos, configuração
e tokenizer têm hashes no manifest. O run final
`protectai-validated-smoke-2026-10-28` concluiu 18/18 e retomou sem reinferência,
preservando proveniência. Um teste específico protege essa propriedade.

Consistência real individual/batelada: dois exemplos, diferença máxima de score
0,0, decisões idênticas a threshold 0,5. Isso não substitui validação completa GPU.
Comparação pareada de infraestrutura: 18 registros, B3 histórico reutilizado contra
ProtectAI smoke; McNemar exato bilateral p=1,0, bootstrap pareado estratificado
com seed 2026 e 200 réplicas/IC 95%. Não se afirma equivalência, superioridade ou
significância confirmatória com esse smoke pequeno e não representativo.

Prompt Guard: revisão pública fixada
`11614a155199674a0a95e6602d6ab0417b790ed0`; o snapshot local não estava disponível.
Status NOT_RUN com LocalEntryNotFoundError explícito. Não houve tentativa de
obter pesos gated. Detectores de injection não são automaticamente detectores
equivalentes de jailbreak geral.

### DP e equivalência

Reanálise histórica: B3/B4 pareados por dataset/row/hash em 9.139 registros,
zero divergências. Não foi nova inferência. Testes adicionais validam equivalência
com classificador injetado para epsilon 0,5/1,2/2,5.

Run `dp-final-2026-10-28`: 10.000 sorteios Laplace por epsilon, seed 2026,
sensibilidade sintética 1, contador 100 e warmup 100 por epsilon. MAE observado:
1,991440 / 0,829767 / 0,398288; variância: 7,836613 / 1,360523 / 0,313465.
O relatório inclui erro relativo, variância teórica e composição básica por
número de liberações. Esta simulação não estabelece DP da aplicação ou do texto.

No ambiente local, p50 do sorteio foi aproximadamente 0,0004 ms nos três epsilons;
os percentis completos constam nos CSVs. A medição exclui I/O e não representa
overhead total de auditoria. Parsing, heurística, classificador, decisão, auditoria,
LLM e total têm campos separados; ainda falta um estudo operacional completo por
ambiente. Não foram comparados CPU local e GPU GCP.

## Testes e incidentes

- `python -m pytest -q`: **106 passed, 1 warning, 16,03 s** na execução final.
- Aviso esperado: teste que simula falha de download no driver HF causal.
- O comando inicial falhou ao coletar um backup local de nome pontuado. `pytest.ini`
  restringe a descoberta à suíte `tests`, sem apagar ou renomear o backup.
- Uma execução intermediária passou testes mas emitiu exceções nativas no softmax
  PyTorch/Windows. A normalização dos pequenos logits finais passou para SciPy;
  execuções seguintes e smoke real concluíram sem essas exceções.
- Houve negações intermitentes de criação de processo. Comandos necessários foram
  retomados; a autenticação GitHub funcionou fora da restrição de rede.
- Testes cobrem contingências conhecidas, pares inválidos, bootstrap reproduzível,
  conflitos/duplicatas, folds agrupados, piso heurístico, calibração, ASR incompleto,
  concordância, retomada privada com driver simulado, classes desconhecidas,
  batching sem pesos, retomada completa preservando hashes e equivalência DP.
- Verificação Git confirmou ausência de alterações em resultados históricos.

## Antes e agora

| Antes | Agora |
|---|---|
| Recomendação de treino incluindo avaliação externa | Treino padrão e autorizado limitado a prompt_injections_train |
| Estimativa de seleção reutilizando OOF | Pipeline novo com avaliação externa aos folds de seleção |
| Classe desconhecida com fallback | Falha explícita; revisão congelada no novo runner |
| Ausência de julgamento removida do denominador | Limites ASR, cobertura e denominador elegível preservados |
| McNemar parcial/join por hash | Correção por ambas as classes e identidade única |
| Resultado local implícito | Manifests, hashes, status, contagens e evidências exportadas |

## Reprodução local em PowerShell

```powershell
Set-Location C:\Users\leolima\Documents\aethon_repo
.\venv\Scripts\Activate.ps1
python -m pytest -q
python src/research_integrity.py --run-id integrity-reproduction
python src/research_generalization.py --run-id nested-reproduction
python src/research_dp.py --run-id dp-reproduction
python src/research_baseline.py --model protectai --revision 90c9989b1a342275dd0d1a95aad283c04e075671 --run-id protectai-reproduction --smoke
python src/research_baseline.py --model protectai --revision 90c9989b1a342275dd0d1a95aad283c04e075671 --run-id protectai-reproduction --smoke --resume
```

Use IDs novos para novas medições. Runs completos existentes validam hashes;
mudança na implementação/configuração/dados exige um novo ID. Os scripts de
exportação e reanálise documentam os IDs desta entrega; não fazem download.

## GCP, experimentos pendentes e limitações

Comandos Linux e revisão ProtectAI GPU estão em
[GCP_EXECUTION_READINESS.md](GCP_EXECUTION_READINESS.md). Configurações em
`configs/research_2026/` preparam baselines e os cinco alvos LLM. As revisões dos
alvos permanecem nulas de propósito até congelamento; GPT-4o-mini depende de acesso.

Não executados: baseline moderno completo, inferência LLM pareada real, validação
humana, ASR por objetivo, preservação de tarefas legítimas, estudo completo de
latência e execução GCP. O coletor privado possui integração simulada; o protocolo
de julgamentos estruturados ainda precisa de rubricas específicas e avaliadores.
Não há resultado novo de redução efetiva de ASR.

Riscos metodológicos restantes: referência externa previamente observada;
generalização independente ainda sem dados prospectivos; auditoria semântica
pendente; agrupamento atual cobre duplicatas normalizadas, não todas as famílias;
treino pequeno e seleção entre poucos candidatos; intervalos bootstrap não modelam
toda a incerteza de ajuste; poucos clusters de datasets; calibração isotonic sem
amostra suficiente; proteção de texto/segredos/ACL depende também de controles
operacionais. O coletor privado exige confirmação do operador sobre permissões e
retention; padrões de credenciais não garantem sanitização completa. A composição
DP exige limites de contribuição e orçamento definidos no sistema real.

## Matriz de status

| Frente | Status | Limite |
|---|---|---|
| Preservação histórica, auditoria lexical e testes locais | DONE | Revisão semântica separada |
| Nested CV, calibração, thresholds e exportação | DONE | Estudo na distribuição de treino |
| Generalização independente e promoção de novo detector | NOT_RUN | Dados prospectivos e comparação apropriada |
| ProtectAI smoke, batching e retomada local | DONE | 18 prompts; GPU pendente |
| Baselines modernos completos | NOT_RUN | Execução futura |
| Prompt Guard | NOT_RUN | Snapshot local ausente; acesso gated |
| Protocolo/coletor/julgamentos ASR | PARTIAL | Integração simulada; humanos e LLMs pendentes |
| ASR real nos cinco alvos | NOT_RUN | Sem inferência LLM nesta etapa |
| Equivalência B3/B4 histórica e simulação DP | DONE | Não prova DP do sistema real |
| Overhead operacional e latência por ambiente | PARTIAL | Campos e ruído medidos; estudo completo pendente |
| GCP | NOT_RUN | Configuração e comandos preparados |
| Bloqueios de ambiente iniciais | DONE | Contornados por execução autorizada, sem perda de dados |
