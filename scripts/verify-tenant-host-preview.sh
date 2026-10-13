#!/usr/bin/env bash
set -euo pipefail
host="${PREVIEW_TENANT_HOST:?Set PREVIEW_TENANT_HOST to a verified preview tenant hostname}"
unknown="${PREVIEW_UNKNOWN_HOST:?Set PREVIEW_UNKNOWN_HOST to an unregistered hostname under the same wildcard}"
if [[ "$host" != *.rodada.bar || "$unknown" != *.rodada.bar || "$host" == "$unknown" ]]; then
  echo "Preview and unknown hosts must be distinct .rodada.bar subdomains" >&2; exit 2
fi
echo "Checking TLS, HTTPS and per-Host install identity: $host"
manifest="$(curl --fail --silent --show-error --max-time 15 "https://$host/manifest.webmanifest")"
printf '%s' "$manifest" | python -c 'import json,sys; m=json.load(sys.stdin); assert m["start_url"] == "/" and m["scope"] == "/" and m["name"].startswith("Rodada — "); print("OK:", m["name"])'
for endpoint in health ready; do
  result="$(curl --fail --silent --show-error --max-time 15 "https://$host/$endpoint/")"
  printf '%s' "$result" | python -c 'import json,sys; assert json.load(sys.stdin)["status"] in {"ok", "ready"}'
  echo "OK: /$endpoint/ healthy"
done
status="$(curl --silent --show-error --max-time 15 --output /dev/null --write-out '%{http_code}' "https://$unknown/api/venue/context")"
if [[ "$status" != 421 ]]; then echo "FAIL: unknown host status $status, expected 421" >&2; exit 1; fi
echo "OK: unknown host rejected with 421; preview DNS/TLS probe succeeded"
