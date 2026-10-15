#!/usr/bin/env bash
# Existing emulator + NEW explicitly configured local disposable PostgreSQL only.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="${RODADA_TEST_PYTHON:-$ROOT/.venv/bin/python}"
export PATH="$(dirname "$PYTHON"):$PATH"
export PYTHONPATH="$ROOT/apps/api" DJANGO_SETTINGS_MODULE=rodada_api.settings
export DJANGO_SECRET_KEY=issue106-disposable-only DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,10.0.2.2
export RODADA_BFF_HOST_SECRET=rodada-integration-local-only RODADA_API_BASE_URL=http://127.0.0.1:8101
"$PYTHON" -c 'import sys;sys.path.insert(0,"scripts");from cross_surface_fixture import require_disposable_database;require_disposable_database();import django;django.setup();from django.db import connection;from cross_surface_fixture import require_connected_database;require_connected_database(connection)'
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then echo 'Commit source changes before an exact-SHA run'; exit 2; fi
: "${RODADA_POST_DROP_FIXTURE:?Set a unique absolute fixture path}"
: "${RODADA_POST_DROP_MARKER:?Set a unique absolute fault marker path}"
[[ ! -e "$RODADA_POST_DROP_FIXTURE" && ! -e "$RODADA_POST_DROP_MARKER" ]] || { echo 'Existing evidence paths: use fresh paths, never overwrite a prior run'; exit 2; }
"$PYTHON" - <<'PY'
import socket
for port in (8000,8101,3110):
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',port)) == 0:
            raise SystemExit(f'Refusing an existing listener on {port}; stop only your own test processes first')
PY
command -v adb >/dev/null
[[ "$(adb shell getprop ro.kernel.qemu | tr -d '\r')" == 1 ]] || { echo 'Disposable emulator required'; exit 2; }
mkdir -p artifacts
run_id="$(git rev-parse --short=12 HEAD)-$(date -u +%Y%m%dT%H%M%SZ)"
run_dir="$ROOT/artifacts/runs/$run_id"
mkdir -p "$run_dir"
api_pid= proxy_pid= web_pid=
step=preflight
cleanup() {
  code=$?
  trap - EXIT
  for pid in "$web_pid" "$proxy_pid" "$api_pid"; do
    if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; fi
  done
  "$PYTHON" scripts/sanitize-cross-surface-traces.py > "$run_dir/trace-export.txt" 2>&1 || true
  "$PYTHON" - "$run_dir" "$code" "$step" <<'PY'
import json,subprocess,sys,shutil
from pathlib import Path
out=Path(sys.argv[1]);code=int(sys.argv[2])
sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
for path in Path('artifacts').glob('*.json'):
    try: receipt=json.loads(path.read_text())
    except ValueError: continue
    if receipt.get('sha') == sha: shutil.copy2(path,out/path.name)
for pattern in ('*-instrumentation.txt','android-compose-confirmed.png'):
    for path in Path('artifacts').glob(pattern): shutil.copy2(path,out/path.name)
if Path('artifacts/sanitized-traces').exists(): shutil.copytree('artifacts/sanitized-traces',out/'sanitized-traces',dirs_exist_ok=True)
(out/'execution.json').write_text(json.dumps({'sha':sha,'result':'PASS' if code==0 else 'FAIL','last_step':sys.argv[3], 'exit_code':code,'automated_gate':'NO-GO','reason':'This executable slice does not yet cover every E2E-01..14 or all A1–F8 requirements.'},indent=2)+'\n')
PY
  echo "Evidence preserved: $run_dir; slice exit=$code; full #106 remains NO-GO"
  exit "$code"
}
trap cleanup EXIT
step=migrations
"$PYTHON" apps/api/manage.py migrate --noinput > "$run_dir/migrations.txt" 2>&1
"$PYTHON" scripts/verify-android-live-post-drop.py prepare --fixture "$RODADA_POST_DROP_FIXTURE"
"$PYTHON" -m uvicorn rodada_api.asgi:application --host 127.0.0.1 --port 8101 > "$run_dir/django.txt" 2>&1 &
api_pid=$!
"$PYTHON" scripts/android-post-drop-proxy.py --evidence "$RODADA_POST_DROP_MARKER" > "$run_dir/proxy.txt" 2>&1 &
proxy_pid=$!
for i in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8101/ready/ >/dev/null && curl -fsS http://127.0.0.1:8000/__fault/status >/dev/null; then break; fi
  if [[ "$i" == 60 ]]; then exit 1; fi
  sleep 1
done
step=native-recovery
unset RODADA_SKIP_ANDROID_BUILD
bash scripts/android-live-post-drop.sh | tee artifacts/android-recovery-instrumentation.txt
bash scripts/android-table-service-post-drop.sh | tee artifacts/android-table-instrumentation.txt
step=compose
bash scripts/android-compose-order.sh
step=web-build
(cd apps/web && npm ci --no-audit --no-fund && npm run typecheck && npm run build) > "$run_dir/web-build.txt" 2>&1
(cd apps/web && exec node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3110) > "$run_dir/next.txt" 2>&1 &
web_pid=$!
for i in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:3110/staff >/dev/null; then break; fi
  if [[ "$i" == 60 ]]; then exit 1; fi
  sleep 1
done
export RODADA_ANDROID_PROOF="$ROOT/artifacts/android-real-post-drop.json" RODADA_ANDROID_COMPOSE_PROOF="$ROOT/artifacts/android-compose-order.json"
step=shared-browser
(cd apps/web && npx playwright test --config playwright.android-cross-surface.config.ts)
step=independent-sql
"$PYTHON" scripts/verify-android-web-cross-surface.py
"$PYTHON" scripts/verify-qr-lifecycle.py
"$PYTHON" scripts/verify-browser-origins.py
step=financial-browser
(cd apps/web && RODADA_CROSS_PHASE=financial npx playwright test --config playwright.android-cross-surface.config.ts)
step=financial-sql
"$PYTHON" scripts/verify-financial-ui.py
step=complete
