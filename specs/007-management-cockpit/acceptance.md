# Acceptance — Spec 007 Management Cockpit + Analytics

## A1 — Home mobile

Dado um gerente autenticado em viewport de 360–430 px,
quando abrir Gerência,
então deve ver primeiro pulso do dia, alertas acionáveis e estado operacional,
sem depender de gráfico histórico para entender se existe problema agora.

## A2 — Exceção aparece sem caça manual

Dado um pedido acima do SLA,
quando a projeção atualizar,
então um alerta deve aparecer com contexto, tempo e próxima ação,
sem exigir que o gerente navegue até a cozinha para descobrir o problema.

## A3 — Realtime degradável

Dado WebSocket/Redis indisponível,
quando o gerente continuar usando o app,
então o estado deve indicar stale/offline e revalidar via API,
sem inventar atualização e sem perder a capacidade de leitura básica.

## A4 — Financeiro consistente

Dado um callback local de Tap on Phone sem confirmação server-side,
quando Gerência mostrar pagamentos,
então a cobrança não pode entrar como recebida definitivamente.

## A5 — Timeline auditável

Dado um evento persistido relevante,
quando o gerente abrir a timeline,
então consegue localizar o evento e seu contexto.

Se o evento/milestone for inferido, isso não pode ser mascarado como observação manual.

## A6 — Business date

Dado um Venue cujo cutoff operacional ocorre após meia-noite,
quando uma venda acontecer antes do cutoff,
então ela deve pertencer ao mesmo business date da operação noturna configurada.

## A7 — Fechamento diário

Dado um dia operacional encerrado,
quando o gerente abrir o fechamento,
então o sistema apresenta vendas, recebimentos, ajustes/refunds, Tabs abertas e divergências sem reconstrução manual.

## A8 — Correção pós-fechamento

Dado um ajuste feito depois do fechamento,
quando o histórico for consultado,
então o fechamento original e a correção permanecem auditáveis; o passado não é sobrescrito silenciosamente.

## A9 — Fechamento mensal

Dado um mês com dias fechados,
quando abrir o resumo mensal no celular,
então a primeira visão responde receita, variação, ticket, clientes/visitas, pico, área/produto destaque e saúde operacional antes de gráficos detalhados.

## A10 — Ocupação × receita

Dado histórico suficiente de TableOccupancy e vendas,
quando o gerente analisar uma área,
então consegue comparar ocupação/giro com receita por período sem a UI afirmar causalidade.

## A11 — Sem leaderboard tóxico

Quando métricas de equipe forem exibidas,
então a interface não deve apresentar ranking simplista de “melhor/mais rápido” e deve preservar contexto/provenance relevante.

## A12 — Push útil

Dado fluxo normal de pedidos e pagamentos,
então novos pedidos e pagamentos aprovados não geram push gerencial por padrão.

Dada uma condição crítica configurada e sustentada,
então o gerente pode receber uma notificação deduplicada.

## A13 — Insights rastreáveis

Dado um insight do sistema,
quando o gerente tocar nele,
então deve ser possível identificar período/base/dados que o sustentam e se ele é fato, estimativa ou hipótese.
