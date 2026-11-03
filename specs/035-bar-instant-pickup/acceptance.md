# Critérios de aceite — Spec 035
- [ ] Criar água em BAR/PICKUP e ler o modo no catálogo; bloquear PICKUP em KITCHEN.
- [ ] Editar modo, sem alterar histórico de pedidos já confirmados.
- [ ] Na fila Bar, produto PICKUP mostra ação **Separado** sem iniciar preparo.
- [ ] Um pedido misto permite água READY enquanto drink permanece NEW, depois preparo e READY normais.
- [ ] Atalho de PREPARE falha; PICKUP não pode receber comando PREPARING; lote misto inválido é atômico.
- [ ] Replay com mesma chave devolve comprovante anterior; READY gera apenas tarefa de dispatch canônica.
- [ ] Build Web, typecheck, testes e validação visual conforme guardrails.
