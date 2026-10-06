# Spec 007 — Management Cockpit + Analytics

**Status:** Draft for implementation after Core POS + realtime foundations

## Objetivo

Transformar o **Rodada Gerência** em uma superfície mobile-first que permita ao gerente entender em segundos o que está acontecendo no estabelecimento, agir apenas nas exceções importantes e, fora do pico, analisar fechamento e desempenho.

Premissa principal:

> **Durante a operação, o gerente não procura problemas: os problemas aparecem para ele.**

A superfície de Gerência é uma Web/PWA responsiva, mas o baseline de design é **celular 360–430 px**, uso com uma mão, em movimento e com baixa atenção disponível. Tablet/desktop expandem densidade e análise; não definem a experiência principal.

## Modos de uso

### 1. Operação ao vivo

Durante o serviço, Gerência funciona como um **cockpit de exceções em tempo real**.

Prioridades:
1. alertas acionáveis;
2. situação de cozinha/bar;
3. comandas/mesas que exigem atenção;
4. pagamentos e caixa;
5. atividade recente;
6. receita e métricas de pulso.

Gráficos históricos nunca podem competir visualmente com problemas operacionais ativos.

### 2. Gestão e fechamento

Fora do pico, a mesma superfície muda de foco para:
- fechamento diário;
- fechamento mensal;
- vendas;
- operação;
- cardápio;
- clientes;
- equipe;
- financeiro;
- insights.

## Navegação mobile

Navegação principal inferior:

```text
Agora | Operação | Vendas | Gestão | Mais
```

Mapeamento:
- **Agora**: pulso + exceções;
- **Operação**: cozinha, bar, atendimento, mesas, pagamentos;
- **Vendas**: receita, ticket, clientes, mix e comparações;
- **Gestão**: fechamento, exceções financeiras, aprovações e configuração operacional;
- **Mais**: cardápio, clientes, equipe, relatórios e configurações.

No desktop, a navegação pode ganhar mais densidade, mas deve preservar a mesma arquitetura de informação.

## MGM-001 — Home “Agora”

A home deve ser legível em aproximadamente 5 segundos.

Ordem recomendada:

```text
RODADA                                  ● AO VIVO

Hoje
R$ 12.840
+8,4% vs terça passada

187 clientes     R$ 68,66 ticket
43 abertas       12 pedidos em fila

⚠ 3 precisam da sua atenção
[alertas acionáveis]

Operação agora
Cozinha       12 fila      8 min
Bar            4 fila      3 min
Pagamentos    R$ 920 pendente

[Ver operação ao vivo]

Últimos eventos
...
```

A comparação padrão deve usar um período operacionalmente comparável quando houver dados suficientes, por exemplo mesma faixa/dia da semana, e não uma comparação arbitrária que induza interpretação errada.

## MGM-002 — Alertas acionáveis

Alertas devem representar uma condição que justifique ação ou atenção do gerente.

Exemplos:
- pedido acima do SLA;
- fila de cozinha/bar acima de limite configurado;
- mesa/comanda aguardando conta acima do esperado;
- pagamento com falhas repetidas ou estado ambíguo;
- item estratégico indisponível;
- caixa/fechamento com divergência;
- comanda aberta após encerramento do turno;
- volume operacional anormal.

Severidade:
- `info`: observação útil, não urgente;
- `warning`: atenção necessária;
- `danger`: ação prioritária.

Cada alerta deve responder:
- o que aconteceu;
- há quanto tempo;
- contexto afetado;
- por que importa;
- próxima ação disponível.

Não notificar eventos normais como “novo pedido”.

## MGM-003 — Operação

A tela Operação mostra cards expansíveis de:
- Cozinha;
- Bar;
- Atendimento;
- Mesas/Ambientes;
- Pagamentos.

Cada card prioriza:
- carga atual;
- tempo/latência;
- quantidade acima de SLA;
- status;
- exceções.

Deve existir ação **Ver só problemas**.

### Mesas e ambientes

No celular, a lista/estado é o caminho primário. O mapa 2D é uma visão especializada com pinch/zoom e filtros.

Estados físicos continuam vindo de Table Ops:
`AVAILABLE`, `OCCUPIED`, `DIRTY`, `CLEANING`, `OUT_OF_SERVICE`.

Gerência pode analisar:
- ocupação por área;
- tempo de permanência;
- giro;
- tempo de limpeza;
- receita por área/hora.

## MGM-004 — Timeline operacional

Gerência possui uma timeline pesquisável e filtrável de eventos relevantes.

Exemplos:

```text
17:52 Pagamento confirmado +R$ 142
17:51 Pedido #928 pronto
17:50 Mesa 18 pediu conta
17:47 Chopp 500 ml ficou indisponível
```

