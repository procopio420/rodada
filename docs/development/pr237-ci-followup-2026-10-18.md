# PR237 — correções e validação de integração

2026-10-18. Escopo exclusivo do [PR237](https://github.com/procopio420/rodada/pull/237); PR247 não integrado. Bases dos ajustes: dbf3d5fa, 4fe7d080 e d5522df1. O SHA final está no PR e no histórico Git deste documento.

## Correções
- API: regressões pós-quitação comprovam CLOSED e usam REOPEN gerencial/versionado/reautenticado antes de estorno ou mudança. Corridas preservam saldo zero e ausência de cobrança duplicada.
- Integração do Bar: categorias/Todos → item → confirmação, com recibo/readback e recuperação da mesma intenção. O cenário de resposta perdida libera a resposta antes de escolher outro produto; não mede seleção simultânea durante busy.
- Web: Todos virtual restaurado, distinto da categoria real homônima. Busca, ativos e indisponibilidade preservados.
- ActionDialog: Escape fecha só a camada superior; pendência continua bloqueando fechamento. Histórico externo retorna à lista e restaura foco; interno preserva contexto.
- Conferência de rodada e seletores de rota de impressão usam touch-min existente. Impressão não muda comandos, pareamento, confirmação física ou garantias de papel.
- Testes percorrem os popups e a área unificada, mantendo payload imutável, replay, armazenamento, configurações e isolamento A/B. Mesa livre usa abertura atômica; ocupada usa abertura na ocupação, ambas com resposta perdida e replay idêntico.
- Teste do limite de 99 agrupa duas linhas históricas 99+1, sem misturar o rascunho manual à rodada enviada diretamente (Spec026 T08e).
- Auditoria de toque considera o modal focado, mantendo auditoria integral da tela quando ativa e Axe. Controle de covers removido não emite comandos; cobertura canônica permanece em integração/API.

Nenhuma mudança de CI, baseline/tolerância visual, schema, autorização ou ledger neste follow-up. Specs001/026/029 e aceite visual028 acompanham o escopo.

## Evidências executadas
| Gate | Resultado e limite |
| --- | --- |
| API local PostgreSQL isolado | 7 PASS em190.639s; não usa a base de demonstração |
| CI 4fe7d080 | API run39166338613, Web run39166338624 e Android run39166338629: PASS |
| CI d5522df1 | Android PASS; API/Web ainda em execução na última consulta. Novos checks exigidos no SHA final |
| Build Web final | webpack PASS; typecheck PASS |
| ESLint focado | PASS nos componentes/testes novos; auditoria completa dos alterados encontra dívida anterior em attendance-web.tsx:50 (setState em effect e dependências), sem supressão |
| Visual global | 595 executados:586 PASS e9 FAIL de regressões legadas; nenhuma interrupção por max-failures |
| Reexecuções corrigidas | guest-quantity:1 PASS; tab-search + table-service:16 PASS; printing + repeat-order + attendance-dialogs:28 PASS após rebuild. Todos os9 casos que falharam estão cobertos por estas reexecuções |
| Segurança de fonte | gate Web d5522df1:419 linhas adicionadas, zero achados; diff check PASS |

A evidência visual é uma execução global seguida de reexecuções focadas das falhas corrigidas; não se afirma uma segunda execução global limpa. Artefatos ignorados em visual-artifacts/android-sync-runtime/pr237-*.log. Reexecuções concorrentes usaram portas/output separados.

Integração Web PostgreSQL local permanece bloqueada por fcntl indisponível neste runtime; nenhuma troca por SQLite/shim ou remoção do isolamento. CI Linux é a evidência dessa integração. Turbopack não aceita o vínculo externo de dependências deste checkout; build usa webpack, sem mudar configuração do produto.

## Revisão e decisão
Revisão independente do primeiro delta de CI: fingerprint988b89b36a0c7ab43e238969c10d9b9dd692ab43, NO_FINDINGS_WITH_GAPS. Revisões dos deltas visuais, incluindo fingerprint1f1dc1061947e58f523c1e547e2acfd76a4e3081 e complementos de impressão/busca/recovery/limite99, sem achados reproduzíveis após correções. Revisores não executaram testes; conclusões limitadas aos deltas, sem aprovação GitHub de todo o PR.

NO-GO para merge até checks do SHA final e aprovação qualificada GitHub. REVIEW_BLOCKED: revisão automática R3 anterior recusou escopo superior a35 arquivos; requer outro revisor qualificado para o PR completo. A autorização do solicitante para merge não substitui esse gate. Provedor real, perda real de resposta em dispositivo, TalkBack, aparelho físico, impressão física e homologação operacional não verificados. Sem main, deploy, Play ou banco remoto alterados. Próximo responsável: revisão qualificada e conferência dos checks finais.
