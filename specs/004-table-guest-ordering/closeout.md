# Spec 004 — matriz de fechamento operacional (14/10/2026)

Base auditada: `main@d5acc98` (PR #143). Branch `fix/spec004-closeout`.
Inventário inicial exato: tasks **28 concluídas / 48 pendentes**;
acceptance **41 concluídos / 20 pendentes**. Checkbox é inventário documental,
não prova de ausência. Classificação abaixo preserva todos os textos originais.

## Contrato final

MVP: Table/Occupancy independentes de Tab, Zone textual, QR opaco permanente,
GuestSession revogável, QR-first, 0..N Tabs, pedidos canônicos/idempotentes,
política/bloqueio/disponibilidade, Dispatch, consulta da própria Tab e lifecycle
release/limpeza. Este fechamento não significa que todo o roadmap original existe.

- #144: FloorPlan, TablePlacement, edição/arrasto/CAS, projeção guest sanitizada.
- #145: TableGroups; agrupamento físico nunca funde identidade financeira.
- #146: TabIdentifier/código curto/QR dinâmico/NFC; dependência de autorização comum.
- #147: login/perfil Customer e claim guest autorizado; Customer opcional staff não é prova.
- #148: queries/relatórios de giro/limpeza; timestamps canônicos já são entregues.
- #106: turno integrado Web + Android e gates de dispositivo/campo; PR #127 entrega
  correlação Android → Web Bar, não a totalidade desse aceite.

Decisão autorizada pela missão de 14/10: adiar recursos opcionais sem apagar o
contrato original. Nenhum item foi classificado OBSOLETE: não há decisão que
justifique apagar capacidade. Table sem FloorPlan é válida; o critério que exige
TablePlacement será validado no roadmap #144. “minha parte” depende de identidade
participante e não é total da Table; MVP mostra a própria Tab.

PRs examinados: #107 (serviço/claim/start/open/rollout), #119 (UX/recovery/menu/
repetição), #127 (Android → Bar). Confirmados integrados no histórico da base.
Spec 027 exige owner opcional para QR-first e claim explícito; não bloquear pedido
por ausência de owner. Spec 026 governa os envelopes/replay e configuração de repetição.

## Matriz completa

`código` e `teste` são caminhos relativos à raiz. Evidência executada em seção
própria, vinculada ao SHA do PR. As linhas IMPLEMENTED representam existência e
cobertura; aceite final exige gates PASS do mesmo SHA. DEFERRED fica desmarcado.

