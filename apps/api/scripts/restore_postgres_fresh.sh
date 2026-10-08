#!/usr/bin/env bash
# Restore a custom-format backup into an explicitly fresh database. Never use
# this for the live/source database: the target is dropped before restoration.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: RODADA_RESTORE_DB=<fresh-db> $0 path/to/backup.dump" >&2
  exit 64
fi

: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${RODADA_RESTORE_DB:?RODADA_RESTORE_DB must name a fresh restore target}"

backup_file="$1"
[[ -f "$backup_file" ]] || { echo "Backup file not found: $backup_file" >&2; exit 66; }
[[ "$RODADA_RESTORE_DB" != "$POSTGRES_DB" ]] || {
  echo "Refusing to restore over POSTGRES_DB ($POSTGRES_DB). Choose a different RODADA_RESTORE_DB." >&2
  exit 64
}

for command in dropdb createdb pg_restore; do
  command -v "$command" >/dev/null || {
    echo "$command was not found. Install PostgreSQL client tools before restoring." >&2
    exit 127
  }
done

export PGHOST="${POSTGRES_HOST:-localhost}"
export PGPORT="${POSTGRES_PORT:-5432}"
export PGUSER="$POSTGRES_USER"
export PGPASSWORD="${POSTGRES_PASSWORD:-}"

# The target must be disposable. --if-exists keeps a first rehearsal safe;
# no source database is ever named here.
dropdb --if-exists "$RODADA_RESTORE_DB"
createdb "$RODADA_RESTORE_DB"
pg_restore --no-owner --no-privileges --dbname="$RODADA_RESTORE_DB" "$backup_file"
echo "Restored $backup_file into fresh database $RODADA_RESTORE_DB"
