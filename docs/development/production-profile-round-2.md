# Explicit production configuration (not deployed evidence)

Select `DJANGO_SETTINGS_MODULE=rodada_api.settings_production` for API and dispatcher.
Inject `DJANGO_SECRET_KEY` (at least 50 high-entropy characters) and database/payment
credential keys from the environment secret store; do not put values in Git or shell
history. Set explicit `DJANGO_ALLOWED_HOSTS=api.rodada.ai` and HTTPS-only
`DJANGO_CSRF_TRUSTED_ORIGINS` for actual approved browser origins.

The ingress must terminate TLS, block direct upstream access, strip incoming
X-Forwarded-Proto then set it from the actual connection. Only after proving that
boundary set `RODADA_TRUST_HTTPS_PROXY=1`. API redirects HTTP, sends HSTS (one year,
subdomains; preload is intentionally opt-in), secure cookies and frame protection.
Web BFF must likewise run behind HTTPS with its secure-cookie production behavior.
DRF bearer endpoints keep their explicit authentication; CSRF middleware protects
Django cookie-authenticated endpoints, not a substitute for BFF origin validation.

Executable preflight in the provisioned environment:

```sh
python manage.py check --deploy --fail-level WARNING --settings=rodada_api.settings_production
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
curl --fail --head https://api.rodada.ai/ready/
```

Verify HTTP redirect, certificate chain, HSTS and frame headers through public ingress;
prove spoofed proxy headers cannot suppress redirect. Exercise Web cross-origin
mutation rejection and cookie flags. Verify revocation while SSE is open, reconnect,
connection counts and bounded request duration under intended concurrent device load.
Provision per-client ingress SSE/request limits based on measured pilot load (not an
unverified global application counter). Disable ingress response buffering for SSE.

Before pilot: run `apps/api/scripts/rehearse_restore.sh` on a separate restore DB;
measure/approve RTO/RPO and restore drill access. Keep encrypted backup storage outside
runtime hosts. Deploy immutable image SHA; rollback to previous image only if schema
backward compatibility is verified. Never reverse financial history to roll back.
Expose readiness/health, auth-denial rates, unresolved-payment age, SSE/replay errors,
DB connections and request latency. Test alert ownership/escalation with actual staff.

Local profile preflight does not prove infrastructure, secret rotation, monitoring,
rollback or intended-environment backup behavior. All remain unverified deployment
gates until their exact artifacts exist. No live PSP activation is authorized.
