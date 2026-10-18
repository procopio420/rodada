# Acceptance — Spec 007 Management Cockpit + Analytics

## Catálogo gerencial — 2026-10-18

Uma ação de adicionar (sem duplicar Bar/Cozinha); escolha de estação autorizada na criação; editar visível como botão. Popup: categorias/Todos→grade→formulário do produto correto, busca e retorno/Escape/foco, loading/vazio/erro e save pendente explícitos. Navegar não emite mutation. Nome/ícone mantêm endpoints/validações; polling não sobrescreve nome em edição. Validar 360/390/430/desktop, fonte200%, teclado/axe e regressão do QuickCatalog nas estações.

## Navegação por tarefa — 2026-10-18

- Cinco destinos: Agora, Operação, Financeiro, Cardápio e Gestão, com heading/descrição correspondentes.
- Caixa/fechamento/estornos/aprovações/relatórios juntos; salão/produção/giro juntos; produtos/variações juntos; configuração/equipe/clientes/impressoras juntos, sem duplicação de destinos principais.
- Retornos internos preservam a área; aliases vendas/mais e voltar/avançar do navegador selecionam a aba correta.
- Validar navegação com fixtures equivalentes antes/depois, 360/390/430/1280px, fonte200%, teclado, alvos44px, axe, loading/vazio/erro e alertas financeiros preservados. Testes de UI não comprovam aceite de operador real.

## A1 — Home mobile

Dado um gerente autenticado em viewport de 360–430 px,
quando abrir Gerência,
então deve ver primeiro pulso do dia, alertas acionáveis e estado operacional,
sem depender de gráfico histórico para entender se existe problema agora.

Regressão de 2026-10-18: resumo consulta somente Tabs ativas e percorre next_offset antes de publicar contagem/exposição. Histórico encerrado não pode esconder abertas antigas. Falha/401 em página intermediária ou offset inválido não publica totais parciais. Paginação não constitui snapshot transacional de alterações concorrentes; revalidação continua necessária.

Leituras entre papéis: abertura pelo atendimento aparece à gerência; parcial/pendente fica aberta; quitação confirmada sai das ativas e aparece no histórico com itens/pagamentos; cancelamento vazio auditado aparece Cancelada sem recebimento. Itens totalmente cancelados e Tab encerrada preservam histórico sem selo Paga. Período usa dia operacional; outro Venue não acessa os dados. Evidência: [manager-history-audit.md](manager-history-audit.md).

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

Piloto: falha inicial de autorização mostra um aviso e nenhuma conclusão de operação
sem exceções; após leitura válida, painel de alertas mantém seu tratamento de falhas.

## Histórico em popup — 2026-10-17

Ícone discreto no cabeçalho abre histórico do dia operacional, permite data/busca/paginação e detalhes somente leitura; transferência é explícita. Voltar restaura lista/foco. Revogação desmonta/limpa histórico e resposta antiga não pode repopular. Evidência: [histórico da gerência](tab-history-evidence.md).

Extrato concluído: Total da conta substitui Total a pagar; selo Paga depende de quitação confirmada líquida e ausência de taxa desatualizada; simulação explícita. Omitir saldozero e parcelas zeradas sem esconder transferência/estorno/pendências. Casos pagos, transferência, pendente, cortesia, simulado, estornado e taxa desatualizada cobertos em management-tab-history.spec.ts.

Evidência do recorte de navegação por tarefa: [navigation-evidence.md](navigation-evidence.md), 42 casos focados PASS; gate global bloqueado em seletor legado de Atendimento.
