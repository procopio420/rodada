# Acceptance — Spec 001

- [ ] Staff abre uma Tab sem selecionar mesa ou Customer.
- [ ] Staff pode abrir uma Tab com nome/apelido simples.
- [ ] Staff pode opcionalmente associar/mover a Tab entre contextos físicos.
- [ ] Duas Tabs podem compartilhar a mesma TableOccupancy mantendo ledgers independentes.
- [ ] Fechar uma Tab não encerra automaticamente a TableOccupancy.
- [ ] Pedido com produtos ativos e operacionalmente disponíveis é confirmado com snapshot de preço.
- [ ] Cozinha/Bar autorizado marca produto da estação como indisponível e a alteração é auditada.
- [ ] Produto indisponível deixa de ser confirmável por staff, caixa e guest usando a mesma regra de domínio.
- [ ] Carrinho stale é rejeitado na confirmação se algum item ficou indisponível, com indicação dos itens afetados.
- [ ] Tornar produto indisponível não altera OrderItem já confirmado.
- [ ] Todo Order possui `tab_id`.
- [ ] Cada item confirmado gera efeito financeiro exatamente uma vez.
- [ ] Estados operacionais registram timestamps.
- [ ] Cancelamento pós-confirmação não apaga histórico e exige auditoria.
- [ ] Pagamento manual reduz exposure.
- [ ] Tab com exposure zero pode ser fechada.
- [ ] Caixa resume recebimentos por método.
