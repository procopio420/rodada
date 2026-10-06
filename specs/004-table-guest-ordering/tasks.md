# Tasks — Spec 004

## API/Domain

- [ ] Table model + status
- [ ] TableOccupancy model + invariants
- [ ] Table ↔ ServicePoint/Zone integration
- [ ] Tab ↔ TableOccupancy optional association
- [ ] enforce multiple Tabs per occupancy
- [ ] release table service
- [ ] cleaning start/complete services
- [ ] increment `access_generation` on cleaning completion
- [ ] GuestSession model
- [ ] TabIdentifier model
- [ ] opaque Table public token
- [ ] short code identifier
- [ ] dynamic Tab QR identifier
- [ ] NFC_TAG association/revocation
- [ ] guest ordering modes
- [ ] guest block/unblock
- [ ] server-side generation validation
- [ ] rate limiting
- [ ] audit events
- [ ] metrics queries

## Guest PWA

- [ ] resolve QR
- [ ] table context screen
- [ ] create anonymous/named Tab
- [ ] join existing Tab by short code
- [ ] optional login/profile path
- [ ] menu/catalog
- [ ] add item / notes
- [ ] submit order
- [ ] order status
- [ ] tab total
- [ ] show dynamic Tab QR

## Staff Web

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
- [ ] closing last Tab does not release table
- [ ] cleaning timestamps produce deterministic metrics
- [ ] NFC reassignment revokes previous association
- [ ] rate limit tests
- [ ] authorization tests
