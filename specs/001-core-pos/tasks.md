# Tasks — Spec 001

## API/Domain

- [ ] Venue / StaffMember / permissions
- [ ] Product / catalog
- [ ] Zone / ServicePoint mínimo
- [ ] Tab com `display_label` opcional e sem dependência de mesa/Customer
- [ ] associação opcional Tab ↔ TableOccupancy preparada para Spec 004
- [ ] garantir várias Tabs por TableOccupancy
- [ ] Order / OrderItem sempre ligados a Tab
- [ ] `Order.source` preparado para `STAFF | CASHIER | GUEST`
- [ ] Charge / Payment / Adjustment
- [ ] CashShift
- [ ] AuditEvent
- [ ] exposure service
- [ ] cancellation/reversal service
- [ ] tab close rules sem side effect de liberar mesa

## Web

- [ ] tela de tabs abertas
- [ ] abrir tab anônima ou por nome/apelido
- [ ] catálogo rápido
- [ ] lançar pedido
- [ ] tela da tab
- [ ] receber pagamento
- [ ] fechar tab
- [ ] tela simples Bar/Cozinha
- [ ] caixa básico

## Quality

- [ ] tests Tab sem mesa
- [ ] tests duas Tabs independentes no mesmo TableOccupancy
- [ ] tests fechar Tab não encerra TableOccupancy
- [ ] tests snapshot de preço
- [ ] tests charge idempotente
- [ ] tests cancelamento/reversal
- [ ] tests fechamento
- [ ] tests cash summary
- [ ] seed demo
