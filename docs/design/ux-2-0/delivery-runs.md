# Rodada UX 2.0 — Entregas e DeliveryRuns orientados pelo salão

Data: 2026-10-16. **Status: conceito de produto / futura spec**, não comportamento integrado. Direção: separar trabalhos de entrega da fila de atendimento e de pedidos de conta, sem fragmentar o contexto comum da comanda e sem criar tarefas artificiais para o garçom.

Referências: \`specs/003-dispatch/spec.md\` (DSP-003/004/006–010), \`docs/product/principles.md\`, \`docs/domain/model.md\`, \`specs/026-operational-ux-friction/\`. O domínio já reconhece \`DeliveryTask\` e prevê \`DeliveryRun\`; a otimização por mapa está explicitamente fora do escopo inicial da Spec 003.

## Divisão das filas no Agora

- **Atendimentos:** SERVICE_REQUEST e BILL_REQUEST. Tarefas originadas por guest/QR com Tab válida abrem o fluxo contextual da comanda ou da conta; Tab incerta passa pela mesa/seleção autorizada. Claim e conclusão são comandos explícitos onde necessários; navegar não muda tarefa.
- **Entregas:** DeliveryTasks em READY. Mostra quantidade, produto, estação de retirada, destino, idade e status operacional quando disponíveis. A pessoa pode resolver uma entrega específica ou preparar uma saída com vários destinos. Visualização não significa PICKED_UP nem DELIVERED.
- A alternância entre as áreas não mistura contagens, ações, prioridade nem a responsabilidade operacional. Persistência da seleção do operador é opcional, sem impacto no domínio.
- No pico, a fila de prontos pode ser a área inicial por preferência operacional, configuração/role ou estado real; não esconder chamados urgentes. O protótipo permanece com Atendimentos inicial até validação.

## Fluxo de lote proposto

\`\`\`
ENTREGAS
  → tarefas READY agrupáveis / individual
  → Montar saída
      → fonte(s) de retirada e capacidade do funcionário / bandeja
      → selecionar tarefas compatíveis (somente READY e autorizadas)
      → rota proposta pelo mapa/caminhos transitáveis
      → iniciar saída (quando útil, nunca obrigatório apenas para telemetria)
      → observar etapas ou corrigir exceções
      → concluir/ajustar tarefas por evidência canônica ou correção autorizada
\`\`\`

*Uma saída agrupa entregas, não as transforma em pedido, cobrança ou novo Order.* Cada DeliveryTask conserva OrderItem/Tab/destino, a autoria e o estado independente; um lote pode ser parcial ou interrompido. Um Item pode mudar de READY se for corrigido ou cancelado; a proposta deve revalidar o conjunto antes de iniciar, e alterações de mesa/occupancy invalidam a destinação antiga.

### Critérios de compatibilidade antes de roteirizar

1. Mesmo Venue e contexto de autorização, tarefa pendente READY e destino atual resolvido em Table, Zone ou ServicePoint autorizado.
2. Respeitar a **estação física de coleta**: juntar BAR com KITCHEN só se houver plano real para buscar em ambos; por padrão, separar.
3. Capacidade da bandeja e do operador configurável: volume, peso, número de copos e equilíbrio — não somente quantidade arbitrária. Alguns itens são frágeis/quentes e podem exigir viagem dedicada.
4. Combinar proximidade com **idade dos itens**, temperatura/tempo de serviço, prioridade operacional e restrições de acesso; não sacrificar um pedido antigo em nome de trajeto matematicamente curto.
5. Evitar reatribuição de task em posse de outro operador; claim explícito é facultativo e regras de ownership continuam canônicas.
6. Nunca misturar itens com destino/occupancy ambíguos, revogados ou alterados. O fato de duas Tabs estarem na mesma mesa não funde responsabilidade ou pedido.
7. Não marcar DELIVERED por traçado geométrico. O mapa é **ajuda de deslocamento**, não evidência de entrega.

## Modelo espacial para uma rota verdadeiramente otimizada

O salão deve ser um **grafo interno navegável**, não apenas uma imagem com mesas.

- **Floorplan** versionado por Venue: zonas, posições aproximadas das mesas/ServicePoints, pontos de retirada, saídas/obstáculos, corredores e transições (porta, escada, balcão).
- **Waypoints** e **arestas transitáveis** com distâncias estimadas ou custos de caminhada; segmentos interditados/temporários; suporte a área externa.
- IDs físicos estáveis; mudança do móvel ou da mesa não modifica identidade de Tab, Occupancy, OrderItem e nem o histórico.
- Para um lote pequeno, calcular as distâncias de percurso sobre o grafo (ex.: Dijkstra/A*) e buscar uma ordem de visitas viável com capacidade, origem, prioridades e tempo de espera. Para vários stops, usar heurística de VRP/capacitated pickup-and-delivery, sem alegar ótimo global quando o algoritmo for aproximado.
- Distância em linha reta só é aceitável como **estimativa explícita** de demo, não como caminho real em ambiente cheio.
- Melhorar com observação de percursos, sem exigir GPS indoor nem coletar localização contínua de funcionários.

## UX e automação

- A proposta de rota mostra: **Retire no Bar**, quantos itens, mesas agrupadas, ordem sugerida e o porquê quando possível; a pessoa pode reordenar ou desagrupar sem fechar pedidos.
- Não exigir um toque por mesa entregue para alimentar telemetria. A Spec 003 privilegia eventos passivos com proveniência e confiança; caso não haja evidência suficiente, manter estado **não confirmado**, com opção simples de correção por exceção.
- Se houver confirmação humana operacional, ela deve identificar tarefas exatas, revalidar autorização/versão e ser protegida contra replay/resposta perdida. Nenhum lote pode apagar histórico de tarefa individual.
- Fallback sem mapa: agrupar por Zone/estação e mostrar lista textual legível; modo degradado não bloqueia pedidos, venda ou entrega manual.
- Tratar as mudanças de rota em tempo real como sugestões, não comandos financeiros ou conclusões automáticas.

## Protótipo / demo desta iteração

\`prototype/ux-2-0/index.html\` exibe duas áreas em Agora: **Atendimentos** e **Entregas**. Na segunda há quatro tarefas de entrega fictícias, três do Bar compatíveis (duas mesas, quatro bebidas) e uma da Cozinha. A ação **Montar saída** começa com as três do Bar e mostra uma ordem de paradas gerada por vizinho mais próximo em **coordenadas fictícias**, com SVG de referência. Misturar Bar/Cozinha ou ultrapassar quatro unidades bloqueia a simulação; a capacidade de quatro é arbitrária **somente para testar UI**. Concluir o lote altera só o estado JavaScript na página, não o backend.

**O protótipo não conhece corredores reais, obstáculos, dimensão física das bandejas, operação real do Bar do Aderlan ou ETA.** Sua rota não é evidência de viabilidade e não deve ser usada para conduzir funcionários em um bar.

## Implementação incremental proposta

| Etapa | Entrega | Aceitação |
| --- | --- | --- |
| D1 | Filas separadas e tarefa individual contextualizada | Relacionamento canônico DispatchTask → OrderItem → Tab/Occupancy, sem inferir IDs por label; retorno e erro seguro |
| D2 | DeliveryRun manual agrupando por Zone/estação | Revalidação READY, capacidade, ownership, interrupção, auditoria e idempotência |
| D3 | Editor de floorplan / caminhos por Venue | Posição, zoneamento e corredores medidos e conferidos pelos operadores; mudança versionada |
| D4 | Sugestão de percursos com algoritmo | Grafo/capacidade/ordem/idade/estação; indicadores reais versus baseline, teste no estabelecimento |
| D5 | Telemetria e inferência passiva, quando houver evidência | \`MANUAL / INFERRED / CORRECTED\`, confiança e correções sem aumentar ações obrigatórias |

### Gates de validação

- Provar que as duas filas são claras no celular e que pedidos de conta não se perdem em entregas.
- Comparar uma noite normal e pico com 5, 20 e 50 tasks, múltiplas origens, ocupações e mudanças de destino.
- Verificar que um item cancelado, não pronto ou assumido por outro operador não entra indevidamente no lote.
- Medir distância percorrida **real**, tempo READY → destino, idade dos pedidos e intervenções manuais, sem declarar redução por simulação.
- Testar app Web/Android 360/390/430 dp, fontes ampliadas, teclados, offline, timeout, replays e eventos concorrentes.
- Não misturar entrega passiva e declaração fictícia de sucesso; se não houver sinal confiável, preservar a incerteza.

## Fora de escopo desta entrega

API, migrations, domínio, provisionamento de mapa real, algoritmos de produção, sensor/BLE, pagamentos e alteração do app publicado. É um experimento navegável para alinhar produto, não autorização de deploy ou prova de otimização.
