# Plan — Spec 004

T06d Web continuation reuses MOVE_LOCATION of Spec009, occupied destinations,
contextual Tab read and existing tokens/dialogs. Preserve origin occupancy and
guest context. Validate immutable intent/replay and financial snapshots in
disposable PostgreSQL, mobile 360/390/430 and complete visual regression.

## Slice 1 — Table + Floor + Occupancy

- Table e estados;
- FloorPlan;
- TablePlacement com coordenadas normalizadas e histórico;
- mesa sem placement como estado válido;
- posicionamento/movimento por staff;
- TableOccupancy;
- associação de múltiplas Tabs;
- release table;
- limpeza;
- access_generation;
- métricas/timestamps.

## Slice 2 — QR + GuestSession + Placement guest

- token opaco da Table;
- endpoint de resolução;
- PWA guest;
- sessão anônima;
- floorplan sanitizado para guest;
- posicionamento de Table sem placement pelo guest;
- concorrência/versionamento de placement;
- modos `DISABLED | JOIN_ACTIVE | DIRECT`.

## Slice 3 — Guest Tab + Order

- criar Tab pelo guest;
- join por código curto;
- Order `source=GUEST`;
- mesma pipeline de fulfillment.

## Slice 4 — Controle operacional

- bloquear/desbloquear guest ordering;
- revogação por occupancy/generation;
- rate limit;
- auditoria;
- canvas 2D staff com drag/reposition;
- agrupamento visual/operacional de mesas;
- UX de staff para estados da mesa.

## Slice 5 — Identificadores adicionais

- QR dinâmico de Tab;
- associação/revogação NFC;
- profile/Customer claim;
- device session persistente.

## Slice 6 — Métricas

- ocupação;
- espera para limpeza;
- duração da limpeza;
- giro;
- volume guest vs staff.


## Slice 7 — Guest experience contínua

- navegação `Cardápio | Pedidos | Conta`;
- quick-add e modificadores somente quando necessários;
- live order summary;
- status guest simplificado;
- pedir novamente;
- solicitações estruturadas de atendimento integradas ao Dispatch.

Round 2: usar DispatchTask existente para chamadas SERVICE_REQUEST/BILL_REQUEST;
API guest autorizada pela sessão original da ocupação, UUID retry-safe, botões
acessíveis na home e teste navegador com backend/PostgreSQL reais.

## T05b — plano mínimo

Acrescentar scope não secreto ao contexto existente; hook guest preserva
intenção usando a credencial já gerida pelo fluxo, sem duplicá-la. Reutilizar
confirm_guest_order e seu replay. Cobrir reload/resposta perdida/readback,
contexto divergente/revogação/bloqueio/storage, Web360/390/430 e PostgreSQL.
Executar visual completo, build/tipos e lint dos arquivos Python alterados.

### T06c
Reutilizar TableOccupancy/TabOccupancyAssignment e detalhe autorizado de Tab; acrescentar precondição opcional de contexto ao GET existente, sem novos locks ou mutations. Listagem de ocupação filtra vínculos liberados. AttendanceWeb preserva contexto de retorno e solicita seleção ao workspace já montado, reutilizando seleção serializada e rascunhos por Tab. Validar múltiplas comandas, conflito/vínculo antigo, outro Venue, falha/retry, pendência, foco/retorno e Web/API 360/390/430.

### T07b — confirmação de liberação Android
TablesScreen captura mesa/ocupação/generation ao abrir revisão, informa revogação QR e estado de limpeza e só chama o callback após confirmar. Revalida inventário local, permissão e busy; API permanece com contrato existente. Testar cancelamento sem callback, confirmação única e contexto alterado em Compose; regressões PostgreSQL de mesas/guest/ledger.

### T08c — repetição guest
Reutilizar reviewRepeatedOrder/RepeatOrderDialog, adaptando o catálogo guest ativo
à disponibilidade operacional. Ler contexto e catálogo ao abrir e ao incluir;
comparar token, scope, Tab e conteúdo completo da revisão. Projetar
guest_policy.table_ordering_enabled a partir da mesa já autorizada/locked.
Inclusão somente local, única e preservando linhas anteriores; envio e replay
reutilizam a intenção T05b. Validar fixtures adversariais, mobile, jornada real
em PostgreSQL, bloqueios e preservação do histórico. Não alterar mutations ou
regras financeiras.

### T09a — quantidade e agrupamento guest
Agrupar localmente Product/variant/options/note idênticos, preservando unidades
na edição e repetição. Validar o resultado inteiro antes de substituir o draft;
limite 99 sem truncamento. Reutilizar grid/controles de quantidade existentes e
feedback acessível. Alterações de quantidade não modificam intenções pendentes.
Cobrir configuração distinta e ordem de opções, notas exatas, limite de inclusão/
edição/repetição, dados obsoletos, disponibilidade, bloqueios e jornadas reais em
PostgreSQL 360/390/430 com resposta perdida e replay. Sem regra/API nova.

### T09b — descoberta guest
Reutilizar helpers de busca/categoria do Atendimento e Product.category projetada
pela leitura guest. Filtrar apenas exibição; catálogo completo conserva revisão
por IDs, quantidades e seleção. Todos inicial, busca global, categoria ao limpar,
fallback quando removida e contagem/vazio. Acesso Pedido atual fica estável mesmo
vazio e foca o draft. Ensaiar 146 produtos (143 CSV + três fixtures existentes),
configuração, bloqueios/atualização/revogação/intent, Web/API PostgreSQL em três
larguras e visual completo, sem modificar referências ou tolerâncias.

## Fechamento MVP 14/10/2026

Executar matriz closeout.md, patch mínimo Guest navegação/status, regressões
negativas PostgreSQL, Web real BFF/API/PostgreSQL e visual proporcional.
Slices de mapa/grupos/identificadores/perfil/relatórios permanecem #144–#148;
checklists originais preservadas. Revisão independente antes do merge; #106
continua responsável pelo turno integrado Web+Android.

## Gestão de mesas
Contrato: [management-tables.md](management-tables.md). Implementar serviço transacional de quantidade/estado, API protegida, tela dedicada e testes PostgreSQL/mobile. Recorte implementado e validado localmente; evidência e limites em [management-tables-evidence.md](management-tables-evidence.md).

## Execução isolada #145 — agrupamentos sem FloorPlan

Adicionar `TableGroup` e `TableGroupMembership` no bounded context hospitality com migration `0006_table_groups`. Constraints PostgreSQL para chave de replay e exclusividade de membro ativo, lock ordenado das Tables. API `TABLE_MANAGE` para listar/criar/desfazer; alterações auditadas e reconsultadas. Projetar grupos na lista de mesas/Guest sanitizado, incorporar as ações na Gestão de Mesas reutilizando componentes existentes. Não alterar entidades financeiras nem depender da #144.

Aceite exige PostgreSQL real para concorrência, permissões, lifecycle/ledger imutáveis, Web visual mobile/desktop, BFF integrado, migration dry-run, CI final e code review R3 independente.
