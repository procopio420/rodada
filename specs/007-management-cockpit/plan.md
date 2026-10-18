# Plan — Spec 007 Management Cockpit + Analytics

Auditoria de histórico entre papéis (2026-10-18): corrigir leitura do resumo para active=true e paginação completa, com deduplicação/validação de offset e falha sem totais parciais. Não alterar regras de ledger. Validar API com sessões distintas ANDROID/WEB e PostgreSQL descartável, UI de canceladas/pagas e regressão de200+comandas.

Catálogo gerencial: reutilizar ActionDialog, attendanceCategoryGrid, posProducts/ProductIcon e normalização/categorias existentes. QuickCatalog ganha opção explícita de estação autorizada, mantendo comportamento padrão nas estações. CatalogIconEditor separa escolha de categoria/produto do formulário, sem lista select extensa ou disclosure escondido.

## Reorganização por tarefa — 2026-10-18

Centralizar metadados/aliases das cinco abas na navegação. Reagrupar somente links/painéis de manage, mantendo leituras e guards. Atualizar retornos estáticos internos e vocabulário do design system. Usar âncoras nativas para hash/retorno: Next Link concatenava hash inicial ao retornar de página interna, reproduzido em regressão. Validar jornadas/pixels com fixtures, responsividade/acessibilidade, typecheck/build e suite visual; risco R2, sem mutations novas.

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

Piloto: adiar montagem de alertas até snapshot autorizado; preservar falha explícita.

## Histórico em popup — 2026-10-17

ManagementTabHistory reutiliza ActionDialog, OperationalIcon/history, BillSummary e tokens. GET via BFF existente com history_day, data fixada entre páginas e detalhe canônico; nenhum comando financeiro. AbortController e geração invalidam leituras em navegação/close/unmount. Parent mantém trava após revogação, impedindo remontagem por leitura antiga.
