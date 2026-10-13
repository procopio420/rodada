---
name: rodada-django-api
description: Use when implementing or reviewing Django 5.2, Django REST Framework, PostgreSQL, migrations, permissions or domain services in apps/api of Rodada.
---

# Django / DRF — Rodada API

## Activate for
Changes under `apps/api/**`, DRF endpoints, Django ORM, PostgreSQL migrations, auth/capabilities, financial services, outbox and concurrent domain commands. This is a task-specific **procedure**, not a replacement for [API AGENTS](../../../apps/api/AGENTS.md).

## Before modifying
1. Identify the full spec directory (numbers alone can collide), its `spec.md` and `acceptance.md`. Read [domain ownership](../../../docs/architecture/overview.md) and [domain model](../../../docs/domain/model.md).
2. Locate the existing module's models/services/selectors/API/tests. Prefer extending a bounded domain service over duplicating business rules in a serializer or view.
3. Confirm whether the operation touches `Venue` isolation, staff capability, GuestSession, financial ledger, order confirmation, table occupancy, realtime or a payment provider.

## Implementation checklist
- Django/DRF serves as the authority for scoped reads and mutations; client-supplied headers, Host, UUIDs or `venue_slug` cannot broaden access.
- Write monetary amounts as integer cents. Make financial effects transactional, idempotent, append-only and auditable; model unknown/pending provider state separately from settled money.
- Use `transaction.atomic` and appropriate row locks/constraints where invariants require concurrency safety; never rely on SQLite to prove PostgreSQL locking.
- Preserve Order → Tab, occupancy separate from Tab, availability revalidated on confirmation, and existing OrderItems when a product becomes unavailable.
- A timeout after commit is *ambiguous*: reconcile by original immutable intent/idempotency key and canonical readback. Duplicate webhook, double submit and retries must be harmless.
- Add an audit trail (actor, timestamp, previous/new state/reason when applicable), permissions and cross-Venue negative tests with each privileged mutation.
- Review database migrations for reversible/compatible rollout; never run migrations, fixture reset or seed against shared demo/production without explicit approval.

## Test and handoff
In an isolated PostgreSQL test environment:
```sh
cd apps/api
python manage.py check --settings=rodada_api.settings
python manage.py makemigrations --check --dry-run --settings=rodada_api.settings
pytest --ds=rodada_api.settings
```
Run focused regressions first; report executed commands and their SHA, skips and failures. An API PASS is not an on-site/payment-provider acceptance. Consult [procedures](../../../docs/agents/PROCEDURES.md).
