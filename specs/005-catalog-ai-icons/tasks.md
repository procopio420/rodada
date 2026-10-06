# Tasks — Spec 005

## Catalog/API

- [ ] ProductIcon model/reference
- [ ] source/status enums
- [ ] published icon invariant
- [ ] placeholder fallback
- [ ] quick-create Product command
- [ ] inherit FulfillmentStation from station context
- [ ] permissions for station quick create
- [ ] CatalogIconGenerator port
- [ ] provider adapter
- [ ] style contract version field
- [ ] generation request idempotency
- [ ] generation rate limit
- [ ] storage/CDN integration
- [ ] upload validation
- [ ] audit generation/regeneration/publish/upload/remove

## Staff / Bar / Kitchen

- [ ] **+ Item** action
- [ ] compact name + price form
- [ ] station prefilled
- [ ] category/description optional
- [ ] Generate icon with AI toggle/action
- [ ] generating state + placeholder
- [ ] preview
- [ ] regenerate
- [ ] publish generated asset
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
- [ ] duplicate generation command is idempotent
- [ ] regeneration preserves currently published icon
- [ ] failed generation preserves Product and ordering
- [ ] unauthorized station cannot create/manage another station's products
- [ ] uploaded invalid MIME/dimensions rejected
- [ ] Customer/Tab/Order data never enters generation payload
- [ ] all surfaces resolve the same published asset
