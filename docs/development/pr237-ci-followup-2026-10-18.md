# PR237 — regressões de CI e estado de integração

2026-10-18. Base do ajuste: `dbf3d5fa067009cd9a255035a092f8c39c4507ac`. Escopo exclusivo do [PR237](https://github.com/procopio420/rodada/pull/237); PR247 não foi integrado.

## Diagnóstico e correção
O CI do SHA base teve4 falhas de API (994 casos aprovados) e7 falhas Web BFF (103 aprovados,3 skips). São fixtures de exceções pós-quitação e navegação de disponibilidade anterior ao popup.

- FourTrackShift: comprovar CLOSED após pagamento integral e fazer REOPEN gerencial/versionado/reautenticado antes de estorno.
- ReleaseConcurrency: somente um pagamento integral é gravado, segundo nega TAB_CLOSED; pedido concorrente nega limite ou Tab não aberta. Conferir CLOSED, saldo0 e ledger sem cobrança adicional.
- TabOperation HTTP: mudança após quitação usa REOPEN gerencial explícito, mantendo ocupações independentes.
- Web production-regions/workflows: Bar percorre abertura do seletor, Todos, item e Sim para indisponibilizar/reativar, com readback. Cozinha mantém controles existentes.
- Recovery Bar: comando aplica no servidor, resposta é perdida, outra seleção ocorre após fim de busy do modal; reload/replay reutiliza payload/recibo original. O cenário não mede ações simultâneas enquanto a resposta original permanece em voo.

Neste primeiro delta não houve alteração de código produtivo, CI, schema, autorização ou regra financeira. Aceites existentes Specs001/026 atualizados antes dos testes.

## Evidência do delta
- PostgreSQL de teste isolado:7 testes API PASS em190.639s (quatro falhas originais cobertas, mais adjacentes). System check PASS. Não executada novamente a suíte completa de998 neste ambiente.
- Build Web webpack PASS. Tentativa padrão Turbopack falhou no vínculo externo de dependências do checkout isolado; não foi mudada configuração de build.
- Integração Web PostgreSQL local: BLOCKED, start_api depende de fcntl indisponível neste runtime. Nenhuma substituição por SQLite/shim nem remoção do isolamento. CI do novo SHA é obrigatório.
- Suíte visual global executada novamente: FAIL em attendance-catalog.spec.ts:15, controle Contas obsoleto;592 não executados após parada na primeira falha, além de diagnóstico externo ao teste. Teste não foi removido ou relaxado.
- Gates locais de linhas adicionadas API/Web e diff check PASS.
- Revisão independente R3 `/root/review_pr237_ci`, delta8arquivos sobre dbf3d5fa, fingerprint988b89b36a0c7ab43e238969c10d9b9dd692ab43: NO_FINDINGS_WITH_GAPS após corrigir seletor de reativação. Revisor não executou testes; revisão cobre só este delta, não os83 arquivos anteriores, e não é aprovação GitHub.

## Decisão
NO-GO para merge nesta fotografia: suíte visual global falha, integração do delta aguarda CI e não há aprovação qualificada GitHub do PR237. A autorização de merge do solicitante não altera os gates. Sem main/deploy/banco remoto alterados. Próximo responsável: manutenção do teste de Atendimento e revisão qualificada do SHA final; revalidar toda a cadeia antes de merge. Artefatos locais ignorados: visual-artifacts/android-sync-runtime/pr237-*.log.


## Manutenção visual subsequente — base 4fe7d080
CI Linux deste SHA concluiu com sucesso: API run39166338613, Web run39166338624 e Android run39166338629. O workflow Web não executa o visual global neste PR; essa validação continua separada.

Correções de apresentação identificadas na regressão:
- Todos virtual restaurado no catálogo, distinto de categoria real homônima; busca, ativos e indisponibilidade preservados.
- Escape de ActionDialog não propaga cancelamento a diálogos ancestrais.
- Histórico aberto pela lista fecha o workspace ao retornar e restaura foco ao ícone; abertura interna mantém contexto.
- Seleção/quantidade da conferência de rodada usam touch-min, sem alterar payload/preço.

Os testes legados percorrem agora a área unificada, popups de categorias e superfícies Cardápio/Pedido atual/Conta. Mantêm payload imutável, replay, armazenamento, isolamento A/B, configurações e erros de seleção. A abertura disponível migrou para service/open-tab atômico; seguida de abertura em ocupação, ambas com resposta perdida e repetição da mesma intenção. O controle de covers removido não emite comandos; cobertura canônica permanece em integração/API. Auditoria de toque considera o modal focado e preserva auditoria da tela quando ativa e Axe.

Build webpack e typecheck PASS. ESLint dos testes/componentes focados PASS; execução completa dos arquivos alterados encontra dívida anterior de setState em effect em attendance-web.tsx:50 e dependências do mesmo effect. Nenhuma supressão adicionada.

Revisão independente do delta, fingerprint1f1dc1061947e58f523c1e547e2acfd76a4e3081: NO_FINDINGS_WITH_GAPS após restaurar cobertura de mesa DIRTY; inclui revisão dos controles produtivos, payload/replay e helper de auditoria. Não representa aprovação GitHub ou execução do revisor.

Suíte visual global em execução; não há PASS global nesta fotografia. Nenhuma mudança de CI, baseline, tolerância, API, schema ou ledger. Aprovação qualificada GitHub ainda ausente.