A timeline é uma projeção de fatos persistidos/auditáveis. Não deve inventar precisão para eventos inferidos.

Quando um milestone for inferido, a UI deve poder representar `source` e `confidence` quando isso for material para investigação.

## MGM-005 — Vendas

Métricas iniciais:
- receita bruta;
- receita líquida de ajustes/reembolsos conforme definição financeira;
- número de clientes/visitas quando mensurável;
- Tabs abertas/fechadas;
- ticket médio;
- itens por Tab;
- consumo médio por pessoa quando identidade/quantidade permitir;
- receita por hora;
- receita por ambiente/zona;
- origem do pedido: staff / guest QR / outros canais definidos;
- método de pagamento;
- produtos mais vendidos;
- evolução versus período comparável.

Toda métrica deve ter definição canônica e fonte de dados documentada.

## MGM-006 — Ocupação × receita

Gerência deve conseguir cruzar utilização física com resultado financeiro.

Exemplos de perguntas:
- qual área gera mais receita por hora aberta?
- o que acontece quando a rua passa de 85% de ocupação?
- qual área tem maior giro?
- em quais horários falta capacidade física?

Métricas possíveis:
- ocupação média por área/faixa;
- receita por área;
- receita por hora de área ocupada;
- receita por assento quando capacidade estiver cadastrada;
- giro de mesa;
- tempo de limpeza;
- correlação exploratória entre ocupação, ticket e receita.

Correlação não deve ser apresentada como causalidade.

## MGM-007 — Cardápio e mix

Gerência deve permitir análise de:
- unidades vendidas;
- receita;
- preço médio realizado;
- disponibilidade/tempo indisponível;
- participação no mix;
- combinações frequentes;
- cancelamentos/ajustes ligados ao item.

Quando custo estiver disponível em spec futura:
- custo;
- margem de contribuição;
- CMV.

Não inventar margem sem custo confiável.

Pode existir uma estimativa de oportunidade perdida por indisponibilidade, mas deve ser claramente marcada como **estimativa** e documentar a metodologia.

## MGM-008 — Clientes

Sem transformar Gerência em CRM genérico, mostrar:
- clientes/visitas identificadas;
- novos × recorrentes;
- frequência;
- gasto médio;
- histórico quando Customer estiver associado à Tab;
- participação de guest ordering.

Clientes anônimos permanecem válidos no produto.

## MGM-009 — Equipe

Métricas por pessoa podem existir para diagnóstico operacional, distribuição de carga e auditoria.

**Não criar leaderboard simplista de “melhor funcionário”, “garçom mais rápido” ou equivalente.**

Motivo: incentiva atalhos e ignora contexto, zona, carga, tamanho do pedido e eventos inferidos.

Permitido:
- carga/ownership;
- distribuição de Tabs/tasks;
- tempo por etapa com contexto;
- cancelamentos/overrides;
- ações auditáveis;
- comparação de capacidade da operação como um todo.

Qualquer métrica individual deve distinguir medição observada, inferida e corrigida quando aplicável.

## MGM-010 — Pagamentos e financeiro ao vivo

Mostrar:
- recebido;
- saldo pendente;
- métodos de pagamento;
- pagamentos recusados;
- `CONFIRMATION_PENDING`;
- refunds/estornos;
- divergências;
- caixa atual quando aplicável.

Gerência não deve tratar callback local de provider como confirmação financeira definitiva. Fonte de verdade segue Spec 006.

## MGM-011 — Fechamento diário

O Rodada deve gerar um resumo de fechamento a partir dos próprios eventos/ledger.

Conteúdo mínimo:
- vendas brutas;
- adjustments/cortesias;
- cancelamentos relevantes;
- refunds/estornos;
- recebido por método;
- saldo/pêndencias;
- Tabs ainda abertas;
- posição de caixa;
- divergências;
- exceções operacionais relevantes.

O gerente **confirma/revisa** o fechamento; não precisa remontar o dia manualmente.

Correções pós-fechamento devem preservar histórico e gerar nova evidência/auditoria, nunca reescrever silenciosamente o passado.

## MGM-012 — Fechamento mensal

Fechamento mensal não é apenas soma visual dos dias.

Resumo executivo inicial:
- receita;
- variação vs mês anterior/período comparável;
- clientes/visitas;
- ticket médio;
- receita por hora aberta;
- pico operacional;
- melhor área;
- produtos destaque;
- percentual acima de SLA;
- pagamentos;
- ajustes/cancelamentos/refunds;
- disponibilidade;
- evolução operacional.

A primeira tela deve responder “o que mudou e por quê?” antes de expor gráficos detalhados.

## MGM-013 — Insights

Rodada pode gerar insights determinísticos/estatísticos com linguagem objetiva.

