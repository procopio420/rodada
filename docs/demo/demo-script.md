# Demo — Bar do Aderlan

Objetivo: mostrar que Rodada não é só “comanda digital”. Ele junta **PDV + operação + relacionamento + mesa/self-service**, sem confundir mesa com conta.

## Cena 1 — abrir atendimento

1. Buscar `João da Oficina`.
2. Mostrar `🏠 DA CASA`, limite R$ 500 e histórico sem pendências.
3. Abrir Tab `João`.
4. Associar opcionalmente à ocupação atual da Mesa 24 / Rua.

## Cena 2 — várias comandas na mesma mesa

1. Mostrar Mesa 24 como `OCCUPIED`.
2. Na mesma ocupação, exibir Tabs `João`, `Ana` e `Rafael`.
3. Reforçar: cada pedido e saldo continuam separados; a mesa só diz onde o grupo está.

## Cena 3 — cliente pede pelo QR

1. Escanear o QR da Mesa 24.
2. Abrir a PWA sem instalação/login obrigatório.
3. Mostrar `Você está na Mesa 24`.
4. Criar/assumir uma Tab.
5. Adicionar `2 Brahma` e enviar.
6. Pedido aparece na mesma fila do Bar com `source=GUEST`.
7. Mostrar botão do staff `Bloquear pedidos QR` sem fechar a Tab.

## Cena 4 — cozinha controla disponibilidade

1. Na tela Cozinha, marcar `Fritas` como `UNAVAILABLE` porque acabou.
2. Mostrar que o item muda imediatamente para "Indisponível" no catálogo do staff.
3. Abrir o menu guest da Mesa 24 e mostrar a mesma indisponibilidade.
4. Tentar confirmar um carrinho antigo com Fritas e mostrar a rejeição explícita do item.
5. Reativar Fritas e mostrar retorno aos canais.
6. Reforçar: isso não cancela pedido de Fritas que já estava confirmado/preparando.

## Cena 5 — vender pelo staff

1. Na Tab João, adicionar `4 Brahma` e `1 Fritas`.
2. Confirmar pedido.
3. Mostrar que Brahma roteia para Bar e Fritas para Cozinha.
4. Charges aparecem no mesmo Tab/ledger.

## Cena 6 — operar

1. Brahmas ficam `READY`.
2. Sistema cria/mostra entrega pendente para `Rua / Mesa 24`.
3. Agrupar com outro pedido pronto na Rua em um `Run`.
4. Garçom assume e conclui a entrega.

## Cena 7 — acessar a mesma Tab de vários jeitos

Mostrar a Tab João sendo resolvida por caminhos equivalentes:

- busca por nome;
- perfil Customer/Rodada;
- código curto;
- guest session no celular;
- QR dinâmico da própria Tab;
- pulseira/tag NFC associada temporariamente.

Reforçar: são identificadores/acessos; **a Tab é uma só**.

## Cena 8 — controlar exposição

1. Tab chega a R$ 420 / R$ 500.
2. Mostrar aviso de proximidade do limite.
3. Receber parcial de R$ 200.
4. Exposure cai para R$ 220 sem fechar Tab.

## Cena 9 — fechar sem confundir com liberar mesa

1. Receber restante da Tab João e fechá-la.
2. Ana ainda está com Tab aberta: Mesa 24 continua `OCCUPIED`.
3. Depois de todos saírem, staff toca `Liberar mesa`.
4. Mesa vira `DIRTY`; guest ordering é bloqueado e sessões da ocupação deixam de autorizar novos pedidos.
5. Funcionário toca `Iniciar limpeza` e depois `Limpa / disponível`.
6. Mesa volta a `AVAILABLE` com nova `access_generation`.
7. Mostrar métricas de ocupação, espera para limpeza e duração da limpeza.

## Pergunta para o Aderlan

> “Se isso funcionasse numa sexta cheia, onde você acha que mais mudaria sua operação?”
