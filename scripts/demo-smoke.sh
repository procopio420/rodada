#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose -f demo/compose.yaml)
evidence="${RODADA_DEMO_EVIDENCE:-/tmp/rodada-demo-shift.json}"
"${compose[@]}" up -d --build api dispatcher web
for attempt in {1..60}; do
  if curl --fail --silent http://127.0.0.1:18764/ready/ >/dev/null; then break; fi
  if [[ "$attempt" == 60 ]]; then echo 'Demo API did not become ready' >&2; exit 1; fi
  sleep 1
done
"${compose[@]}" exec -T api python manage.py seed_release_demo
"${compose[@]}" exec -T api python manage.py check
"${compose[@]}" exec -T api python manage.py makemigrations --check --dry-run
python3 scripts/demo-full-shift.py --evidence "$evidence"
"${compose[@]}" exec -T db psql -U rodada -d rodada_demo -v ON_ERROR_STOP=1 < demo/reconcile.sql
if [[ "${RODADA_DEMO_RESTART:-0}" == 1 ]]; then
  "${compose[@]}" restart db api dispatcher web
  for attempt in {1..60}; do
    if curl --fail --silent http://127.0.0.1:18764/ready/ >/dev/null; then break; fi
    if [[ "$attempt" == 60 ]]; then echo 'API failed restart recovery' >&2; exit 1; fi
    sleep 1
  done
  python3 scripts/demo-full-shift.py --evidence "$evidence" --verify
fi
