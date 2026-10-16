# North Star e KPIs operacionais — Rodada

**Status:** direção de produto proposta para validação em piloto (não é alegação de ganho medido)  
**Data:** 2026-10-16  
**Contexto:** conversas exploratórias com proprietários de bares, incluindo Santo Malte; referência de operação: Bar do Aderlan.

## Promessa de valor

> **Mais rodadas atendidas, com menos espera e menos trabalho desnecessário para a equipe.**

Rodada não compete por ter mais telas ou ser um ERP reduzido. Compete por remover etapas entre o cliente querer consumir e receber seu pedido, especialmente no pico. Simplicidade é meio; throughput, experiência e confiabilidade são resultados.

### Pitch para discovery

"Quando o bar enche, quanto tempo leva para o cliente conseguir pedir outra cerveja e ela chegar à mesa? O Rodada foi pensado para encurtar esse caminho, sem obrigar sua equipe a ficar registrando cada microetapa."

**Hipóteses a validar:** menor fricção pode aumentar frequência de pedidos e capacidade de atendimento; não assumir que necessariamente aumenta receita ou margem sem piloto e controles.

## Uma North Star, métricas direcionadoras e guardrails

A visão atual do produto estabelece como **North Star estratégica**:

> **Pedidos efetivamente entregues e pagos por hora de funcionamento do Venue, sem piorar a experiência.**

Preservar essa definição já aprovada em `docs/product/vision.md`. Ela é **meta de produto**, não métrica plenamente observável enquanto entrega e alocação de pagamentos não forem verificáveis. Não contar pedido só confirmado ou marcado pronto como entregue e pago.

**Métrica direcionadora candidata, próxima da tese "mais uma rodada":**
**rodadas adicionais efetivamente atendidas por hora de comanda ativa**. Definição inicial de "rodada adicional": pedido elegível posterior ao primeiro Order confirmado da mesma Tab/visita, contado uma vez por Order (não por item nem por clique); sujeito a validar se pedidos fracionados artificialmente causam viés. `Confirmado`, `entregue` e `pago` são estágios diferentes e devem aparecer separados até medição confiável.

### KPIs de fricção (reduzir)

| Sigla | Métrica | Início → fim | Cuidados |
|---|---|---|---|
| **TTNR** | Time to Next Round | Primeira interação instrumentada de novo pedido/repetição → confirmação do novo Order | Não representa o instante em que o cliente *pensou* em pedir; separar guest/staff, novo pedido/repetição e abandonos |
| **HTO** | Human Touches per Order | Contagem de intervenções digitais/manuais *desnecessárias* para levar Order ao fluxo de produção | Contagem por Order; excluir trabalho físico essencial de preparar/entregar; instrumentar apenas ações observáveis, não inventar taps |
| **OSL** | Order-to-Station Latency | Persistência de Order confirmado → evidência de recebimento/exibição na estação de destino | Distinguir evento enfileirado, ack de aplicação e efetiva exibição; com múltiplas estações medir separadamente e explicitar agregação |
| **OTT** | Order-to-Table | Confirmação do Order → entrega ao cliente | Somente valor **observado/confirmado** quando houver evidência adequada; separadamente reportar estimativas, atrasos de confirmação e cobertura. Entrega parcial é por item/lote |

Acompanhar também `READY → PICKED_UP`, `READY → DELIVERED` e `PICKED_UP → DELIVERED` com proveniência por milestone, sem exigir taps do garçom.

### KPIs de resultado (aumentar sem distorcer)

- Pedidos entregues e pagos por hora aberta (North Star estratégica).
- Rodadas adicionais entregues por hora de comanda ativa (diagnóstico; sujeito a viés de confirmação).
- Percentual de Tabs com segunda rodada e valor incremental por Tab/visita.
- Throughput por estação e por período comparável; receita por hora como indicador econômico, **não substituto** de delivery.

### Guardrails

Não otimizar velocidade em detrimento de:
- erros, retrabalho, reenvios, cancelamentos e reclamações;
- tempo até o cliente receber itens, inclusive entregas parciais;
- pagamentos/ledger consistentes, taxa de perda e exceções de caixa;
- satisfação do cliente e carga real da equipe;
- taxa de confirmação/cobertura e incerteza dos dados.

