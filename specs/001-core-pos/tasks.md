# Tasks — Spec 001

## API/Domain

- [x] Venue / StaffMember / permissions
- [x] Product / catalog
- [x] ProductAvailability separado de `Product.active`
- [ ] availability mutation com auditoria + permissão por estação/manager
- [x] availability query compartilhada por todos os canais
- [x] validação transacional de disponibilidade no confirm Order
- [ ] Zone / ServicePoint mínimo
- [x] Tab com `display_label` opcional e sem dependência de mesa/Customer
- [ ] associação opcional Tab ↔ TableOccupancy preparada para Spec 004
- [ ] garantir várias Tabs por TableOccupancy
- [x] Order / OrderItem sempre ligados a Tab
- [x] `Order.source` preparado para `STAFF | CASHIER | GUEST`
- [ ] Charge / Payment / Adjustment
- [ ] CashShift
- [x] AuditEvent
- [x] exposure service
- [ ] cancellation/reversal service
- [ ] tab close rules sem side effect de liberar mesa

## Web

- [ ] tela de tabs abertas
- [ ] abrir tab anônima ou por nome/apelido
- [ ] catálogo rápido
- [x] lançar pedido
- [x] tela da tab
- [x] receber pagamento
- [x] fechar tab
- [x] tela simples Bar/Cozinha
- [x] ação rápida `Disponível / Indisponível` por produto na estação
- [x] catálogo mostra estado indisponível sem permitir confirmação
- [ ] caixa básico

## Quality

- [x] tests Tab sem mesa
- [ ] tests duas Tabs independentes no mesmo TableOccupancy
- [ ] tests fechar Tab não encerra TableOccupancy
- [x] tests snapshot de preço
- [x] tests separar `active` de disponibilidade operacional
- [x] tests indisponível bloqueia STAFF/CASHIER/GUEST na confirmação
- [x] tests carrinho stale / corrida de disponibilidade
- [x] tests mudança não altera OrderItem confirmado
- [ ] tests permissão + audit de disponibilidade
- [x] tests charge idempotente
- [ ] tests cancelamento/reversal
- [x] tests fechamento
- [ ] tests cash summary
- [x] seed demo
