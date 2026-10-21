# S5 — revisão conjunta, rodada de inspeção

2026-10-20. Branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`; working tree local acumulado, sem commit/push/merge/deploy. Nenhum código de produto alterado nesta rodada.

## Escopo

Composição das cinco abas e subpáginas da Spec034: navegação, aliases/retorno/histórico, layout/axe, estados e regressões interceptadas. Reexecução dos arquivos management*.spec.ts em uma composição, build/tipos/auth/tenant e inventário de lint/evidências. Revisão independente local de S4 e navegação.

## Evidência já concluída

- Build webpack/typecheck PASS; auth4 PASS e tenant10 PASS.
-320 imagens históricas verificadas pelos manifests SHA256SUMS:0 divergências. Não comparar fontes históricas ao working tree posterior como se fossem a mesma revisão.
- Lint focado14arquivos:FAIL com7erros set-state-in-effect, já registrados nas slices, em pricing/printing/setup/refunds/catalog-customization/house-account. Lista sanitizada em docs/development/evidence/spec034-review/lint-findings.json. Não suprimidos.
- Seleção inicial de testes com regex management atingiu o nome do worktree e selecionou874casos. Interrompida após4falhas de attendance-catalog já observadas anteriormente, fora do recorte. Não é execução completa nem prova causal. Reiniciada com39nomes explícitos de arquivos:245casos da Gerência.

## Revisão independente local

Reviewer `/root/review_team_ux`, somente leitura, sem autoria. NO_FINDINGS_WITH_GAPS: diffs reais de S4a–e preservam handlers, centavos, versões, payloads, flags e disabled. Retorno à aba usa mesmo href; managementLayout tem defaultfalse e único opt-in no editor, ProductionBoard mantém JSX/classes anteriores. Inspecionados pixels de produtos390, grupo390, opção360zoom e disponibilidade390. Reviewer não executou testes: resultados executados são do autor.

Lacunas: restauração de foco em retorno de produtos/customização não está explicitamente testada; inputs de linha única truncam na ampliação; zoom nativo/leitor de tela/operador não verificados; sucesso real/concorrrência/replay/duas Venues/revogação não demonstrados pelas fixtures. Nenhuma aprovação autenticada GitHub: gateR3 REVIEW_BLOCKED, sem recomendação de merge/deploy.

## Próxima rodada de fechamento

Conferir lacuna de foco com reprodução, corrigir somente achados confirmados; sincronizar checklist/aceite com evidências atuais e separar PASS local de FAIL/NOT_RUN. Manter falhas herdadas explícitas, sem abrir novos redesenhos. Aceite operacional e integração real dependem dos gates externos.

Capturas da composição atual:20PNG (cinco abas × quatro larguras) e manifest de fontes em docs/development/evidence/spec034-review. Inspecionados pixels das cinco abas390. Sem mudanças de produto durante a revisão.


## Resultado composto e correção do teste

39arquivos/245casos:244 PASS e1 FAIL em7,1min. A única falha foi management-tab-history.spec.ts:151, que esperava a frase antiga de sessão encerrada. As verificações de fechamento do diálogo e remoção do gatilho do histórico já passaram. Corrigida somente a expectativa para heading Sessão encerrada e link Entrar novamente com href/staff dentro do alerta; assertivas de limpeza preservadas. Código de produto inalterado. Não declarar que245 passaram na mesma execução.

Rerun history+session-login:21 PASS23,6s, incluindo o caso anteriormente falho; ESLint do teste PASS. Revisão independente confirmou que o ajuste preserva401, histórico com pagamento visível, diálogo0 e gatilho0, acrescentando destino/staff. Hash do teste:9DAF1F171C2D74E96B7880BAE751641A1537ECDC4360D64694AF9A926A33C535. Não repetida toda a suíte após alteração restrita ao teste. Nenhuma falha nova de produto confirmada nesta rodada; lacunas manuais/globais seguem abertas.