| critério | classificação | código | teste | evidência | decisão |
| --- | --- | --- | --- | --- | --- |
| tasks.md:5 — Table model + status | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:6 — Zone textual P0 + associação auditada Table -> Zone | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:7 — FloorPlan model + guest/staff projections | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:8 — TablePlacement model + active-placement invariant | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:9 — normalized x/y coordinates + placement history | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:10 — optimistic locking/version on placement mutation | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:11 — TableGroup temporary grouping | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #145; não bloqueia MVP |
| tasks.md:12 — TableOccupancy model + invariants | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:13 — TablePlacement ↔ ServicePoint/Zone integration | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:14 — Tab ↔ TableOccupancy optional association | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:15 — enforce multiple Tabs per occupancy | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:16 — release table service | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:17 — cleaning start/complete services | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:18 — increment `access_generation` on cleaning completion | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:19 — GuestSession model | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:20 — TabIdentifier model | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #146; não bloqueia MVP |
| tasks.md:21 — opaque Table public token | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:22 — short code identifier | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #146; não bloqueia MVP |
| tasks.md:23 — dynamic Tab QR identifier | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #146; não bloqueia MVP |
| tasks.md:24 — NFC_TAG association/revocation | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #146; não bloqueia MVP |
| tasks.md:25 — guest ordering modes | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:26 — guest block/unblock | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:27 — server-side generation validation | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:28 — rate limiting | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:29 — audit events | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:30 — metrics queries | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #148; não bloqueia MVP |
| tasks.md:34 — resolve QR | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:35 — table context screen | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:36 — sanitized 2D floorplan | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:37 — "Onde vocês estão?" placement flow for unplaced Table | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:38 — handle placement conflict/stale version | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:39 — create anonymous/named Tab | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:40 — join existing Tab by short code | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #146; não bloqueia MVP |
| tasks.md:41 — optional login/profile path | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #147; não bloqueia MVP |
| tasks.md:42 — menu/catalog consumindo disponibilidade operacional compartilhada | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:43 — item indisponível visualmente desabilitado | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:44 — tratamento de carrinho stale quando disponibilidade muda antes do submit | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:45 — add item / notes | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:46 — submit order | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:47 — persistent navigation: Cardápio / Pedidos / Conta | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:48 — quick-add item; modifiers only when required | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:49 — live order summary | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:50 — simplified guest order status | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:51 — reorder previous available items | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:52 — structured service/bill requests to Dispatch | IMPLEMENTED | `apps/api/modules/dispatch/services.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_dispatch.py; apps/web/tests/integration/service-requests.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:53 — tab total / own-part projection when available | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:54 — show dynamic Tab QR | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #146; não bloqueia MVP |
| tasks.md:58 — 2D floor canvas with movable Table markers | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:59 — place previously unplaced Table | DEFERRED | — | — | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:60 — clear placement when Table is physically removed/stored | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:61 — drag/reposition active Table without touching occupancy/tab | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:62 — create/dissolve TableGroup | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #145; não bloqueia MVP |
| tasks.md:63 — table board: AVAILABLE / OCCUPIED / DIRTY / CLEANING / OUT_OF_SERVICE | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:64 — occupancy detail with multiple Tabs | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:65 — release table | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:66 — start cleaning | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:67 — mark clean/available | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:68 — guest ordering block toggle | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:69 — associate/move Tab | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:70 — issue/revoke NFC tag | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #146; não bloqueia MVP |
| tasks.md:71 — show/copy short code | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #146; não bloqueia MVP |
| tasks.md:75 — cannot order against sequential/raw table id | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:76 — old GuestSession rejected after occupancy release/generation change | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:77 — guest block rejects guest mutation but staff still orders | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:78 — two Tabs on same occupancy remain financially independent | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:79 — closing last Tab does not release table | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:80 — cleaning timestamps produce deterministic metrics | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #148; não bloqueia MVP |
| tasks.md:81 — NFC reassignment revokes previous association | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #146; não bloqueia MVP |
| tasks.md:82 — moving a Table preserves occupancy, Tabs, Orders, ledger and QR | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:83 — guest floorplan does not expose internal operational state | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:84 — concurrent placement update rejects stale version | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| tasks.md:85 — grouping Tables never merges financial identity | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #145; não bloqueia MVP |
| tasks.md:86 — rate limit tests | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:87 — authorization tests | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:89 — Round 2: guest service/bill buttons call persisted Dispatch requests without financial mutations. | IMPLEMENTED | `apps/api/modules/dispatch/services.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_dispatch.py; apps/web/tests/integration/service-requests.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| tasks.md:90 — Round 2: retain integrated browser/visual evidence at final release SHA. | IMPLEMENTED | `apps/web/components/guest-ordering.tsx` | `apps/web/tests/{integration,visual}/guest-navigation.spec.ts` | Playwright real + 525 visual PASS; capturas versionadas | release de código do PR; campo/turno #106 |
| acceptance.md:4 — Explicit occupied destination and independent origin lifecycle verified in 360/390/430. | IMPLEMENTED | `apps/web/components/attendance-web.tsx; apps/web/components/order-workspace.tsx; apps/api/modules/ordering/views.py` | `apps/web/tests/{integration,visual}/table-entry.spec.ts; apps/web/tests/integration/tab-location-move.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:5 — Web/API PostgreSQL proves one movement after lost response/reload, with immutable financial snapshots and preserved assignment history. | IMPLEMENTED | `apps/web/components/attendance-web.tsx; apps/web/components/order-workspace.tsx; apps/api/modules/ordering/views.py` | `apps/web/tests/{integration,visual}/table-entry.spec.ts; apps/web/tests/integration/tab-location-move.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:11 — Mesa possui QR com token opaco não sequencial. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:12 — QR permanece o mesmo quando a mesa muda de lugar. | IMPLEMENTED | `apps/api/modules/hospitality/services.py::set_table_location` | `apps/api/tests/test_hospitality_tables.py::test_zone_context_moves_a_table_without_touching_occupancy_or_tab_identity` | contexto textual Table/Zone; token preservado | MVP textual; nenhum posicionamento 2D validado (#144) |
| acceptance.md:13 — Scan do QR resolve a Table sem expor PK interno. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:14 — Table pode existir AVAILABLE sem placement ativo. | IMPLEMENTED | `apps/api/modules/hospitality/models.py` | `apps/api/tests/test_hospitality_tables.py::test_table_has_opaque_stable_public_token` | Table criada AVAILABLE sem relação obrigatória de placement | existência independente entregue; mapa continua #144 |
| acceptance.md:15 — Staff autorizado pode associar/remover o contexto textual de Zone sem alterar ocupação, Tabs, pedidos, ledger ou QR. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:16 — Guest abre PWA sem instalar app ou criar conta. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:17 — Ao escanear Table sem placement, guest pode selecionar posição aproximada num floorplan 2D sanitizado. | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| acceptance.md:18 — Staff pode posicionar ou arrastar uma Table no floorplan. | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| acceptance.md:19 — Staff pode retirar uma Table do mapa encerrando apenas o placement, sem apagar a Table ou trocar o QR. | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| acceptance.md:20 — Reposicionar Table preserva TableOccupancy, Tabs, Orders, ledger, GuestSession válida e QR. | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| acceptance.md:21 — Update concorrente com versão stale não sobrescreve placement silenciosamente. | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| acceptance.md:22 — Floorplan guest não expõe estados operacionais de outras mesas, staff ou filas internas. | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #144; não bloqueia MVP |
| acceptance.md:23 — Staff pode agrupar/desagrupar Tables sem fundir suas identidades ou contas. | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #145; não bloqueia MVP |
| acceptance.md:24 — Em `DIRECT`, guest pode iniciar atendimento numa Table `AVAILABLE`. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:25 — Em `JOIN_ACTIVE`, guest não inicia ocupação nova. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:26 — Em `DISABLED`, guest não envia pedido. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:27 — Uma TableOccupancy suporta duas ou mais Tabs independentes. | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:28 — Todo pedido guest pertence a uma Tab e possui `source=GUEST`. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:29 — Pedido guest chega à mesma pipeline de fulfillment de um pedido staff. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:30 — Item marcado indisponível por Bar/Cozinha aparece indisponível no menu guest sem criar regra paralela. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:31 — Guest não confirma item que ficou indisponível depois de entrar no carrinho. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:32 — Staff bloqueia guest ordering sem fechar Tab nem impedir pedido interno. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:33 — Fechar a última Tab não libera a Table automaticamente. | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:34 — `release table` muda `OCCUPIED → DIRTY` e encerra a ocupação. | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:35 — Staff inicia limpeza `DIRTY → CLEANING`. | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:36 — Staff conclui limpeza `CLEANING → AVAILABLE`. | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:37 — Concluir limpeza incrementa `access_generation`. | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:38 — GuestSession de geração anterior não consegue criar novos pedidos. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:39 — Guest mantém Cardápio como home durante a sessão e consegue fazer vários pedidos. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:40 — Guest navega por Cardápio / Pedidos / Conta sem precisar entender estados internos do restaurante. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:41 — Guest vê status simplificado RECEBIDO / PREPARANDO / PRONTO-CHEGANDO derivado do fulfillment. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:42 — Guest consegue pedir novamente um item anterior ainda disponível. | IMPLEMENTED | `apps/api/modules/guest_access/{services,views}.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_guest_access.py; test_spec004_closeout.py; apps/web/tests/integration/guest-*.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:43 — Guest consegue criar solicitação estruturada de atendimento/conta que entra no Dispatch. | IMPLEMENTED | `apps/api/modules/dispatch/services.py; apps/web/components/guest-ordering.tsx` | `apps/api/tests/test_dispatch.py; apps/web/tests/integration/service-requests.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:44 — Guest pode assumir Tab por código curto. | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #146; não bloqueia MVP |
| acceptance.md:45 — Uma Tab pode receber e revogar associação NFC. | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #146; não bloqueia MVP |
| acceptance.md:46 — NFC pode ser reutilizado em outra Tab após revogação/fechamento. | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #146; não bloqueia MVP |
| acceptance.md:47 — Perfil Customer é opcional e pode ser ligado depois sem migrar a Tab. | DEFERRED | `— (não entregue)` | `—` | ausência auditada / contrato preservado | #147; não bloqueia MVP |
| acceptance.md:48 — Sistema registra timestamps para ocupação, liberação, início e fim da limpeza. | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:52 — Resposta perdida/reload retoma payload/chave originais sem duplicar Order/Charge/audit. | IMPLEMENTED | `apps/web/lib/client/guest-order-intent.ts; apps/api/modules/guest_access/services.py` | `apps/web/tests/{integration,visual}/guest-order-intent.spec.ts; apps/api/tests/test_guest_access.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:53 — Readback/duplo toque/contexto indisponível mantêm bloqueio até prova canônica. | IMPLEMENTED | `apps/web/lib/client/guest-order-intent.ts; apps/api/modules/guest_access/services.py` | `apps/web/tests/{integration,visual}/guest-order-intent.spec.ts; apps/api/tests/test_guest_access.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:54 — Sessão/Tab/ocupação/generation divergentes e revogação/bloqueio não adotam intenção. | IMPLEMENTED | `apps/web/lib/client/guest-order-intent.ts; apps/api/modules/guest_access/services.py` | `apps/web/tests/{integration,visual}/guest-order-intent.spec.ts; apps/api/tests/test_guest_access.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:55 — Storage inválido/falho impede POST; rejeição inicial segura permite revisão. | IMPLEMENTED | `apps/web/lib/client/guest-order-intent.ts; apps/api/modules/guest_access/services.py` | `apps/web/tests/{integration,visual}/guest-order-intent.spec.ts; apps/api/tests/test_guest_access.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:56 — Jornada real PostgreSQL, Web360/390/430, visual/build/tipos/lint/diff registrados. | IMPLEMENTED | `apps/web/lib/client/guest-order-intent.ts; apps/api/modules/guest_access/services.py` | `apps/web/tests/{integration,visual}/guest-order-intent.spec.ts; apps/api/tests/test_guest_access.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:61 — Mesa Web permite filtrar nome/número normalizado e escolher individualmente comandas vinculadas, inclusive fora da página de Contas. | IMPLEMENTED | `apps/web/components/attendance-web.tsx; apps/web/components/order-workspace.tsx; apps/api/modules/ordering/views.py` | `apps/web/tests/{integration,visual}/table-entry.spec.ts; apps/web/tests/integration/tab-location-move.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:62 — Abertura direta e retorno preservam filtro, foco, destino e rascunhos; falha mantém contexto anterior e bloqueios pendentes. | IMPLEMENTED | `apps/web/components/attendance-web.tsx; apps/web/components/order-workspace.tsx; apps/api/modules/ordering/views.py` | `apps/web/tests/{integration,visual}/table-entry.spec.ts; apps/web/tests/integration/tab-location-move.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:63 — GET contextual rejeita vínculo liberado/movido, ocupação liberada, mesa divergente, IDs inválidos e outro Venue; leitura não altera financeiro/histórico. | IMPLEMENTED | `apps/api/modules/hospitality/{models,services,table_service}.py` | `apps/api/tests/test_hospitality_tables.py; test_table_service.py; test_table_service_concurrency.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:68 — Revisão identifica mesa e efeito sobre QR/limpeza; cancelar não chama mutation. | IMPLEMENTED | `apps/attendance-android/app/src/main/java/com/rodada/attendance/operations/TablesScreen.kt` | `apps/attendance-android/app/src/androidTest/java/com/rodada/attendance/operations/TableReleaseTest.kt` | histórico Spec026 T07b/revalidation; Android não alterado nem reexecutado | critério local existente; integração/hardware permanece #106 |
| acceptance.md:69 — Alvo original preservado; mudança local de ocupação/generation, busy e permissão bloqueiam. | IMPLEMENTED | `apps/attendance-android/app/src/main/java/com/rodada/attendance/operations/TablesScreen.kt` | `apps/attendance-android/app/src/androidTest/java/com/rodada/attendance/operations/TableReleaseTest.kt` | histórico Spec026 T07b/revalidation; Android não alterado nem reexecutado | critério local existente; integração/hardware permanece #106 |
| acceptance.md:73 — Revisão atual por IDs/preço/configuração, sem defaults; cancelar preserva draft e inclusão não envia. | IMPLEMENTED | `apps/web/components/{guest-ordering,repeat-order}.tsx` | `apps/web/tests/{integration,visual}/guest-repeat-order.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:74 — Releitura impede visita/Tab/token divergentes e bloqueio/revogação/falha/conteúdo alterado; configuração distinta não se funde. | IMPLEMENTED | `apps/web/components/{guest-ordering,repeat-order}.tsx` | `apps/web/tests/{integration,visual}/guest-repeat-order.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:75 — PostgreSQL/Web em 360/390/430: nova intenção, resposta perdida/replay sem duplicação, histórico/Payments preservados; bloqueio de mesa após revisão impede inclusão. | IMPLEMENTED | `apps/web/components/{guest-ordering,repeat-order}.tsx` | `apps/web/tests/{integration,visual}/guest-repeat-order.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:80 — +/− acessíveis, zero remove, agrupamento por configuração idêntica e edição conserva quantidade; limite 99 rejeita inclusão/edição/repetição inteira sem perder draft. | IMPLEMENTED | `apps/web/components/guest-ordering.tsx` | `apps/web/tests/{integration,visual}/guest-quantity.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:81 — Variantes/opções/notas diferentes permanecem distintas, ordem de option IDs não cria configuração nova; controles e payload pendente preservados nos bloqueios. | IMPLEMENTED | `apps/web/components/guest-ordering.tsx` | `apps/web/tests/{integration,visual}/guest-quantity.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:82 — Web/API PostgreSQL 360/390/430: quantidade agrupada enviada uma vez, replay idêntico, exposição/charges corretos e Payments preservados; bloqueio real de mesa em 390. | IMPLEMENTED | `apps/web/components/guest-ordering.tsx` | `apps/web/tests/{integration,visual}/guest-quantity.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:83 — 385 testes visuais PASS (7,3 min), tipos/build/diff PASS; resultado final e limites em Spec 026/revalidation.md. | IMPLEMENTED | `specs/026-operational-ux-friction/revalidation.md` | histórico dos testes citado na Spec026 | snapshot histórico preservado, não total atual | ver gate atual abaixo, sem nova homologação |
| acceptance.md:86 — Busca global por nome, acentos/caixa/espaços nas bordas, categorias consistentes, retorno ao limpar, fallback e vazio; fixture de 146 produtos. | IMPLEMENTED | `apps/web/components/guest-ordering.tsx; apps/api/modules/guest_access/views.py` | `apps/web/tests/{integration,visual}/guest-catalog.spec.ts` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:87 — Filtros/atalho preservam configuração, quantidade, draft e intent; indisponibilidade, bloqueio e revogação respeitados; primeira inclusão não desloca catálogo. | IMPLEMENTED | `apps/web/components/guest-ordering.tsx; apps/api/modules/guest_access/views.py` | `apps/web/tests/{integration,visual}/guest-catalog.spec.ts; apps/api/tests/test_guest_access.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:88 — Web/API PostgreSQL 360/390/430: categoria real, seleção cruzando filtros, bloqueio de mesa, foco/draft e replay sem duplicar Order/Charge. | IMPLEMENTED | `apps/web/components/guest-ordering.tsx; apps/api/modules/guest_access/views.py` | `apps/web/tests/{integration,visual}/guest-catalog.spec.ts; apps/api/tests/test_guest_access.py` | suite PostgreSQL / Web do SHA; ver gates abaixo | MVP; manter/reconciliar checkbox |
| acceptance.md:89 — 393 testes visuais PASS (7,6 min), Ruff/tipos/build/diff PASS; detalhes na Spec 026. Não implica paridade global, aparelho físico ou publicação. | IMPLEMENTED | `specs/026-operational-ux-friction/revalidation.md` | histórico dos testes citado na Spec026 | snapshot histórico preservado, não total atual | ver gate atual abaixo, sem nova homologação |

Os totais 318/385/393 e limites citados em critérios importados são snapshots
históricos preservados de Spec026/revalidation.md, não contagem do gate atual.
A execução deste fechamento está separada abaixo.

## Gaps reais desta entrega

Navegação Guest antes: somente regiões na página sem atalhos persistentes.
Depois: Cardápio/Pedidos/Conta rolam/focalizam regiões montadas, preservam draft
/intenção e não enviam mutation. Reutiliza tokens e padrão de regiões da produção.
Antes: NEW/ACCEPTED/PICKED_UP expostos como microestados. Depois: projeção pública
Recebido/Preparando/Pronto-chegando, com Entregue/Cancelado apenas por fato canônico
e fallback explícito desconhecido. Não altera fulfillment nem financeiro.

## Evidências e gates

Revisão visual: capturas da mesma fixture (Table24, uma Tab, Fritas em PREPARING,
draft1×) na base d5acc98 e no patch, Chromium153, em360/390/430/1280.
Par mobile360 preservado em docs/evidence/spec004/guest-{before,after}-360.png.
Captura real desktop em guest-real-1280.png. Revisão manual mostrou os atalhos
novos e tradução de Em preparo→Preparando; layout/tokens adjacentes preservados.
Capturas fixture não são prova E2E; o desktop real é BFF/Django/PostgreSQL.


Inventário reconciliado: **tasks 46 concluídas / 30 roadmap**, **acceptance 50
aprovados / 11 roadmap**. Matriz completa: 96 IMPLEMENTED / 41 DEFERRED;
nenhum MISSING_MVP remanescente nem critério OBSOLETE apagado.

Execuções locais em PostgreSQL16.2 descartável, CPython3.12.14, Node24.19.0,
Next16.3.8, Playwright1.58.2 e Chromium153.0.8010.0:

| Gate | Comando | Resultado |
| --- | --- | --- |
| Django | `python manage.py check --settings=rodada_api.settings` | PASS, 0 issues |
| Drift | `python manage.py makemigrations --check --dry-run --settings=rodada_api.settings` | PASS, No changes detected |
| API PostgreSQL | `pytest --ds=rodada_api.settings tests/test_spec004_closeout.py tests/test_guest_concurrency.py tests/test_guest_access.py tests/test_hospitality_tables.py tests/test_table_service.py tests/test_table_service_concurrency.py tests/test_global_guest_block.py tests/test_full_shift_smoke.py tests/test_venue_hostnames.py tests/test_order_intent_concurrency.py tests/test_dispatch.py` | 76 PASS (49.41s), 0 skips |
| Web | `npm run typecheck`; `npm run build` | PASS |
| Unitários Web | `npm run test:auth`; `test:tenant`; `test:identity`; `test:table-service`; `node --experimental-strip-types --test tests/guest-status.test.mjs` | 4+3+3+1+1 PASS |
| Lint | `check_added_lines.py` por kind `api`, `eslint`, `web`, base `d5acc98` (comandos completos abaixo) | API 0 findings; ESLint 0 novos/fatais (22 erros/2 warnings preexistentes); Web safety 0 findings |
| Web real | `npm run test:integration -- guest-navigation.spec.ts guest-order-intent.spec.ts guest-repeat-order.spec.ts guest-quantity.spec.ts guest-catalog.spec.ts table-entry.spec.ts service-requests.spec.ts attendance.spec.ts` | 21 PASS (2.1m), BFF/Django/PostgreSQL, 360/390/430 e desktop1280 |
| Workflow/status customizado | `npm run test:integration -- workflows.spec.ts z-customization.spec.ts` e reexecução `-- z-customization.spec.ts` após filtrar redirect307/308 | 6 workflows PASS + 1 customization PASS; estado NEW/READY e preço2800 continuam asserted |
| Intent + navegação | `npm run test:integration -- guest-order-intent.spec.ts` | 4 PASS (28.7s); envelope/chave/payload e ausência de duplicação após navegar/reload |
| Visual/a11y | `npm run test:visual` | 525 PASS (10.6m); sem atualizar baseline/tolerância |

Variáveis de teste: `RODADA_E2E_POSTGRES=1`, `POSTGRES_DB=rodada_web_e2e`,
`POSTGRES_HOST=127.0.0.1`, `POSTGRES_PORT=55484`, `POSTGRES_USER=rodada`,
`RODADA_TEST_PYTHON=<venv>/bin/python`. API usa DB `rodada` local e pytest cria
`test_rodada`; nenhuma base remota. Cluster isolado inclui ajuste local de
ownership para namespace de UID único; testes continuam em PostgreSQL real.
Gates CI do HEAD do PR150 são a prova reproduzível no PostgreSQL17/Chromium145.

Fonte do produto testada: commit remoto82870bb / tree1fc8face, equivalente ao
local48a5f2e. Ajustes posteriores são testes, matriz/evidência, sem alterar produto.
CI final e revisão independente são vinculadas ao HEAD do PR150; o comentário
final do PR/issue registra seu SHA exato e commit de merge.

Falhas registradas: tentativas iniciais de infra local sem PostgreSQL alcançável
não contam como PASS. Instalação padrão do browser falhou; Chromium via pacote
isolado resolveu. Segundo start da base E2E já preenchida falhou em slug duplicado;
reexecução com base descartável nova passou. CI Web inicial82870bb teve 93 PASS /
2 FAIL por expectativas antigas Confirmado/Pronto; atualizadas para Recebido/
Pronto-chegando, adicionando asserts canônicos NEW/READY e preço2800. Nada foi
relaxado em domínio, mocks, permissões ou financeiro.

Revisão independente `/root/review_spec004`: P1 foco no catálogo e P2 placement/
quick-add identificados e corrigidos; pointers e Table sem placement reconciliados.
Não constitui aprovação GitHub. Registro final de revisão pelo SHA no PR150.

Limites: nenhuma mutation de piloto/Railway, nenhum Android alterado, nenhum
PSP/NFC/fiscal/rede real homologado. Rate limit é baseline por processo/IP, não
throttle distribuído comprovado. QR físico permanece válido para nova visita;
a sessão da visita antiga é revogada, não o token permanente inteiro.


Comandos exatos dos gates de lint (raiz):
```sh
python scripts/quality/check_added_lines.py --kind api --base d5acc98
python scripts/quality/check_added_lines.py --kind eslint --base d5acc98
python scripts/quality/check_added_lines.py --kind web --base d5acc98
```
CI inicial API do82870bb:731 PASS (608.73s), PostgreSQL17.11. Web inicial teve
2 expectativas obsoletas de rótulo, corrigidas mantendo assert canônico. Nos testes
novos, resposta de redirect308 não é confirmação; matcher acompanha endpoint
com ou sem barra e exige201 final, sem aceitar400/403/409/5xx como sucesso.
