#!/usr/bin/env bash
# End-to-end pilot rehearsal: create representative facts, back up, restore to
# a genuinely separate database, then verify history and run the smoke path.
set -euo pipefail

: "${RODADA_RESTORE_DB:?Set RODADA_RESTORE_DB to a disposable fresh database name}"

python manage.py migrate --noinput
python manage.py seed_restore_rehearsal --venue-slug "${RODADA_REHEARSAL_VENUE_SLUG:-restore-rehearsal}"
backup_file="$(./scripts/backup_postgres.sh)"
RODADA_RESTORE_DB="$RODADA_RESTORE_DB" ./scripts/restore_postgres_fresh.sh "$backup_file"
RODADA_RESTORE_DB="$RODADA_RESTORE_DB" ./scripts/verify_restore.sh
