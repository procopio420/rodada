# E02-02/03 — projeção e confirmação persistente Web

Contrato: PR216/spec033 `619c2718`, baseline PR a publicar, PR212 `ec26e26b`.
Escopo: expor snapshot de estação já persistido em OrderItem no readback existente;
cartão de último pedido confirmado no workspace usando ID/status/linhas históricos.
Sem nova intenção, endpoint, mutation, rota inferida de categoria ou ledger.

Antes: mensagem temporária genérica; histórico apenas na Conta; DTO omitindo
fulfillment_station_snapshot. Depois: confirmação continua visível ao abrir Tab,
mesmo após reload; produção por estação somente do readback canônico, com estado
desatualizado explícito. Valor desconhecido nunca significa READY.

Paridade do cartão segue order-status da PR212. A comanda completa e Compose
continuam pendentes: este slice não conclui E02/AC04 nem paridade global.
Referência SIM substituída pelo Order.id canônico completo, sem criar numeração
fictícia. A projeção aditiva preserva vazio legado como destino desconhecido.
Risco R2 (leitura/UI); testar snapshot histórico após mudança de catálogo e replay,
readback real, refresh/TabA/B e estados desconhecidos antes de recomendar integração.
