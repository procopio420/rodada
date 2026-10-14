#!/usr/bin/env bash
set -euo pipefail

for name in DJANGO_SECRET_KEY POSTGRES_HOST POSTGRES_PORT POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD; do
  if [[ -z "$(printenv "$name" 2>/dev/null || true)" ]]; then
    echo "Missing required variable: $name" >&2
    exit 1
  fi
done
source "$(dirname "$0")/runtime-profile.sh"
export DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS:-127.0.0.1,localhost}"
export RODADA_PAYMENT_SIMULATION=false
export RODADA_API_BASE_URL=http://127.0.0.1:8000
export RODADA_BFF_HOST_SECRET="${RODADA_BFF_HOST_SECRET:-$(python -c 'import secrets; print(secrets.token_hex(32))')}"

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
if [[ "$RODADA_RELEASE_MODE" == demo ]]; then
  python manage.py seed_demo
  if [[ -n "${RODADA_PLAY_REVIEW_PIN:-}" ]]; then
    python manage.py shell < /app/deploy/railway/provision_play_reviewer.py
  fi
else
  python - <<'PYTHON'
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
django.setup()
from modules.access.models import StaffMember
if any(staff.check_pin(pin) for staff in StaffMember.objects.filter(is_active=True) for pin in ("0420", "1234", "2468", "1357")):
    raise SystemExit("Pilot refuses documented demo staff PINs; revoke/reset them before startup")
PYTHON
fi

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
echo "Rodada $RODADA_RELEASE_MODE started; only application-native login is required"
wait -n "$api_pid" "$dispatcher_pid" "$web_pid" "$nginx_pid"
echo "A required service exited; ending container for Railway restart" >&2
exit 1
