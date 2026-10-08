#!/usr/bin/env bash
# Verify a previously restored rehearsal database and execute the canonical
# smoke test against the same PostgreSQL server configuration.
set -euo pipefail

: "${RODADA_RESTORE_DB:?RODADA_RESTORE_DB must name the restored database}"
: "${POSTGRES_DB:?POSTGRES_DB is required so accidental source verification can be refused}"

[[ "$RODADA_RESTORE_DB" != "$POSTGRES_DB" ]] || {
  echo "Refusing to verify the source database. RODADA_RESTORE_DB must be different from POSTGRES_DB." >&2
  exit 64
}

export POSTGRES_DB="$RODADA_RESTORE_DB"
python manage.py migrate --noinput
python manage.py check
python manage.py verify_restore --venue-slug "${RODADA_REHEARSAL_VENUE_SLUG:-restore-rehearsal}"
# pytest creates an isolated test database on this PostgreSQL server. It proves
# the restored server can run the canonical end-to-end path without touching
# the restored records verified immediately above.
pytest --ds=rodada_api.settings tests/test_full_shift_smoke.py
