# Plan — Spec 004

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
