# POST_MERGE_VALIDATION

**Parecer final: ENGINEERING_BASELINE_VALIDATED.**
Escopo: baseline de engenharia e preservação científica; não constitui validação de eficácia em campanha prospectiva.

Execução: `post-merge-20261105T141025Z`. Encerramento UTC: `2026-11-05T14:18:08.490306+00:00`.

## 1. Identificação e verificações Git

- Merge do [PR #7](https://github.com/leobrusc/aethon_repo/pull/7): `9ed55709add0fc45f63847a0394315863faa0876`.
- Candidata preservada: `52e592e0238b80536c85faee633566685d55d178`.
- Pais do merge: `29645563bd64a67aae2482ab6c87bd5e32fecb11 52e592e0238b80536c85faee633566685d55d178`.
- Árvore de ambos os commits: `ec6a0cc85a73fd5dcad11823c9b19454a88fd245`; igualdade exata confirmada.
- PASS: candidata ancestral do merge; worktree detached em `.worktrees/post-merge-validation` no SHA exato.
- PASS: worktree limpo antes e depois dos controles. A única alteração visível final é este novo relatório não commitado; evidências e instalações ficam em `results/`, ignorado pelo Git.
- PASS: cinco arquivos preexistentes no checkout original preservados, hashes iguais ao registro anterior, mesmo status de dois modificados e três não rastreados.
- Nenhuma branch foi movida. Nenhum merge, push, rebase, force push, atualização de lock, exclusão ou release foi executado nesta validação.

## 2. Engenharia e testes

| Controle | Resultado | Evidência |
| --- | --- | --- |
| Pytest completo | PASS: 144 testes, um aviso esperado de download simulado | pytest.txt |
| Ruff: src, tests, scripts | PASS | ruff.txt |
| pip check do ambiente mantido | PASS | pip-check.txt |
| Guard completo desde a main anterior e guard staged | PASS | guard-main.txt; guard-staged.txt |
| git diff --check desde a main anterior | PASS | diff-check.txt |
| Build sdist + wheel sem isolamento do backend e sem downloads | PASS | build.txt; build-hashes.json |
| Wheel instalado em venv novo, import comprovado dentro do venv | PASS | wheel-install-retry.txt; installed-import-retry.txt |
| Sete CLIs do wheel: benchmark, detect, train, integrity, generalization, baseline, dp | PASS: --help | cli-*.txt |
| Instalação editable em segundo venv e import do src deste worktree | PASS | editable-install.txt; editable-import.txt |
| Dry-run source e editable, duas linhas cada | PASS: zero falhas e campos semânticos iguais | cli-comparison.json; cli-*-dry-run.txt |
| Declarações de dependências, locks e manifests históricos | PASS: hashes preservados | git-and-preservation.json; final-preservation.json |

Ambiente: Python 3.12.13 mantido, com PYTHONPATH explícito para o src do commit nas verificações da fonte e flags offline HF/datasets. A instalação do pacote é isolada; dependências terceiras do ambiente mantido são expostas por um arquivo .pth em leitura. Não é uma alegação de reinstalação limpa de todas as dependências. A CI definitiva fez instalações independentes de perfis em Windows/Linux.

Rastreabilidade da correção do comando de instalação: a primeira tentativa herdou PYTHONPATH e o pip considerou a mesma versão já instalada, sem copiar o wheel; o teste de import falhou e impediu falso PASS. O comando corrigido removeu PYTHONPATH e instalou o wheel com --ignore-installed --no-deps apenas no novo venv. Import e todos os CLIs passaram. O registro inicial foi preservado; não foi necessário alterar código ou repetir pytest. O wheel contém código; datasets e reprodução usam checkout/editable conforme a arquitetura documentada.

## 3. Integridade científica

- PASS: 127 arquivos científicos protegidos, 31 evidências indexadas em checkout e Git HEAD e seis manifests históricos.
- PASS: 9.139 pares B3/B4 únicos por dataset/prompt_id/prompt_sha256, labels iguais e zero divergências de decisão.
- PASS: 80 valores de F1/FPR/AUROC/AUPRC recalculados dos resultados históricos e comparados ao CSV publicado, atol=1e-12, rtol=0; NaNs equivalentes. Não houve reescrita dos CSVs.
- PASS: replay determinístico local B0–B4 sobre 9.139 registros, 25 comparações, zero mismatches; ruído sintético verificado com escopo explícito. Não é nova inferência LLM nem nova campanha.
- PASS: cinco payloads canônicos LFS, OIDs SHA-256 comparados aos arquivos hidratados; git lfs fsck passou.
- PASS: blob do CSV histórico idêntico ao PR #1; árvore consolidada idêntica à candidata publicada; nenhum resultado, dataset, threshold, seed, label ou protocolo científico alterado.
- NOT_AUDITED: hash canônico independente do dataset bruto. OID LFS/local comprova continuidade, não referência independente confiável.

## 4. Segurança

| Perfil | Consulta upstream/dependências | Instalação local | Proveniência PyTorch |
| --- | --- | --- | --- |
| cpu-linux-py312.lock | PASS: zero achados/skips | NOT_RUN | NOT_RUN |
| cpu-windows-py312.lock | PASS: zero achados/skips | PASS | PASS |
| dev-linux-py312.lock | PASS: zero achados/skips | NOT_RUN | NOT_RUN |
| dev-windows-py312.lock | PASS: zero achados/skips | PASS | PASS |
| gpu-linux-py312.lock | PASS: zero achados/skips | NOT_RUN | NOT_RUN |
| research-linux-py312.lock | PASS: zero achados/skips | NOT_RUN | NOT_RUN |
| research-windows-py312.lock | PASS: zero achados/skips | PASS | PASS |

Os sete locks foram reconsultados sem supressões; hashes dos locks foram conferidos contra o ledger de resolução. Perfis Windows CPU/development/research existentes foram conferidos quanto a versões exatas, ausência de pacotes não declarados e recibos PEP 610 de URL/hash oficiais do torch. Os outros perfis tiveram auditoria de dependências local, sem pretensão de instalação Linux/CUDA neste Windows.

NOT_AUDITED permanece para catálogo dos binários exatos +cpu/+cu; skips nativos do torch e do projeto local são mantidos nos JSONs. A consulta upstream separada não transforma esses skips em cobertura binária. FAIL histórico para processamento irrestrito de entradas hostis continua reconhecido; o ambiente histórico não foi usado. Nenhuma dependência ou lock foi atualizado.

## 5. CI definitiva e artefatos

- Candidata: [run 42037363713](https://github.com/leobrusc/aethon_repo/actions/runs/42037363713), SHA `52e592e`, SUCCESS; evidência pré-merge, não substitui a execução abaixo.
- Commit definitivo: [run 42041263626](https://github.com/leobrusc/aethon_repo/actions/runs/42041263626), evento push em main, SHA `9ed55709add0fc45f63847a0394315863faa0876`, SUCCESS.

- [research-and-gpu-audit](https://github.com/leobrusc/aethon_repo/actions/runs/42041263626/job/127292377452): SUCCESS.
- [cpu-development (windows)](https://github.com/leobrusc/aethon_repo/actions/runs/42041263626/job/127292377582): SUCCESS.
- [cpu-development (linux)](https://github.com/leobrusc/aethon_repo/actions/runs/42041263626/job/127292377942): SUCCESS.

Outros workflows associados ao SHA estão registrados em ci-runs.json; não foram confundidos com o workflow completo de engenharia. Os cinco artefatos abaixo foram baixados (menos de 1 MiB no total), seus relatórios de segurança/replay inspecionados, e hashes dos arquivos extraídos registrados em ci-downloaded-hashes.json. O digest ZIP abaixo é o declarado pelo GitHub, não uma verificação independente do ZIP.

| Artefato | ID | Bytes | Digest informado pelo GitHub |
| --- | --- | --- | --- |
| security-windows | 13424010211 | 9262 | `sha256:8ed852c189d2b971e60924fd9ed844a9a3e97485ef000e2a97c6b5bce0a8cbf3` |
| validation-windows | 13423790259 | 1777 | `sha256:4a309edb062cb27ef41fb8fd8eca487c7a4a401de4bb7f04f714ce0da60b2dcf` |
| security-linux | 13423070141 | 9099 | `sha256:aa94e4348a6fef78e04f4f6f6132919113be71d0274aef07369efd23bcb814dc` |
| validation-linux | 13422470194 | 1758 | `sha256:137614ed28444e7176323f8030562a202ad1e42fef455d1e4e579275d7dcf7a1` |
| security-research-cuda | 13420688857 | 8077 | `sha256:8d589b6a12bed9d7ed49e24743862815218e2c5e7d94c2846008e03c522c6431` |

## 6. Riscos residuais e próxima fase científica

- NOT_AUDITED: vulnerabilidades dos binários exatos do PyTorch e hash canônico independente do dataset bruto.
- NOT_RUN: inferência GPU, ASR prospectiva, equivalência científica com poder estatístico e novos baselines completos. Os smokes e replays não demonstram eficácia externa.
- Pendente: referência externa já observada, revisão semântica de sobreposição, incerteza de seleção/agrupamento e rubricas/validação humana para ASR.
- REVIEW: licença/ownership explícitos antes de release ou redistribuição. Nenhuma release criada.

Próxima fase recomendada: congelar um protocolo prospectivo versionado e um holdout realmente não observado, com revisão semântica de vazamento, proveniência e hashes de referência independentes. Definir objetivos ASR, rubricas, revisão humana, manutenção de tarefas legítimas, critérios de aceitação e análise de incerteza antes da coleta. Fixar snapshots de modelos, ambientes, seeds e thresholds escolhidos somente com treino. Depois executar um piloto pareado limitado, sob autorização de hardware/custos e armazenamento privado de respostas, seguido da campanha planejada; sempre IDs novos e sem promover novos detectores com base no histórico já observado.

## 7. Parecer e evidências

**ENGINEERING_BASELINE_VALIDATED**: testes, build, instalação, CLIs, guards, identidade científica, sete auditorias e CI do merge passaram no escopo declarado. Resultados científicos publicados foram preservados; eficácia prospectiva e segurança universal não são inferidas.

Evidências locais: `results/audit/post-merge-20261105T141025Z/`.
checks.json contém comandos, cwd, códigos de saída e SHA-256 dos logs. Git, replay, métricas, payloads LFS, build e CI têm JSONs próprios. O relatório permanece local, não commitado; nenhum PR adicional foi necessário para esta entrega. Publicação posterior deve usar branch separada e PR em rascunho.
