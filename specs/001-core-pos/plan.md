# Plan — Spec 001

## Slice 1 — Foundation

Venue, staff roles, catalog, products, `ProductAvailability` e seed de demo.

Separar desde o início ativação administrativa (`Product.active`) de disponibilidade operacional (`AVAILABLE | UNAVAILABLE`).

## Slice 2 — Tabs + Orders

Criar Tab anônima ou com `display_label`, criar Order, adicionar itens e snapshot de preço.

O modelo de Tab não deve exigir mesa/Customer e deve permanecer compatível com múltiplos identificadores futuros.

## Slice 3 — Ledger + Payments

Charges derivadas, payments manuais, exposure e fechamento.

## Slice 4 — Fulfillment + station controls

Estados/timestamps de OrderItem, tela operacional simples de Bar/Cozinha e controle de disponibilidade dos produtos da estação.

Toda confirmação de Order revalida disponibilidade no servidor; mudança posterior não altera OrderItem já confirmado.

## Slice 5 — Optional location context

Suporte opcional a ServicePoint/TableOccupancy sem acoplar ledger à mesa e com múltiplas Tabs no mesmo contexto físico.

## Slice 6 — CashShift + audit

Caixa básico, cancelamentos, ajustes e auditoria.
