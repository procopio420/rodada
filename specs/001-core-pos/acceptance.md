# Acceptance — Spec 001

- [x] Staff abre uma Tab sem selecionar mesa ou Customer.
- [x] Staff pode abrir uma Tab com nome/apelido simples.
- [ ] Staff pode opcionalmente associar/mover a Tab entre contextos físicos.
- [ ] Duas Tabs podem compartilhar a mesma TableOccupancy mantendo ledgers independentes.
- [ ] Fechar uma Tab não encerra automaticamente a TableOccupancy.
- [x] Pedido com produtos ativos e operacionalmente disponíveis é confirmado com snapshot de preço.
- [x] Cozinha/Bar autorizado marca produto da estação como indisponível e a alteração é auditada.
- [x] Produto indisponível deixa de ser confirmável por `STAFF`, `CASHIER` e `GUEST` na regra/API de Order; a UI guest completa fica na Spec 004.
- [x] Carrinho stale é rejeitado na confirmação se algum item ficou indisponível, com indicação dos itens afetados.
- [x] Tornar produto indisponível não altera OrderItem já confirmado.
- [x] Todo Order possui `tab_id`.
- [x] Cada item confirmado gera efeito financeiro exatamente uma vez.
- [x] Estados operacionais registram timestamps.
- [ ] Cancelamento pós-confirmação não apaga histórico e exige auditoria.
- [x] Pagamento manual reduz exposure.
- [x] Tab com exposure zero pode ser fechada.
- [ ] Caixa resume recebimentos por método.
