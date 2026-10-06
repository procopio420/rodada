# Plan — Spec 004

## Slice 1 — Table + Occupancy

- Table e estados;
- TableOccupancy;
- associação de múltiplas Tabs;
- release table;
- limpeza;
- access_generation;
- métricas/timestamps.

## Slice 2 — QR + GuestSession

- token opaco da Table;
- endpoint de resolução;
- PWA guest;
- sessão anônima;
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
