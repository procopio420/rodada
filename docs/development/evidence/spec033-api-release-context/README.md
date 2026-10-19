# E04/E06 canonical release occupancy fence

Source `ebd22333` requires the originally confirmed occupancy UUID and generation in the release endpoint and domain service. `a7e9c4ae` strengthens a pre-existing claim replay assertion; production release code is unchanged by that test correction.

Disposable PostgreSQL 17.6 on 127.0.0.1:55642, database `rodada_release_test` and Django-created test database. No shared runtime or production data touched. Command (apps/api):

```sh
POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=55642 POSTGRES_USER=rodada POSTGRES_DB=rodada_release_test python -m pytest tests/test_table_release_context.py tests/test_hospitality_tables.py tests/test_table_service_concurrency.py tests/test_party_size.py tests/test_tab_location_safety.py tests/test_table_service.py tests/test_full_shift_smoke.py --ds=rodada_api.settings --reuse-db -o addopts='' -q
```

Result: **54 passed in 78.28 seconds**, no skips. Includes five new context tests, real PostgreSQL release/open and cleaning races, Guest revocation, lifecycle, party size, location safety and full-shift financial regression. Django system check and migration drift check passed; focused service/serializer/new-test Ruff passed. Existing view/class Ruff baseline warnings were not suppressed or altered. Python scripts were updated to supply captured context; destructive reset scripts were not executed.

Independent root R3: NO_FINDINGS_WITH_GAPS (review.md). Required client adoption and CI remain integration gates; omitting context now returns 400. No release idempotency, PSP, physical-device or pilot acceptance is claimed. No merge/deploy.
