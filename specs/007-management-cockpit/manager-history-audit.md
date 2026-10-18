# Auditoria de comandas do atendimento na Gerência

Data: 2026-10-18. Branch `codex/management-navigation`; HEAD/base `dbf3d5fa067009cd9a255035a092f8c39c4507ac` com delta local não commitado. Preserva os recortes anteriores de navegação/cardápio e alterações alheias. R3 por projeção financeira; não houve alteração de API, ledger, schema ou permissões.

## Achado e correção

O resumo gerencial usava a primeira página de `/tabs/`, incluindo encerradas, e só depois filtrava abertas no cliente. Regressão reproduzida com250 encerradas e205 abertas: mostrava0. Corrigido para consultar `active=true`, percorrer todas as páginas, deduplicar IDs e rejeitar offsets não inteiros/regressivos. Somente após leitura completa publica contagem/exposição; erro em página intermediária mantém falha explícita, sem subtotal apresentado como total.

Alteração de produto limitada a `apps/web/app/manage/page.tsx` (getOpenTabs e chamada). Testes novos/estendidos: `apps/api/tests/test_manager_tab_lifecycle.py`, `apps/web/tests/visual/management-navigation.spec.ts`, `management-tab-history.spec.ts`. Contratos: Spec001 quitação, Spec007 A1/histórico e Spec017 correções; sem nova ADR.

## Cenários verificados

| Cenário | Resultado canônico conferido pela gerência |
| --- | --- |
| Atendimento abre e confirma pedido | Tab ativa, saldo e itens corretos, autoria do atendimento |
| Recebimento parcial autorizado | Continua aberta, somente saldo remanescente; relatório recebe valor confirmado |
| Quitação confirmada e retry | CLOSED, closed_at, sai de ativas, entra no histórico; total/recebimentos preservados; sem duplicar pagamento/fechamento |
| Pagamento pendente | Continua aberta; não conta como recebido nem entra no histórico encerrado |
| Cancelamento de comanda vazia pelo autor | CANCELLED, auditável, sai de ativas; histórico sem pagamento; replay único |
| Cancelar comanda com consumo diretamente | Rejeitado, não desaparece das abertas |
| Cancelar todos os itens e encerrar Tab | CLOSED com itens CANCELLED preservados; total líquidozero, sem Payment/receita recebida inventados |
| Sem capacidade para receber |403, mantém aberta/saldo; nenhum Payment |
| Gerente de outro Venue |404 no detalhe, histórico sem dados estrangeiros |
| Virada do dia/cutoff e201 encerradas | Período e paginação respeitados pelos testes existentes de histórico |

Sessões de teste distintas: atendimento com plataforma ANDROID e capacidade de recebimento explicitamente concedida; gerente com plataforma WEB. PINs dos novos testes gerados em runtime, sem impressão. A plataforma da sessão não é execução física do app: endpoints Android correspondentes foram conferidos no código, mas não foi executada nova jornada de toque Android durante esta auditoria.

## Evidência executada

- PostgreSQL descartável `test_rodada_history_audit`:32 testes PASS em35.176s (6 novos de ciclo entre papéis,3 histórico,23 ledger/pagamentos). Dados/sessões da demo não alterados.
- Playwright focado:30 PASS em37.6s (14 navegação/contagem/falhas,16 histórico/extrato). Regressão nova comprovou FAIL antes da correção: esperado205, recebido0.
- Negativas Web: erro500/401 na segunda página e offset inválido não publicam contagem ou exposição parcial. Cancelada conserva itens e não recebe selo Paga.
- Build/typecheck PASS; autenticação Node4 PASS; Ruff do teste novo PASS. ESLint completo21 diagnósticos legados/0 novos ou fatais no delta; Web safety0; diff check PASS.
- Suite visual global executada com parada na primeira falha:1 FAIL em `attendance-catalog.spec.ts:15` (seletor legado Contas),619 não executados. Não é aprovação global; nenhuma baseline/tolerância foi alterada.
- Revisão independente do código e negativas: NO_FINDINGS_WITH_GAPS, sem achados reproduzíveis; revisor não reexecutou testes e não aprovou GitHub.
- Consulta local real, somente leitura: resumo aberto e popup histórico consultados; conferidos itens, recebimentos e selo de uma comanda quitada. A data padrão não exibia o dia anterior; selecionar o dia operacional correspondente mostrou os registros. Dados reais não copiados para fixtures/evidência.

## Limites e próximo responsável

Paginação por offset não congela aberturas/fechamentos concorrentes: dados podem mudar entre páginas e requerem revalidação. O load completo mantém limitação preexistente de geração/revogação, registrada pela revisão; não houve expansão desse fluxo. API é a autoridade, realtime apenas invalida/revalida leituras. Sem nova medição de latência de propagação ou aceite de operador, aparelho físico, provider real ou produção.

Implementado e validado localmente no recorte; NO-GO para afirmar aceite global/deploy. Próximo responsável: mantenedor para revisão/PR e manutenção do teste visual adjacente; operador para aceite real Android→Gerência. Sem commit/push/merge/deploy autorizado neste recorte e sem alteração do checkpoint preexistente.
