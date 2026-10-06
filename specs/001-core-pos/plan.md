# Plan — Spec 001

## Slice 1 — Foundation

Venue, staff roles, catalog, products e seed de demo.

## Slice 2 — Tabs + Orders

Criar Tab anônima ou com `display_label`, criar Order, adicionar itens e snapshot de preço.

O modelo de Tab não deve exigir mesa/Customer e deve permanecer compatível com múltiplos identificadores futuros.

## Slice 3 — Ledger + Payments

Charges derivadas, payments manuais, exposure e fechamento.

## Slice 4 — Fulfillment states

Estados/timestamps de OrderItem e tela operacional simples.

## Slice 5 — Optional location context

Suporte opcional a ServicePoint/TableOccupancy sem acoplar ledger à mesa e com múltiplas Tabs no mesmo contexto físico.

## Slice 6 — CashShift + audit

Caixa básico, cancelamentos, ajustes e auditoria.
