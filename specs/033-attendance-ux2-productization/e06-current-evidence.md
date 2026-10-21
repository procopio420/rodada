# E06-01 — matriz por evidências, 20/10/2026

Baseline inspecionada: `b824d2e270253988bc5d4f1d8a2966f19ba99f24`.
Issue [272](https://github.com/procopio420/rodada/issues/272).
PR230 fechada/substituída; PR271 integrada em `e26694df`; nenhuma PR aberta na consulta.
Este registro complementa, sem apagar, baseline/parity históricos. Checkbox aberta
não demonstra ausência de código. Nenhum AC global foi fechado nesta auditoria.

## Evidência executada e limites

- [Web CI 39484200340](https://github.com/procopio420/rodada/actions/runs/39484200340),
  HEAD exato acima, job118848975189: **159 PASS / 3 SKIP**, PostgreSQL17, Django,
  BFF e Chromium, 16,5min de integração. Logs consultados; typecheck/build,
  auth/tenant/identity/gateway também passaram. Visual completo, menu canônico
  opt-in e gate responsive027 foram **SKIPPED** nesta execução.
- Android/API não foram executados novamente neste HEAD pela simples alteração
  Web. Evidências anteriores e código presente são reuso; não transferir PASS
  para este SHA. Revisor automatizado `ChatGPT R3 reviewer` está SKIPPED:
  isto **não** é aprovação independente autenticada.
- Rehearsal novo: `apps/api/tests/test_spec033_integrated_rehearsal.py`.
  É composição API/DB, não ensaio de rede, Compose, dispositivo ou PSP.
  A guard de PostgreSQL faz SKIP em SQLite deliberadamente. Resultado pendente
  até execução no candidato; não contabilizar sua existência como PASS.

## AC-01..24

Paths Web abaixo relativos a `apps/web/`; API a `apps/api/`; Android a
`apps/attendance-android/app/src/`. As categorias descrevem o **AC inteiro**;
subcenários aprovados não aceitam automaticamente a paridade Web/Android.

| AC | Classificação | Código e teste verificável | Evidência / delta real |
| --- | --- | --- | --- |
| 01 | Implementado, evidência insuficiente | API `modules/dispatch/targets.py`, `tests/test_dispatch_targets.py`; Web `components/attendance-task-context.tsx`, `tests/integration/ux2-now.spec.ts`; Android `StaffTaskTargetTest.kt` | Web CI baseline; repetir composição nativa e origem QR no mesmo ensaio |
| 02 | Implementado, evidência insuficiente | Web `components/attendance-ux2-workspace.tsx`, `tests/integration/ux2-now.spec.ts`; Android `TabDraftContextsTest.kt`, `AttendanceNavigationTest.kt` | Web baseline; Back/foco/drafts em Compose e fontes ampliadas pendentes |
| 03 | Implementado, evidência insuficiente | API `tests/test_dispatch_targets.py`; Web `tests/integration/attendance-queue-acceptance.spec.ts`; Android `LiveServiceRequestSessionFenceTest.kt` | Revogação/fallback Web cobertos; execução nativa corrente não comprovada |
| 04 | Implementado, evidência insuficiente | Web `components/attendance-order-status.tsx`, `tests/integration/attendance-ux2-workspace.spec.ts`, `attendance-order-status.spec.ts`; Android `OrderSubmissionStatusTest.kt` | Web baseline; confirmar matriz Compose/estação no SHA integrado |
| 05 | Implementado, evidência insuficiente | Web `lib/client/order-intent.ts`, `tests/integration/attendance-ux2-workspace.spec.ts`; Android `IntegratedIntentRecoveryTest.kt`, `LivePostDropReconciliationTest.kt` | Web commit+ACK perdido/reload verde; restart físico não comprovado |
| 06 | Implementado, evidência insuficiente | Web `tests/integration/attendance-ux2-workspace.spec.ts`, `tests/visual/attendance-ux2-workspace.spec.ts`; Android `RepeatOrderTest.kt` | PR271 corrige repetir; revalidação completa Android e modificadores pendente |
| 07 | Implementado, evidência insuficiente | API `tests/test_ordering_foundation.py`, `test_order_intent_concurrency.py`; Web `lib/client/order-intent.ts`; Android `OrderRecoveryPolicyTest.kt` | Reexecutar concorrência PG e erro definitivo nas duas superfícies |
| 08 | Parcialmente implementado | Web `tests/integration/attendance-delivery-freshness.spec.ts`, `tests/visual/attendance-ux2-workspace.spec.ts`; Android `StaffTaskReadTest.kt`; `web-peak-dispatch.md` | Fila independente Web CI; 50 tarefas/fontes/pico e tempo de interação corrente sem prova conjunta |
| 09 | Implementado, evidência insuficiente | Web `tests/integration/ux2-now.spec.ts`; API `tests/test_dispatch_targets.py` | Web navegação sem claim/complete verde; repetir Android |
| 10 | Implementado, evidência insuficiente | Web `components/attendance-delivery-page.tsx`, `tests/integration/attendance-delivery-page.spec.ts`; Android `DeliveryPageTest.kt` | Web quatro larguras/lost ACK; provenance nativa e toque físico pendentes |
| 11 | Implementado, evidência insuficiente | API `tests/test_service_requests_round2.py`, `test_dispatch_targets.py`; Web `attendance-queue-acceptance.spec.ts`; Android `LiveDeliveryRecoveryTest.kt` | Web baseline; concorrência PG e sessão nativa no candidato pendentes |
| 12 | Implementado, evidência insuficiente | Web `tests/integration/attendance-settlement-recovery.spec.ts`; API `tests/test_ledger_payments.py`; Android `ReceiptSettlementTest.kt` | Web parciais/ledger/draft verde; paridade nativa no HEAD pendente |
| 13 | Implementado, evidência insuficiente | Web `attendance-settlement-recovery.spec.ts`, `attendance-zero-close.spec.ts`; Android `FinancialResponseFenceTest.kt` | Web baseline readback/um pagamento/zero-close; rede e operador físicos pendentes |
| 14 | Implementado, evidência insuficiente | API `tests/test_hospitality_tables.py`; Web `tests/integration/attendance.spec.ts`; novo `test_spec033_integrated_rehearsal.py` | Novo ensaio compõe três Tabs e última CLOSED sem release; execução pendente |
| 15 | Implementado, evidência insuficiente | API `tests/test_table_release_context.py`; Web `tests/integration/attendance-release-occupancy.spec.ts`, `attendance-ux2-workspace.spec.ts`; Android `LiveTableReleaseFenceTest.kt` | Web ciclo e corrida A→B verde; composição completa PG/epoch nativa pendente |
| 16 | Implementado, evidência insuficiente | API `tests/test_ledger_payments.py`, `test_payments_concurrency.py`; Web `attendance.spec.ts`, `attendance-settlement-recovery.spec.ts` | Web rejeição de pagamento não autorizado; regressão financeira PG e PSP externo não equivalentes |
| 17 | Parcialmente implementado | Web `components/attendance-credit-bar.tsx`, `tests/visual/attendance-credit-bar.spec.ts`; Android `parity.md` (capturas da barra); `parity.md` | Barra existe; limites/fronteiras/fontes e modo efetivo dependem também031 |
| 18 | Não implementado no escopo WARN_ONLY | Spec031/PR215, preservação ENFORCE em API/Web/Android | Não habilitar WARN_ONLY pelo cliente. Integração031 e seus gates próprios ainda necessários |
| 19 | Implementado, evidência insuficiente | Web `components/attendance-credit-bar.tsx`; API `modules/ordering/views.py`; `parity.md` | Sem garantia financeira fictícia; snapshots/atualização gerencial exigem execução auditável |
| 20 | Parcialmente implementado | Web CI159; suites API/Compose; novo rehearsal | Falta um pacote de evidência comum por SHA, IDs e superfícies; novo teste é backend apenas |
| 21 | Parcialmente implementado | Web recovery CI; Android `LivePostDropReconciliationTest.kt`, `LiveDeliveryRecoveryTest.kt` | Parte automatizada existe; app morto/troca/revogação em aparelho real continuam gate |
| 22 | Dependente de homologação externa | `parity.md`, `evidence/`, testes visuais/Compose existentes | Capturas históricas parciais; aparelho S24-class/TalkBack/toque e matriz completa corrente não executados |
| 23 | Parcialmente implementado | API `tests/test_table_turnover_metrics.py`; `epics/E06-integration-and-release/spec.md` | Timestamps/relatórios canônicos existem. Comparativo medido antes/depois, passos e latências de intenção ainda sem ensaio/dados; não estimar |
| 24 | Dependente de homologação externa | `docs/agents/CODE-REVIEW.md`, `docs/ci-workflows.md`; issue272 | CI Web verde não cobre flags Venue/role, rollback ensaiado, R3 autenticado e aceite humano/piloto |

## Ordem de execução

1. Executar novo rehearsal PostgreSQL: três Tabs homônimas, Bar/Cozinha,
   replay Order/Payment, parciais, fechamento independente, saída explícita,
   Guest revogado e nova geração; registrar resultado por SHA.
2. Corrigir qualquer regressão encontrada, reexecutar suítes API/Web aplicáveis.
3. Revalidar Compose/recovery no mesmo candidato; visuais e pico em recorte próprio.
4. Instrumentação/comparativo e flag/rollback têm contrato E06, mas precisam de
   implementação/ensaio específico; não confundir relatório de giro com todos os
   eventos de fricção. Físico, operador, TalkBack e piloto não serão simulados.
5. Spec028: S3 já contém runtime, transportes e API (`agent_delivery.py`), apesar
   do tracking aberto. Conferir CI e regressões antes de expandir para S4–S7.

**Decisão: NO-GO global.** E06-01 é inventário, não aceite de produto/release.
