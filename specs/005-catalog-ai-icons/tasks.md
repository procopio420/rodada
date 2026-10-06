# Tasks — Spec 005

## Catalog/API

- [ ] ProductIcon stable 1:1 model/reference
- [ ] create ProductIcon shell with every new Product
- [ ] source/status enums
- [ ] published icon invariant
- [ ] placeholder fallback
- [ ] normalized Product name/search key per Venue
- [ ] product autocomplete/suggest query
- [ ] resolve-or-create Product command
- [ ] DB/transaction guard against exact normalized-name races
- [ ] inherit FulfillmentStation from station context
- [ ] permissions for station quick create
- [ ] CatalogIconGenerator port
- [ ] provider adapter
- [ ] style contract version field
- [ ] automatic generation enqueue on Product create
- [ ] content/style fingerprint for generation deduplication
- [ ] generation request idempotency
- [ ] generation rate limit
- [ ] storage/CDN integration
- [ ] upload validation
- [ ] audit generation/regeneration/publish/upload/remove

## Staff / Bar / Kitchen

- [ ] **+ Item** action
- [ ] Product name typeahead/autocomplete
- [ ] existing result row with icon + price + station + availability
- [ ] **Criar "{nome}"** fallback when no exact match
- [ ] selecting existing Product never duplicates it
- [ ] compact price form only when creating a new Product
- [ ] station prefilled for new Product
- [ ] category/description optional
- [ ] no generate button/toggle in quick-create flow
- [ ] automatic generating state + placeholder after create
- [ ] automatic publish of first generated asset
- [ ] preview in edit/detail
- [ ] secondary regenerate action only in advanced edit/review
- [ ] upload manual asset
- [ ] remove/reset to placeholder

## Guest

- [ ] render published ProductIcon
- [ ] graceful placeholder
- [ ] no guest dependency on generation status

## Design system

- [ ] define Rodada icon style v1
- [ ] square/safe-area contract
- [ ] transparent-background preference
- [ ] no-text/no-logo rule
- [ ] small-size legibility check
- [ ] shared ProductIcon component across catalog surfaces

## Quality

- [ ] Product saves when AI provider is unavailable
- [ ] autocomplete exact match prevents obvious duplicate Product
- [ ] concurrent resolve-or-create yields one Product
- [ ] fuzzy suggestion never silently merges Products
- [ ] duplicate/automatic generation command is idempotent
- [ ] unchanged generation fingerprint does not create duplicate assets
- [ ] regeneration preserves currently published icon
- [ ] failed generation preserves Product and ordering
- [ ] unauthorized station cannot create/manage another station's products
- [ ] uploaded invalid MIME/dimensions rejected
- [ ] Customer/Tab/Order data never enters generation payload
- [ ] rename/price/availability changes preserve the ProductIcon 1:1 identity
- [ ] all surfaces and autocomplete resolve the same published asset
