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
