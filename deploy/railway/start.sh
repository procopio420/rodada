#!/usr/bin/env bash
set -euo pipefail

for name in DEMO_GATE_PASSWORD DJANGO_SECRET_KEY POSTGRES_HOST POSTGRES_PORT POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD; do
  if [[ -z "$(printenv "$name" 2>/dev/null || true)" ]]; then
    echo "Missing required variable: $name" >&2
    exit 1
  fi
done
if [[ "$(printf %s "$DEMO_GATE_PASSWORD" | wc -c)" -lt 16 ]]; then
  echo "DEMO_GATE_PASSWORD must be at least 16 characters" >&2
  exit 1
fi

export DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"
export RODADA_PAYMENT_SIMULATION=false
export RODADA_API_BASE_URL=http://127.0.0.1:8000

cd /app/apps/api
for attempt in $(seq 1 30); do
  if python manage.py migrate --noinput; then
    break
  fi
  if [[ "$attempt" -eq 30 ]]; then
    echo "Migrations failed" >&2
    exit 1
  fi
  sleep 3
done
python manage.py seed_demo

umask 077
printf '%s\n' "$DEMO_GATE_PASSWORD" | htpasswd -iB -c /tmp/rodada-demo.htpasswd rodada-demo >/dev/null
python - <<'PY'
from pathlib import Path
import os
port = int(os.environ.get("PORT", "8080"))
if not 1 <= port <= 65535:
    raise ValueError("Invalid PORT")
template = Path("/app/deploy/railway/nginx.conf.tpl").read_text()
Path("/etc/nginx/conf.d/default.conf").write_text(template.replace("__PORT__", str(port)))
PY
nginx -t
uvicorn rodada_api.asgi:application --host 127.0.0.1 --port 8000 &
api_pid=$!
python manage.py dispatch_realtime &
dispatcher_pid=$!
cd /app/apps/web
node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3000 &
web_pid=$!
nginx -g 'daemon off;' &
nginx_pid=$!

cleanup() {
  kill "$api_pid" "$dispatcher_pid" "$web_pid" "$nginx_pid" 2>/dev/null || true
  wait || true
}
trap cleanup EXIT INT TERM
echo "Rodada demo started behind private HTTP Basic Auth gateway"
wait -n "$api_pid" "$dispatcher_pid" "$web_pid" "$nginx_pid"
echo "A required service exited; ending container for Railway restart" >&2
exit 1
