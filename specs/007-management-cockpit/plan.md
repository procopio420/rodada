# Plan — Spec 007 Management Cockpit + Analytics

## Estratégia

Implementar em vertical slices, começando pelo read model operacional e pela home mobile. Não começar por gráficos históricos.

## Slice 1 — Fundação de projeções

- definir fatos internos consumidos pela Gerência;
- usar outbox/event publication idempotente;
- criar `ManagementLiveSnapshot`;
- endpoint de leitura por Venue;
- invalidação/update realtime;
- fallback por polling/revalidation.

## Slice 2 — Agora + alertas

- home mobile;
- métricas de pulso;
- alertas por regra;
- severidade, deduplicação e lifecycle;
- timeline operacional;
- “ver só problemas”.

## Slice 3 — Operação detalhada

- cards Cozinha/Bar/Atendimento/Mesas/Pagamentos;
- drill-down;
- ocupação por zona;
- mapa 2D como visão secundária;
- estados stale/offline.

## Slice 4 — Fechamento diário

- `DailyOperationsSummary`;
- business date configurável;
- resumo financeiro/operacional;
- divergências e Tabs abertas;
- confirmação auditável.

## Slice 5 — Vendas + fechamento mensal

- métricas canônicas;
- comparadores de período;
- `MonthlyManagementSummary`;
- cards/gráficos mobile;
- drill-down por dia/área/produto/método.

## Slice 6 — Insights + push

- insights determinísticos;
- labels fato/estimativa/hipótese;
- push apenas para exceções configuradas;
- cooldown e deduplicação.

## Regras técnicas

- PostgreSQL é autoridade;
- dinheiro deriva do ledger;
- projeções são idempotentes e reconstruíveis;
- não usar WebSocket como fonte de verdade;
- evitar query analítica pesada na home;
- timestamps e business date devem ser timezone-aware;
- métricas baseadas em milestones inferidos preservam provenance;
- nenhuma projeção pode reclassificar evento inferido como observado.

## Design

Baseline 360–430 px.

Priorizar componentes existentes:
- AppShell;
- ProductHeader;
- SurfaceNav / bottom navigation;
- Metric;
- MoneyValue;
- Panel;
- DataRow;
- StatusBadge;
- InlineNotice;
- WorkCard.

Novos padrões transversais só entram no design system se não puderem ser compostos de primitives existentes.