## Regras analíticas obrigatórias

1. Toda métrica tem denominador e janela explícitos: Venue, turno/`business date`, canal, estação, faixa de movimento e número de amostras elegíveis.
2. Exibir mediana e percentil 90 dos tempos, além de média quando fizer sentido; não concluir melhoria com médias isoladas.
3. Não substituir duração faltante por zero. Telemetria ausente, dispositivos offline e pedidos fora do escopo são "desconhecidos".
4. Diferenciar `OBSERVED`, `GUEST_REPORTED`, `MANUAL`, `INFERRED` e `CORRECTED` por fonte, confiança, horário da observação e evidência. A nomenclatura efetiva deve evoluir em Spec 031/ADR 0009 sem quebrar o contrato existente.
5. "Cliente confirmou recebimento às 21:15" **não** significa "entrega aconteceu exatamente às 21:15". O toque pode ocorrer minutos depois. Tempo pedido → toque é um **limite superior observacional**, não RTT preciso da entrega.
6. Confirmado pelo cliente é uma subamostra auto-selecionada: sempre exibir numerador, denominador, cobertura, atraso de resposta quando conhecido e comparação com pedidos não confirmados; jamais generalizar sem validação.
7. Não misturar pedido que entrou na fila com pedido exibido pelo dispositivo: medir a etapa real coberta pela instrumentação.
8. Taxas/pedidos devem ser normalizados por horas de operação efetivas; taxa por Tab-hora pode ser um diagnóstico separado. Definir o que significa "ativa" antes de publicar.
9. Sem rankings de garçons baseados em sinais inferidos. Não atribuir causalidade ao Rodada sem desenho de experimento.

## Telemetria mínima a especificar antes da implementação

- `order.confirmed`: Venue/Tab/Order, horário servidor, source (`GUEST`/`STAFF`), destino de estação.
- `station.order_seen` ou ack verificável: estação/dispositivo e horário servidor; não usar emissão SSE como garantia de visualização.
- Eventos client-side de início de intenção/abertura da ação `Pedir novamente`, envio, falha e abandono (com privacidade e consentimento aplicáveis).
- Milestones de fulfillment com `source`, `confidence` e evidência (ADR 0009), incluindo eventual evidência `GUEST_CONFIRMED` proposta na Spec 031.
- `order.delivery_feedback`: confirmação, entrega parcial, ainda não, erro; tempo observado e escopo autenticado.
- Pagamento financeiro sempre do ledger canônico; não inferir "pago" a partir de estado do pedido.

## Piloto: Santo Malte / Bar do Aderlan

1. Discovery sem pitch inicial: "Se mudasse três coisas no sistema atual, o que mudaria?"; "o que atrasa outra rodada no pico?"; "o que impediria a troca?".
2. Medir baseline com processo atual, sem alegar que VR System possui ou não um fluxo específico até observar a configuração real do estabelecimento.
3. Rodar amostras comparáveis por dia da semana, faixa horária, lotação, estação e tipo de pedido; garantir instrumentação equivalente quando possível.
4. Testar `Pedir novamente`, guest QR (quando permitido), fila na estação e confirmação de entrega opcional; registrar falhas e não respostas.
5. Reconciliar com pagamentos, qualidade, erros, treinamento, impressão e fiscal antes de concluir ganho operacional.
6. Apresentar ganhos e limitações em Rodada Manage (modo histórico/analítico), mantendo a home do pico focada em exceções.

**Critério de direção para novas features:** reduzem TTNR/HTO/OSL/OTT, aumentam throughput confiável ou protegem os guardrails? Não otimizar "mais telas" como objetivo.

## Referências

- `docs/product/vision.md`
- `docs/product/principles.md`
- `docs/adr/0009-passive-fulfillment-telemetry.md`
- `specs/003-dispatch/spec.md`
- `specs/004-table-guest-ordering/spec.md`
- `specs/007-management-cockpit/spec.md`
- `specs/031-guest-delivery-feedback/`
