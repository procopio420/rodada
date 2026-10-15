# Evidência local e handoff — 2026-10-14

## Identificação
- Branch: `codex/ux-teste-mobile`.
- HEAD base: `bbaa14799d832c60b3c2404f0e34e70f387512b1`; implementação em alterações locais.
- Classificação: R2, apresentação e navegação operacional no Atendimento Web.
- Contratos: Spec 029, `specs/024-attendance-web`, `specs/027-table-service-claim`
  e `docs/design/system.md`. Sem nova decisão arquitetural que exija ADR.
- Consulta de PRs abertos via GitHub: #158 (diretrizes UX), #155 (impressão) e
  #118 (aceites 023/024). #158 também toca o design system e exige conciliação
  documental antes de futura integração. Esta slice usa o contrato do HEAD local;
  não aplica documentos ainda em revisão como se estivessem integrados.

## Autoria desta slice
- `apps/web/app/attendance/page.tsx` e `mobile-design.css`: estilos por superfície.
- `apps/web/components/attendance-web.tsx`: grade, filtros e estado de leitura indisponível.
- `apps/web/components/order-workspace.tsx`: atalhos, feedback, seleção visual,
  saldo canônico e preços históricos.
- `apps/web/components/attendance-draft.tsx`: região focalizável para atalho.
- `apps/web/tests/visual/attendance-mobile-design.spec.ts`: jornadas e regressões.
- `apps/web/tests/visual/attendance-dialogs.spec.ts` e `attendance.spec.ts`:
  expandir mesa antes das ações e usar o rótulo existente “Abrir comanda”.
- `docs/design/system.md` e esta pasta de spec.

## Trabalho anterior preservado
Já havia alterações em API/tab_operations, gateway de atendimento, globals.css,
TabLocationMove, teste attendance-tables-mobile e Spec 027, além de worktrees.
Não são autoria desta slice. Nenhuma alteração financeira/API foi feita por ela.
Não houve commit, push, merge, migration, escrita em banco remoto ou deploy.

## Validação e limites
Os testes usam navegador Chromium local e fixtures determinísticas; não comprovam
integração Django/PostgreSQL nem turno real. Larguras: 360, 390, 430 e 1280px.
Capturas em `apps/web/visual-artifacts/029/after/` (ignoradas pelo Git).
Referência YouTube inacessível; nenhum detalhe visual do vídeo foi inferido.

Build inicial, antes da implementação, passou. A captura de antes não foi concluída:
o sandbox bloqueou sockets locais. A execução posterior autorizada validou as
capturas de depois, sem substituir baselines existentes. Comparação visual direta
antes/depois permanece pendente; não há alegação de paridade com o vídeo/protótipo.

Lint dos componentes antigos: 2 erros `react-hooks/set-state-in-effect` e 2 warnings
no conjunto attendance-web/order-workspace. A execução do ESLint com o conteúdo de
HEAD por stdin confirmou os mesmos 2 erros e 2 warnings na base. Não foram
suprimidos nem incluídos em refatoração de recovery nesta tarefa.

Os resultados finais dos comandos ficam em [acceptance.md](acceptance.md).

## Próxima ação
Revisar o experimento visualmente com o responsável pelo produto, usando login e
ambiente próprios para testar `/attendance`. Não tratar fixtures como homologação.
Preservar o diff anterior ao separar commits. Revisão independente não executada;
decisão de release: NO-GO enquanto houver gates abertos. Nenhum deploy autorizado.

## Rebase e fluxo unificado — 2026-10-14

Rebase solicitado explicitamente pelo usuário para incorporar as novas diretrizes.
`git fetch origin` e `git rebase origin/main` concluídos: HEAD
`47043184408c090ddae33df17d4d72010603f764`. Branch preservada. Backup completo no
stash `058d69dbfcd10d307908899033a7f6cfbd3f583c`, mantido; worktrees excluídos do stash.
Conferência de 23 arquivos: nenhum ausente; somente globals.css, design system,
OrderWorkspace e ActionDialog tiveram combinação com main/ajustes posteriores.
Nenhuma operação de reset, force-push, descarte de trabalho ou commit foi feita.

Conflito em OrderWorkspace resolvido mantendo a seleção validada/serializada,
abertura de Tab nova com draft anterior preservado e as regiões do popup. A correção
de main sobre seleção contextual permanece coberta pela regressão de abertura com
draft em outra Tab. Nenhuma alteração de schema de storage/chave/payload de pedido.

Novos arquivos/alterações desta revisão: AttendanceCatalogCard, evolução controlada
de ActionDialog (open=false preserva montagem), AttendanceWeb unificada,
OrderWorkspace em sheet com regiões exclusivas, CSS/testes e docs da Spec029.
Skills novas lidas: rodada-ux-handoff, rodada-ux-critique e rodada-accessibility-review.
Diretrizes task-first incorporadas ao contrato do experimento.

Servidor Web local desta conversa atualizado em `http://localhost:3120/attendance`,
API existente preservada. Sem login automatizado nem escrita em dados reais para QA.
Gates atuais e limites: acceptance.md. Responsável pela próxima avaliação: produto/
operador humano no ambiente local, antes de eventual revisão independente e release.
