# Quick Catalog runtime

Spec: `specs/005-catalog-ai-icons/`.

Run migrations, then supervise a separate worker:

```sh
python manage.py migrate
python manage.py process_icon_jobs
```

Products, availability, icon shells and pending jobs commit together. Provider calls run in the worker, outside that transaction. Jobs have five-minute leases, stable provider idempotency keys and three attempts with exponential backoff. A revision fence protects manual uploads/removal from older results. Products remain sellable throughout failures.

## Providers

Direct OpenAI Image API:

```sh
RODADA_ICON_PROVIDER=openai
OPENAI_API_KEY=<secret>
RODADA_ICON_PROVIDER_MODEL=<image model available to your account>
```

The adapter uses the official [Image API contract](https://developers.openai.com/api/docs/guides/image-generation), requests one transparent 1024×1024 PNG, and records model/provider/usage. Live generation and visual style approval require credentials and account access; CI fixtures are never runtime fallback imagery.

Alternatively set `RODADA_ICON_PROVIDER=http`, `RODADA_ICON_PROVIDER_URL=https://...`, `RODADA_ICON_PROVIDER_KEY`, and `RODADA_ICON_PROVIDER_MODEL`. The gateway receives JSON `product_context`, `prompt`, `style_version`, `model`, `size`, `background`; returns `image_base64`, `provider`, `model`, optional `usage`. It must honor the `Idempotency-Key` header to prevent repeated provider billing after network ambiguity.

Provider input is limited to product name, description, category and station plus the versioned style contract. Customer, Tab, Order, Venue and staff information never enters this payload. Exception messages are not persisted.

## Storage and access

Set `RODADA_ASSET_ROOT` to a persistent shared volume accessible to API and worker. Django's `default_storage` can instead be configured with an object-storage backend. Assets are decoded/validated and normalized to PNG, then served by immutable opaque published-asset URLs. Next's same-origin public binary gateway lets Guest and Staff resolve the identical asset without exposing credentials. Placeholder SVG is UI code, not a generated asset.

Upload limits: PNG/JPEG/WebP, square 128–2048 px, maximum 5 MB. SVG and MIME mismatches are rejected. Previous generation revisions remain in storage for traceability; only the current published path is retrievable through the public endpoint.

## Permissions and API

Manager/Owner receive `catalog.create.bar`, `catalog.create.kitchen`, `catalog.icon.manage`. Give station operators explicit membership capability `allow` overrides for their station. Neither client station context nor a request field grants permission.

- GET `/catalog/suggestions/?q=...`: venue-scoped exact, partial and bounded fuzzy suggestions, including inactive exact matches.
- POST `/catalog/resolve-or-create/`: name, integer price_cents, fulfillment_station; optional description/category. Exact normalized matches retain configuration and availability.
- PATCH `/catalog/products/{id}/`: authorized management edits preserve icon identity.
- POST `/catalog/products/{id}/icon/`: action regenerate (idempotency_key), upload (image_base64/mime), or remove.

Normalization uses Unicode compatibility folding, casefold, accent removal and whitespace collapse. Migration 0005 stops on existing accent collisions and requires explicit renaming; it never merges products or historical orders.

Manager generation requests are capped at 20/operator/hour and 60/venue/hour. Automatic generation starts are capped at 60/venue/hour and excess work remains queued. Run `process_icon_jobs --once` for one worker iteration.
