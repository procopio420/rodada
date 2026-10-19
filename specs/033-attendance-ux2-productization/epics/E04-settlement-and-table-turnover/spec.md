# Epic E04 — Conta, pagamento parcial, Tab CLOSED e giro da mesa

**Prioridade P0** · Owner: POS/Payments/Cash/Hospitality + interfaces Web/Compose · baseline de E06-01. **Somente contrato.**

## Reuso obrigatório
Android README já descreve pagamentos parciais manuais CASH/terminal externo, Tab close, ocupação, liberação e limpeza. Web OrderWorkspace e BillSummary já mostram ledger/histórico e preço histórico. Specs 001/004/006/012/014/017/029 e ADRs financeiros são proprietários de mutations; **não copiar o recebimento fake do protótipo** nem criar endpoint paralelo sem necessidade.

## UX final

- A conta abre na **Tab financeira escolhida**, com itens confirmados, total canônico, recibos/recebimentos, saldo real, datas/estados pertinentes e alerta de divergência. Draft nunca entra no total devido.
- **Receber parcialmente** reduz saldo só quando servidor confirma Payment e readback; Tab continua OPEN. Suportar múltiplos métodos que já forem legitimamente permitidos pelo dispositivo/capability e não iniciar Tap to Pay sem PSP homologado.
- **Receber total e encerrar** parece uma ação única ao operador **somente se** o backend tiver confirmações atômicas/seguras suficientes. Caso contrario, 2 mutations idempotentes coordenadas (Payment→readback→Tab.close), com estado "recebido; encerramento pendente" recuperável, sem repetir cobrança/fechar com saldo errado. Nunca criar nova intenção no lost ACK.
- Saldo zero permite **Encerrar comanda** diretamente, sem tela de revisão duplicada. Condições especiais (refund/correção/reauth/cash) exigem intervenção adequada; UX curta não contorna autorização.
- Fechamento de Tab não libera TableOccupancy. Mesa multi-Tab mostra quais ainda estão abertas; quando todas encerradas e condições operacionais canônicas permitem, oferecer **Grupo saiu · Liberar mesa** explicitamente. Não exigir segundo “revisar” e checkbox repetido.
- Após release, DIRTY→CLEANING→AVAILABLE conforme API. Revogação de GuestSession/generation é obrigação do servidor. Mesas disponíveis não herdam sessões/Tabs da ocupação anterior.
- Delivery READY não prova que grupo saiu. Proteger contra task com destino obsoleto, mas não criar uma proibição de release unicamente na UI que contrarie o contrato vigente da API; tratar ocorrências com orientação operacional e regra canônica por Venue.

## Contratos e estados adversos

- Eventos financeiros/ledger são idempotentes, conciliáveis, com origem/PSP/CashShift, sem reuso de PaymentIntent em outra Tab ou Venue. Não inferir pagamento de mera intenção PIX iniciada, cartão autorizado ou código FG84.
- Se Payment confirmado e Tab.close falha/timeout, mostrar **comanda paga, encerramento não confirmado**; reconciliar Tab, não cobrar de novo. A operação de mesa deve revalidar occupancy/generation e capabilities.
- Em um recebimento partial, garantir amounts em centavos, saldo não negativo, troco/caixa correto, session consistency e no duplicated cash entry.
- Não chamar fechamento de Tab “fechamento de caixa”; CashShift é independente.

## Fora de escopo
Cobrança fictícia, garantia cartão/caução, mudança de ledger/PSP sem spec, emissão fiscal sem owner, otimizar bandejas ou liberar por QR público.

## Aceite
AC-12..16. Mesa com três Tabs, duas quitadas/uma aberta, pagamento misto parcial, lost ACK depois de lançamento, refund pendente, cleaner, visitante com QR expirado e conta de balcão sem mesa.
