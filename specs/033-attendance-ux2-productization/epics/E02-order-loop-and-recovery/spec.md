# Epic E02 — Pedido direto, estado canônico e recuperação

**Prioridade P0** · Dono: OrderWorkspace/useOrderIntent, Android order intents, Ordering/Production read models · Dependência: baseline E06-01 e acordo de seleção E01. **Somente contrato.**

## Reuso obrigatório
apps/web/lib/client/order-intent.ts já suporta submit/replay com idempotency_key, storage, validação de readback; Spec 026 T05a/T05b já investiu em recuperação. Android README confirma intenção imutável cifrada com AES-GCM/Keystore, reconciliação sequencial após restart e sem fila genérica de dinheiro offline. **Não criar segundo motor ou esquema de intenções** sem demonstração de lacuna concreta.

## Experiência alvo
1. Ao escolher Tab, catálogo permanece acessível, quantidades e variantes/modificadores/observações continuam respeitando produto. Um botão **Enviar N itens** confirma o pedido sem segunda tela obrigatória. **Ver resumo** é opcional e jamais soma itens não enviados ao saldo.
2. Mais uma rodada: copiar linhas históricas reconfiguradas, permitir selecionar/excluir/quantidade, **confirmar repetição** uma vez. Novo pedido é nova intenção, não replay do Order anterior; preservar check de disponibilidade/estação/preço atual e autorizações de correção.
3. Resposta positiva **não basta** se payload incompleto: readback da Tab/Order confirma identificador, linhas, preço histórico e destino por OrderItem/fulfillment_station_snapshot. Mostrar algo como “Pedido #… confirmado — Bar: novo; Cozinha: preparando” baseado somente em estados **realmente retornados**. Nunca inferir categoria de produto como estação.
4. Resposta perdida após commit, timeout, app suspenso ou reload → status **resultado não confirmado**, bloquear segundo envio daquela intenção, guardar payload/fingerprint/chave/Tab/Venue/sessão e oferecer **Verificar pedido**. Reconciliar com endpoint canônico e mesma chave; se o servidor não expõe consulta suficiente, ampliar leitura existente de maneira aditiva, sem reenviar com outra chave.
5. Erro definitivo (403, fechamento de Tab, produto indisponível, SPENDING_LIMIT_EXCEEDED, conflito) exige revalidação e correção. Erro incerto não pode ser convertido em “falhou, tente novamente” com nova intenção. Reconciliar antes de descartar.
6. Conflitos com estoque/serviço, atualizações do venue, status da produção e cancelamento tardio permanecem regidos Specs 001/010/014/017/026. Caixa/PSP não envolvidos.

## Projeções
TabDetails.orders[] / OrderItem state e fulfillment_station_snapshot; ver reutilização do backend antes de criar endpoint. Em UI exibir data/hora só se canônica; estados UNKNOWN/CONFIRMED/NEW/ACCEPTED/PREPARING/READY/DELIVERED distintos. A UI não “envia para bar” presumindo aceitação.

## Não objetivos
Nova fila offline de pagamentos, pedido otimista sem resposta, websocket como fonte financeira de verdade, tela extra de revisão, Order duplicado após retry.

## Aceite
AC-04..07 geral, replay depois de commit, processo Android morto, web refresh, dois operadores enviando, mesmo key/fingerprint diferente, Bar/Cozinha distintos e failover realtime.
