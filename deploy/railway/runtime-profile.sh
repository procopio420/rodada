#!/usr/bin/env bash
# Source before connecting to the database. Never log secret values.
export RODADA_RELEASE_MODE="${RODADA_RELEASE_MODE:-demo}"
export RODADA_DEMO_SEED_ON_START="${RODADA_DEMO_SEED_ON_START-true}"
case "$RODADA_DEMO_SEED_ON_START" in
  true|false) ;;
  *) echo 'RODADA_DEMO_SEED_ON_START must be true or false' >&2; exit 1 ;;
esac
if [[ "${RODADA_ENABLE_TENANT_HOST_UI:-false}" == true ]]; then
  if [[ "$RODADA_RELEASE_MODE" == demo && "$RODADA_DEMO_SEED_ON_START" != false ]]; then
    echo 'Shared tenant activation requires RODADA_DEMO_SEED_ON_START=false' >&2
    exit 1
  fi
  python - <<'PY' || exit 1
import os
secret = os.environ.get('RODADA_BFF_HOST_SECRET', '')
if len(secret) < 32 or len(set(secret)) < 5:
    raise SystemExit('Tenant activation requires a high-entropy RODADA_BFF_HOST_SECRET (at least 32 characters)')
PY
fi
case "$RODADA_RELEASE_MODE" in
  demo) ;;
  pilot)
    if [[ "${DJANGO_DEBUG:-false}" != false || "${RODADA_PAYMENT_SIMULATION:-false}" != false ]]; then
      echo 'Pilot requires DEBUG=false and payment simulation=false' >&2
      exit 1
    fi
    python - <<'PY' || exit 1
import os
secret = os.environ.get('DJANGO_SECRET_KEY', '')
if len(secret) < 50 or len(set(secret)) < 16 or any(word in secret.lower() for word in ('demo', 'dev-only', 'ci-local', 'change-me', 'disposable')):
    raise SystemExit('Pilot requires a newly generated non-demo Django secret (at least 50 characters)')
bff_secret = os.environ.get('RODADA_BFF_HOST_SECRET', '')
if len(bff_secret) < 32 or len(set(bff_secret)) < 5:
    raise SystemExit('Pilot requires a high-entropy RODADA_BFF_HOST_SECRET (at least 32 characters)')
PY
    ;;
  *) echo 'RODADA_RELEASE_MODE must be demo or pilot' >&2; exit 1 ;;
esac
export DJANGO_DEBUG=false
export RODADA_PAYMENT_SIMULATION=false
