# Tasks — Spec 007 Management Cockpit + Analytics

## Domain / contracts

- [ ] Definir business date/cutoff por Venue.
- [ ] Catalogar fatos/eventos consumidos pela Gerência.
- [ ] Definir contratos de `ManagementLiveSnapshot`, `DailyOperationsSummary` e `MonthlyManagementSummary`.
- [ ] Definir fórmula canônica de cada métrica P0.
- [ ] Definir provenance para métricas que usam milestones inferidos.

## Persistence / projections

- [ ] Implementar outbox/publicação idempotente para fatos relevantes ainda não cobertos.
- [ ] Implementar projeção idempotente do snapshot ao vivo.
- [ ] Implementar resumo diário.
- [ ] Implementar rebuild/replay de projeções.
- [ ] Implementar agregação mensal a partir dos resumos/fatos canônicos.

## API / realtime

- [ ] Endpoint da home “Agora”.
- [ ] Endpoint de alertas ativos.
- [ ] Endpoint de timeline com filtros/paginação.
- [ ] Endpoints de operação por estação/mesa/pagamento.
- [ ] Endpoints de fechamento diário/mensal.
- [ ] Invalidação/update realtime com fallback de revalidation.

## Frontend — mobile first

- [ ] Bottom navigation: Agora / Operação / Vendas / Gestão / Mais.
- [ ] Home com números de pulso + alertas.
- [ ] Estado “ver só problemas”.
- [ ] Cards Cozinha/Bar/Atendimento/Mesas/Pagamentos.
- [ ] Timeline.
- [ ] Vendas com um gráfico/contexto por vez no mobile.
- [ ] Fechamento diário.
- [ ] Fechamento mensal com resumo executivo.
- [ ] Estados loading/empty/stale/offline.
- [ ] Expansão tablet/desktop sem quebrar IA mobile.

## Alerting

- [ ] Regras configuráveis de SLA/limiar.
- [ ] Severidade.
- [ ] Deduplicação.
- [ ] Cooldown.
- [ ] Resolver/expirar alerta quando condição deixar de existir.
- [ ] Push apenas para condições aprovadas pela spec.

## Insights

- [ ] Insights determinísticos P0.
- [ ] Base/período visível.
- [ ] Fato vs estimativa vs hipótese.
- [ ] Drill-down para dados sustentadores.
- [ ] Testes para não inferir causalidade.

## Guardrails

- [ ] Nenhum leaderboard simplista de funcionário.
- [ ] Nenhuma margem/CMV sem custo confiável.
- [ ] Nenhum sucesso financeiro derivado só de callback local.
- [ ] Nenhum evento inferido apresentado como observado.
- [ ] Nenhum fechamento reescreve histórico silenciosamente.

- [x] Piloto: acesso negado sem duplicar avisos de painéis não autorizados.
