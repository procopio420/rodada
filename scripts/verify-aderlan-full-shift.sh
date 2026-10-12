#!/usr/bin/env bash
# Disposable G2/P2 release acceptance: real PostgreSQL/HTTP, no provider settlement.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ "${CI:-}" != "true" && "${RODADA_DISPOSABLE_DB_ACK:-}" != "1" ]]; then
  echo "FAIL: requires ephemeral CI or RODADA_DISPOSABLE_DB_ACK=1 (will create demo orders)." >&2
  exit 2
fi
command -v docker >/dev/null || { echo "FAIL: Docker required" >&2; exit 2; }
mkdir -p artifacts
export RODADA_DEMO_RESTART=1
export RODADA_DEMO_EVIDENCE="$ROOT/artifacts/aderlan-full-shift.json"
export RODADA_DEMO_POSTGRES_IMAGE="${RODADA_DEMO_POSTGRES_IMAGE:-public.ecr.aws/docker/library/postgres:17}"
compose=(docker compose -f demo/compose.yaml)
echo "GATE 1: full two-station demo shift, idempotency, refunds, guest, sessions and persisted restart"
bash scripts/demo-smoke.sh
echo "GATE 2: PostgreSQL contractual regressions"
"${compose[@]}" exec -T api python -m pytest --ds=rodada_api.settings \
  tests/test_four_track_shift.py \
  tests/test_cash_management.py \
  tests/test_payments_concurrency.py \
  tests/test_kds_health.py \
  tests/test_restore_rehearsal.py
echo "GATE 3: 8 concurrent clients x 64 full Tabs with canonical reconciliation"
python3 scripts/release-busy-shift.py --url http://127.0.0.1:18764 \
  --workers 8 --tabs 64 --evidence "$ROOT/artifacts/aderlan-busy-shift.json"
echo "GATE 4: restart services and DB, verify 64 tabs remain financially closed"
"${compose[@]}" restart db api dispatcher web
for i in $(seq 1 80); do
  if curl --fail --silent http://127.0.0.1:18764/ready/ >/dev/null; then break; fi
  [[ "$i" != "80" ]] || { echo "FAIL: no readiness after restart" >&2; exit 1; }
  sleep 2
done
python3 scripts/release-busy-shift.py --url http://127.0.0.1:18764 \
  --workers 8 --tabs 64 --evidence "$ROOT/artifacts/aderlan-busy-shift.json" --verify
python3 - <<'PY'
import json
from pathlib import Path
e = Path("artifacts/aderlan-busy-shift.json")
d = json.loads(e.read_text())
assert d["passed"] and len(d["completed_tabs"]) == 64
shift = json.loads(Path("artifacts/aderlan-full-shift.json").read_text())
assert shift["payment_classification"] == "MANUAL_TEST"
assert shift["native_android_ui"] == "NOT_RUN"
summary = {
    "result": "PASS",
    "environment": "disposable Docker PostgreSQL and HTTP, NOT the physical Aderlan bar",
    "manual_test_payment_only": True,
    "physical_wifi": "EXTERNAL_BLOCKED",
    "native_android_ui": "NOT_RUN",
    "provider_settlement": "NOT_RUN",
    "full_shift_replay": True,
    "busy_shift_tabs": len(d["completed_tabs"]),
    "restart_verified": True,
}
Path("artifacts/aderlan-pilot-qa-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary))
PY
echo "PASS: QA simulated shift release gate, not physical bar acceptance"
