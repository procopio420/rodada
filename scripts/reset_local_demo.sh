#!/usr/bin/env bash
set -euo pipefail

# This command is intentionally restricted to the local development defaults.
# It clears all local data before recreating the deterministic demo dataset.
if [[ "${DEBUG:-1}" != "1" ]]; then
  echo "Refusing to reset data unless DEBUG=1." >&2
  exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
api_dir="${script_dir}/../apps/api"

cd "${api_dir}"
python manage.py migrate
python manage.py flush --noinput
python manage.py seed_demo
