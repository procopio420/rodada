# Tasks — Spec 005

## Catalog/API

- [x] ProductIcon stable 1:1 model/reference
- [x] create ProductIcon shell with every new Product
- [x] source/status enums
- [x] published icon invariant
- [x] placeholder fallback
- [x] normalized Product name/search key per Venue
- [x] product autocomplete/suggest query
- [x] resolve-or-create Product command
- [x] DB/transaction guard against exact normalized-name races
- [x] inherit FulfillmentStation from station context
- [x] permissions for station quick create
- [x] CatalogIconGenerator port
- [x] provider adapter
- [x] style contract version field
- [x] automatic generation enqueue on Product create
- [x] content/style fingerprint for generation deduplication
- [x] generation request idempotency
- [x] generation rate limit
- [x] storage/CDN integration
- [x] upload validation
- [x] audit generation/regeneration/publish/upload/remove

## Staff / Bar / Kitchen

- [x] **+ Item** action
- [x] Product name typeahead/autocomplete
- [x] existing result row with icon + price + station + availability
- [x] **Criar "{nome}"** fallback when no exact match
- [x] selecting existing Product never duplicates it
- [x] compact price form only when creating a new Product
- [x] station prefilled for new Product
- [x] category/description optional
- [x] no generate button/toggle in quick-create flow
- [x] automatic generating state + placeholder after create
- [x] automatic publish of first generated asset
- [x] preview in edit/detail
- [x] secondary regenerate action only in advanced edit/review
- [x] upload manual asset
- [x] remove/reset to placeholder

## Guest

- [x] render published ProductIcon
- [x] graceful placeholder
- [x] no guest dependency on generation status

## Design system

- [x] define Rodada icon style v1
- [x] square/safe-area contract
- [x] transparent-background preference
- [x] no-text/no-logo rule
- [ ] small-size legibility check
- [x] shared ProductIcon component across catalog surfaces

## Quality

- [x] Product saves when AI provider is unavailable
- [x] autocomplete exact match prevents obvious duplicate Product
- [x] concurrent resolve-or-create yields one Product
- [x] fuzzy suggestion never silently merges Products
- [x] duplicate/automatic generation command is idempotent
- [x] unchanged generation fingerprint does not create duplicate assets
- [x] regeneration preserves currently published icon
- [x] failed generation preserves Product and ordering
- [x] unauthorized station cannot create/manage another station's products
- [x] uploaded invalid MIME/dimensions rejected
- [x] Customer/Tab/Order data never enters generation payload
- [x] rename/price/availability changes preserve the ProductIcon 1:1 identity
- [x] all surfaces and autocomplete resolve the same published asset
