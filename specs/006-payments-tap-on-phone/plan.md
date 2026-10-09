# Plan — Spec 006

## Slice 1 — Payment domain + ledger

Expandir Payment, métodos/estados, PaymentAttempt, Refund e cálculo de saldo derivado.

Garantir que Tab continua separada de Table/TableOccupancy.

## Slice 2 — Staff payment flow

Adicionar ação **Pagar** na Tab com:
- saldo total;
- valor parcial;
- valor custom;
- seleção de método;
- confirmação de dinheiro e terminal externo.

## Slice 3 — Provider port + idempotency

Criar porta `PaymentProvider`, idempotency keys, normalização de erros e capabilities.

Implementar primeiro adapter real sem vazar conceitos do provider para o domínio.

## Slice 4 — Rodada Atendimento Android + Paytime Tap on Phone

Criar/usar a superfície **Rodada Atendimento** como app Android nativo em Kotlin + Jetpack Compose para o fluxo operacional do staff.

Implementar `PaytimeTapProvider` como primeiro adapter real de Tap on Phone, integrando o SDK diretamente ao app, sem handoff para aplicativo externo.

Fluxo deve usar amount/Tab já calculados pelo backend e tratar timeout/ambiguidade como `CONFIRMATION_PENDING`.

A porta permanece provider-neutral para permitir adapters adicionais por Venue no futuro.

## Slice 5 — Pix + webhooks

Adicionar criação de cobrança Pix, inbox idempotente de webhooks e confirmação server-side.

## Slice 6 — Guest payment + realtime

Permitir pagamento da mesma Tab via GuestSession autorizada e propagar confirmação para Staff/Cashier.

## Slice 7 — Refund + permissions

Adicionar estorno total/parcial, RBAC e trilha de auditoria.

## Slice 8 — Reconciliation + observability

Jobs/commands de reconciliação para operações pendentes, métricas de aprovação, latência, falha e tempo até pagamento.

## Slice 9 — UX avançada

Divisão por itens/pessoa e gorjeta, mantendo o ledger monetário como fonte de verdade.

## Live slice

Implement Paytime REST Pix adapter and venue-scoped configuration, protected create,
status/reconciliation and webhook routes. Harden concurrent inbox deduplication and
terminal transitions. Persist QR evidence using existing attempt metadata. Test
provider contracts with injected HTTP transport and API workflows separately from
live activation. Extend native Tap port and canonical payment presentation; run
backend financial gates and Android tests/build/lint. Document unverified provider
activation gates explicitly.

## SumUp slice

Reuse payment orchestration; add exact-decimal SumUp Checkout and Tap verification
adapters, persistent deterministic simulator, merchant credentials and authorization
models, refund request/reconciliation, Android SumUp boundary/event states and debug
simulator UI. Add provider contract/tenant/refund/PostgreSQL race tests and onboarding
matrix/checklist. PR depends on the existing Paytime PR until it is merged.

## Provider readiness — 2026-10-09

Reuse merchant OAuth, PaymentAttempt metadata and canonical settlement. Add a narrowly scoped signed HttpOnly callback cookie, validate current staff authorization, retain sanitized Pix artifacts, and isolate reconciliation failures. Private SDK and employee delegation remain activation gates.
