# Tasks — Spec 004

## API/Domain

- [x] Table model + status
- [ ] FloorPlan model + guest/staff projections
- [ ] TablePlacement model + active-placement invariant
- [ ] normalized x/y coordinates + placement history
- [ ] optimistic locking/version on placement mutation
- [ ] TableGroup temporary grouping
- [x] TableOccupancy model + invariants
- [ ] TablePlacement ↔ ServicePoint/Zone integration
- [x] Tab ↔ TableOccupancy optional association
- [x] enforce multiple Tabs per occupancy
- [x] release table service
- [x] cleaning start/complete services
- [x] increment `access_generation` on cleaning completion
- [ ] GuestSession model
- [ ] TabIdentifier model
- [x] opaque Table public token
- [ ] short code identifier
- [ ] dynamic Tab QR identifier
- [ ] NFC_TAG association/revocation
- [ ] guest ordering modes
- [ ] guest block/unblock
- [ ] server-side generation validation
- [ ] rate limiting
- [x] audit events
- [ ] metrics queries

## Guest PWA

- [ ] resolve QR
- [ ] table context screen
- [ ] sanitized 2D floorplan
- [ ] "Onde vocês estão?" placement flow for unplaced Table
- [ ] handle placement conflict/stale version
- [ ] create anonymous/named Tab
- [ ] join existing Tab by short code
- [ ] optional login/profile path
- [ ] menu/catalog consumindo disponibilidade operacional compartilhada
- [ ] item indisponível visualmente desabilitado
- [ ] tratamento de carrinho stale quando disponibilidade muda antes do submit
- [ ] add item / notes
- [ ] submit order
- [ ] persistent navigation: Cardápio / Pedidos / Conta
- [ ] quick-add item; modifiers only when required
- [ ] live order summary
- [ ] simplified guest order status
- [ ] reorder previous available items
- [ ] structured service/bill requests to Dispatch
- [ ] tab total / own-part projection when available
- [ ] show dynamic Tab QR

## Staff Web

- [ ] 2D floor canvas with movable Table markers
- [ ] place previously unplaced Table
- [ ] clear placement when Table is physically removed/stored
- [ ] drag/reposition active Table without touching occupancy/tab
- [ ] create/dissolve TableGroup
- [ ] table board: AVAILABLE / OCCUPIED / DIRTY / CLEANING / OUT_OF_SERVICE
- [ ] occupancy detail with multiple Tabs
- [ ] release table
- [ ] start cleaning
- [ ] mark clean/available
- [ ] guest ordering block toggle
- [ ] associate/move Tab
- [ ] issue/revoke NFC tag
- [ ] show/copy short code

## Quality

- [ ] cannot order against sequential/raw table id
- [ ] old GuestSession rejected after occupancy release/generation change
- [ ] guest block rejects guest mutation but staff still orders
- [ ] two Tabs on same occupancy remain financially independent
- [x] closing last Tab does not release table
- [ ] cleaning timestamps produce deterministic metrics
- [ ] NFC reassignment revokes previous association
- [ ] moving a Table preserves occupancy, Tabs, Orders, ledger and QR
- [ ] guest floorplan does not expose internal operational state
- [ ] concurrent placement update rejects stale version
- [ ] grouping Tables never merges financial identity
- [ ] rate limit tests
- [x] authorization tests