Exemplos:
- “Sextas entre 20h e 21h a fila da cozinha cresce 47%.”
- “A área externa respondeu por 41% da receita no período.”
- “Batata e chopp aparecem juntos em 31% das Tabs que contêm batata.”
- “R$ X em vendas vieram de pedidos iniciados pelo guest QR.”

Regras:
- sempre apontar período/base;
- diferenciar fato, estimativa e hipótese;
- não atribuir causalidade sem evidência;
- permitir abrir os dados que sustentam o insight;
- IA generativa pode resumir futuramente, mas **não é necessária para o P0** e não pode ser a fonte dos números.

## MGM-014 — Push notifications

Push deve ser raro e acionável.

Pode notificar:
- condição crítica sustentada;
- divergência de caixa;
- item estratégico indisponível;
- pagamento relevante em exceção;
- fechamento não realizado;
- situação operacional acima de limiar configurado.

Não notificar:
- todo novo pedido;
- todo pagamento aprovado;
- toda mudança normal de status.

Deduplicar alertas e aplicar cooldown/rate limit.

## MGM-015 — Realtime e consistência

Gerência consome projeções/read models derivadas dos fatos canônicos dos módulos existentes.

Fluxo conceitual:

```text
domain transaction
  -> persisted fact / outbox
  -> projection updater
  -> management read model
  -> websocket invalidation/update
  -> Rodada Gerência
```

PostgreSQL continua fonte de verdade. Redis/WebSocket acelera atualização, mas não define números financeiros nem histórico.

A tela deve mostrar estado de atualização quando conexão realtime cair e revalidar pela API.

## Eventos/fatos relevantes

Exemplos conceituais:
- `tab.opened`;
- `tab.closed`;
- `order.confirmed`;
- `fulfillment.state_changed`;
- `fulfillment.milestone_recorded`;
- `table.occupancy_started`;
- `table.occupancy_ended`;
- `table.cleaning_started`;
- `table.available`;
- `catalog.availability_changed`;
- `payment.confirmed`;
- `payment.failed`;
- `payment.confirmation_pending`;
- `refund.confirmed`;
- `adjustment.created`;
- `cash.shift_opened`;
- `cash.shift_closed`.

Nomes concretos podem mudar; o contrato importante é que projeções sejam reconstruíveis a partir de fatos persistidos.

## Read models iniciais

### ManagementLiveSnapshot
Por Venue:
- business date/turno atual;
- receita/recebido;
- Tabs abertas;
- pedidos em fila;
- carga por estação;
- alertas ativos;
- pagamentos em exceção;
- ocupação por zona;
- timestamp da última atualização.

### DailyOperationsSummary
Por Venue + business date:
- métricas financeiras;
- métricas operacionais;
- disponibilidade;
- ocupação;
- origem do pedido;
- métodos de pagamento;
- exceções.

### MonthlyManagementSummary
Agrega dias fechados e metadados de comparação, sem destruir possibilidade de recalcular.

## Business date

Relatórios de bar/restaurante não devem assumir que o dia operacional termina às 00:00.

Venue deve possuir uma regra de **business date cutoff**/turno operacional para que uma operação iniciada à noite e encerrada de madrugada pertença ao mesmo fechamento.

A regra concreta de calendário deve ser configurável e testada.

## Performance

Objetivos iniciais:
- home mobile deve abrir a partir de read model, sem joins analíticos pesados por request;
- atualização de condição crítica deve aparecer em segundos quando realtime estiver saudável;
- relatórios históricos podem ser eventualmente consistentes por poucos segundos/minutos, nunca às custas de consistência financeira;
- projeções precisam ser idempotentes e reconstruíveis.

## Segurança e permissões

Gerência exige papel autorizado.

Ações sensíveis continuam respeitando permissões do domínio:
- refund;
- adjustment/cortesia;
- override;
- fechamento;
- edição de limiares/configuração.

Visualizar uma métrica não concede capacidade de executar a mutation correspondente.

## Fora de escopo

- ERP completo;
- contabilidade/fiscal avançado;
- folha/ponto;
- estoque por insumo/CMV sem spec própria;
- previsão de demanda automática no P0;
- leaderboard gamificado de funcionários;
- chatbot gerencial como requisito do P0;
- data warehouse externo obrigatório para o MVP.

## Princípios de UX

- mobile-first real;
- informação acionável > decoração;
- problemas primeiro, gráficos depois;
- números grandes e poucos por viewport;
- um gráfico por contexto no celular, não mosaico de mini-gráficos;
- touch target mínimo conforme design system;
- sem hover obrigatório;
- mapa é visão especializada, não home;
- status nunca depende só de cor;
- estado offline/stale precisa ser explícito.
