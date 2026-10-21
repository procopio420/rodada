# E03-07 — Isolar chamados da venda no Android

Gap confirmado em `main@4652b301`: `refresh` aguarda `readServiceRequests`
antes de ler catálogo/comandas. Chamado lento retém `loading` e impede venda,
mesmo com API de pedidos saudável. A separação de entregas já existe.

Reusar a mesma estratégia: job próprio para chamados, uma leitura em voo,
cancelamento ao trocar sessão e fence original antes/depois do transporte.
Fila desconhecida conserva dados/contagem desconhecida e bloqueia claim/complete;
catálogo/comandas saudáveis podem ficar ONLINE e reconciliar pedidos.
Nenhuma mutation de pedido, pagamento, autenticação ou ledger muda.

Regressão real: reter resposta de chamados, comprovar core atualizado e Order/Charge
únicos, segundo refresh de comandas sem aguardar fila, A→B→A antes de liberar
503 original, recuperação da fila e rejeição de ação enquanto desatualizada.
Executar junto às duas regressões existentes de entregas. Emulador/API/PG
não equivalem a aparelho físico nem aceite integral AC-08/11/21.
