# E04 — Tarefas executáveis

**Módulos de referência:** apps/web/components/bill-summary.tsx, order-workspace.tsx, apps/attendance-android, Django ordering/payments/cash/hospitality; Spec 001/004/006/012/014/017.

- [ ] **E04-01 Baseline financeiro:** inventariar endpoints de Bill, Payment CASH/externo, close, occupy/release/clean, flags e capabilities. Mapear estados de PSP não homologados e casos já cobertos.
- [ ] **E04-02 Conta real:** reorganizar UI sobre BillSummary canônico em Web e Compose. Recibos/status e saldo sempre obtidos do servidor; sem draft no total. Rascunho pendente contextualizado sem etapa inventada.
- [ ] **E04-03 Partial:** integrar UI compacta de recebimento e readback com mesma idempotency key; manter Tab OPEN e repetir operação apenas por replay seguro, nunca nova cobrança no timeout.
- [ ] **E04-04 Full+close:** avaliar viabilidade transacional do atalho. Se duas mutations, modelar recoverable sequence Payment CONFIRMED → Tab.close → Tab CLOSED, com erro intermediário explícito, sem dupla confirmação de pagamento.
- [ ] **E04-05 Close zero:** botão direto seguro com reauth/capability quando necessário; callback readback e preservação de motivos independentes REQUIRES_ACTION.
- [ ] **E04-06 Mesa:** multi-Tab/occupancy, liberar com grupo fora, geração/revogação de guest, DIRTY/CLEANING/AVAILABLE; não ligar diretamente close→release.
- [ ] **E04-07 Timeouts e concorrência:** Payment pending/refund, overpayment, dois funcionários, versões stale, QR Guest antigo e Tab movida; bloquear apenas conforme API.
- [ ] **E04-08 E2E:** Web/Android/Back PostgreSQL, caixa e provedor simulado apenas em sandbox autorizado; campos de erro/confirmação com logs de ID.
- [ ] **E04-09 Gate:** AC-12..16 PASS, revisão independente R3 financeira, nenhum débito/recebimento duplicado. Não ativar cartão Tap to Pay sem homologação.

**PRs sugeridas:** E04-a UI Bill/readback, E04-b pagamento/close recovery, E04-c ocupação e limpeza native/Web.

## Evidência incremental — 2026-10-17 (não equivale a aceite)

| Subtarefa | Estado verificável | Evidência / gate restante |
|---|---|---|
| E04-03 Partial | Web implementado e teste real executado | PR225;500+1500 em CASH, ledger2000, duas Payments. Compose/paridade e R3 final pendentes. |
| E04-04 Full+close | Sequência recuperável implementada | PR225; PaymentACK perdido, Close503/ACK perdido, reload/readback, sem cobrança extra. Revisão independente encontrou bloqueio concorrente, corrigido; rereview pendente. |
| E04-06 Mesa | Web exige início e fim reais de limpeza | commit813bcda3; teste PG PASS com autoria e released_at<=cleaning_started_at<=ready_at. Release/Guest e Compose ainda requerem jornada conjunta. |
| E04-07 Timeouts | Cobertura parcial real | Capability negada, replay e consumo concorrente passam em PostgreSQL; não comprova todos os cenários dessa tarefa. |
| E04-08/09 | Em andamento | PRs224/225 draft; nenhum gate de piloto ou aceite integral. |

IDs desta tabela são os detalhados deste épico; a checklist agregada possui outra
granularidade. Nenhuma caixa foi marcada com base apenas em código.
