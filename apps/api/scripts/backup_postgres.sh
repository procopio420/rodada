#!/usr/bin/env bash
# Create a portable PostgreSQL custom-format backup of the configured Rodada DB.
set -euo pipefail

: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"

command -v pg_dump >/dev/null || {
  echo "pg_dump was not found. Install PostgreSQL client tools before backing up." >&2
  exit 127
}

backup_dir="${RODADA_BACKUP_DIR:-$PWD/backups}"
mkdir -p "$backup_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_file="$backup_dir/rodada-${POSTGRES_DB}-${timestamp}.dump"

export PGHOST="${POSTGRES_HOST:-localhost}"
export PGPORT="${POSTGRES_PORT:-5432}"
export PGUSER="$POSTGRES_USER"
export PGPASSWORD="${POSTGRES_PASSWORD:-}"

pg_dump --format=custom --no-owner --no-privileges --file="$backup_file" "$POSTGRES_DB"
printf '%s\n' "$backup_file"
