# Acceptance — Spec 031 (proposta)

- [ ] Pedido pronto/chegando e GuestSession válida podem exibir prompt não bloqueante apenas quando elegíveis.
- [ ] Ignorar/dispensar não altera Order, OrderItem, Tab, ledger, Payment ou fila; nunca impede nova rodada.
- [ ] `Sim` registra ator guest, alvo, quantidade, `reported_at` do servidor e proveniência; não inventa horário físico exato de entrega.
- [ ] `Parte` preserva quantidades entregues e pendentes sem completar pedido inteiro.
- [ ] `Ainda não` não é tratado como prova perpétua de não entrega e pode abrir exceção deduplicada segundo política.
- [ ] `Veio errado` gera fluxo de ajuda/Dispatch sem reembolso, cobrança ou cancelamento automáticos.
- [ ] Replays com UUID/payload original retornam mesmo resultado; payload diferente conflita e não duplica eventos.
- [ ] Sessão revogada, ocupação anterior, outro Venue/Tab/Order, estado incompatível e quantidades inválidas são rejeitados com autorização server-side.
- [ ] Feedback tardio ou conflitante preserva histórico e não sobrescreve milestone inferido/observado.
- [ ] Sem staff tap obrigatório, sem hardware obrigatório e falhas de feedback não bloqueiam PDV/fulfillment.
- [ ] Analytics diferencia confirmação guest, inferência, manual/correção e desconhecido, com cobertura e denominador publicados.
- [ ] UI acessível em 360/390/430 px, com recurso visível porém não intrusivo; testes reais com pedidos parciais.
- [ ] Validação PostgreSQL, E2E guest/API/Dispatch, segurança cross-tenant, idempotência, CI final e revisão independente registrados antes de merge de implementação.

Nenhum aceite está marcado como concluído; esta entrega é somente documentação.
