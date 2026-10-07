# Arquitetura Inicial

## Decisão

Começar como **modular monolith** com fronteiras claras de domínio.

```text
Next.js / PWA
      |
      v
Django + DRF
      |
      +-- Catalog
      +-- POS / Tabs / Orders
      +-- Fulfillment
      +-- Dispatch
      +-- Customers / Relationships
      +-- Ledger / Payments
      +-- Cash / Shifts
      +-- Audit
      |
  PostgreSQL
      |
 Redis / WebSocket (dispatch/realtime)
```

## Módulos

### catalog
Produtos, preços, disponibilidade e routing operacional (`BAR`, `KITCHEN`, etc.).

### pos
Tabs, orders, order items, charges e fechamento.

### fulfillment
Estados operacionais de itens/pedidos: `NEW`, `ACCEPTED`, `PREPARING`, `READY`, `PICKED_UP`, `DELIVERED`, `CANCELLED`.

### dispatch
Zones, service points, tasks, claims, prioridades e delivery runs.

### customers
Identidade local e busca rápida.

### relationships
Status de relacionamento e políticas do venue.

### ledger
Charges, payments, adjustments, exposure e invariantes financeiras.

### payments
Adapters de PSP, intents/records, idempotência e webhooks.

### cash
Turnos/caixa e reconciliação básica do PDV.

### audit
Registro imutável das mutations relevantes.

## Realtime

Dispatch e fulfillment são naturalmente realtime. Entram com Redis/WebSocket quando `specs/003-dispatch` for implementada.

O sistema deve continuar consistente mesmo se o socket cair; WebSocket é canal de atualização, PostgreSQL é fonte de verdade.

O canal operacional usa Django Channels. Em produção, `REDIS_URL` configura o
channel layer Redis; desenvolvimento local usa o layer em memória. Após reconnect,
o cliente refaz o snapshot HTTP e pode recuperar eventos incrementais em
`GET /api/dispatch/events/?after=<id>`.

## Payments

O domínio não depende diretamente de um PSP.

```text
PaymentProvider
  create_pix(...)
  authorize_card(...)
  capture(...)
  refund(...)
  get_status(...)
```

Nem todo provider implementa todas as operações.

## Monetário

- centavos, nunca float;
- ledger append-oriented;
- mudanças de exposure dentro de transação;
- idempotency key em comandos externos e webhooks.

## Integrações futuras

- Pix/adquirente;
- WhatsApp;
- NFC/tag;
- impressão;
- fiscal;
- delivery;
- estoque.
