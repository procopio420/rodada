# Railway temporary demo (not production)

This is a **temporary** demonstration containing Django API, SSE dispatcher and Next.js in one container, plus an independent Railway-managed PostgreSQL. Committing these files does not launch any cloud service.

## Runtime topology and public ingress (verified 2026-10-14)

**The Django/DRF API is inside the existing Railway service `rodada-web`, NOT a separate `rodada-api` service.** One Docker container runs Nginx on port 8080, Uvicorn/Django on loopback port 8000, Next.js on loopback port 3000 and the SSE dispatcher. PostgreSQL is a separate Railway service.

- `api.rodada.bar` is the reserved, shared technical API hostname: the Nginx `server_name api.rodada.bar` virtual host forwards **every path directly to Django** (e.g. `/ready/`, `/auth/login/`, `/payments/webhooks/...`). It must NEVER serve Next.js `/staff` or resolve to a Venue.
- `bardoaderlan.rodada.bar` and other explicitly provisioned Venue hosts enter the *same* `rodada-web` listener. The default Nginx server routes public module pages and `/api/*` BFF to Next.js, and explicitly enumerated raw Django paths to Uvicorn. Django remains the authorization and Venue-scoping authority.
- `rodada-web-demo.up.railway.app` remains a legacy/demo compatibility host on that same default server. The wildcard `*.rodada.bar` attaches to `rodada-web`; Cloudflare proxy/SSL settings do not create a second backend.
- Next.js makes *internal* API requests using `RODADA_API_BASE_URL=http://127.0.0.1:8000` (set in `start.sh`). Android/native clients and PSP callbacks use public `https://api.rodada.bar/<django-route>/` without a leading `/api` BFF prefix.

Ingress regression gate: `.github/workflows/railway-demo-build.yml` checks that `Host: api.rodada.bar` serves Django health/auth/webhooks while both `/` and `/staff` return Django 404 (not the Next.js UI), and that Venue/legacy hosts still work. After approval/rollout, recheck real HTTPS Host routing and **Full (strict)** origin TLS separately; CI localhost Host headers do not validate Cloudflare behavior.

## Create two Railway services

1. In Railway create a fresh project named `rodada-aderlan-demo`. Add a PostgreSQL database. Keep its service name `Postgres`.
2. Add a **GitHub Repo** service from `procopio420/rodada` with branch `deploy/railway-aderlan-demo-20261009`.
3. The app service's source **Root Directory** must remain `/` (repo root). Configure Dockerfile builder and **Dockerfile Path** = `deploy/railway/Dockerfile` (or variable `RAILWAY_DOCKERFILE_PATH=deploy/railway/Dockerfile`).
4. In app service **Variables** set:
   - `PORT` = `8080`
   - `DJANGO_SECRET_KEY` = a newly generated unique secret (do not commit)
   - `POSTGRES_HOST` = reference to `Postgres.PGHOST`
   - `POSTGRES_PORT` = reference to `Postgres.PGPORT`
   - `POSTGRES_DB` = reference to `Postgres.PGDATABASE`
   - `POSTGRES_USER` = reference to `Postgres.PGUSER`
   - `POSTGRES_PASSWORD` = reference to `Postgres.PGPASSWORD`
5. Create a Railway HTTPS public domain **on the app service only**. Do not expose the PostgreSQL service to the internet.
6. Check **actual** build/start logs; startup runs migrations and idempotent `seed_demo`. No claims of success until Railway reports a successful deployment.
7. Open the actual HTTPS URL, append `/staff`. There is no HTTP Basic Auth prompt: use the Rodada application login.
8. Then sign in to Rodada with test-only Venue `bar-do-aderlan`, user `ana` PIN `0420` or `bia` PIN `1234`.
9. Navigate to `/attendance`, `/bar`, `/kitchen`, `/manage`, `/cash` and `/reports`. Place a new order and check its production routing before saying the demo works.

## Security and limitations

- Nginx is the only public listener; Next.js and Django API are reachable only inside the app container. This is **not** a Tailscale-only deployment.
- There is **no outer HTTP Basic Auth**: the staff area uses only the Rodada application login. This is not a customer-facing live venue deployment.
- **Security warning**: demo PINs are known in repository documentation. Anyone who knows them may access this isolated demo and create fake orders. Never place real data here, and delete the demo after presenting it.
- Payment methods are demo/manual-only. Never claim PSP settlement, Pix or Tap on Phone.
- Icon/media stored inside this app container are **ephemeral**. PostgreSQL data is managed separately.
- Restart reruns migrations and seeds but does **not** reset database or any created transactions. Use one replica only.
- Railway resources may cost money. Delete after the demo. Never point this demo at production data.
- Configuration files are **untested in Railway** until a live build and smoke test prove them working.

## Explicit secure pilot profile

Default `RODADA_RELEASE_MODE=demo` is disposable staging only. For a separately approved
assisted-pilot target set `RODADA_RELEASE_MODE=pilot`, `DJANGO_DEBUG=false`,
`RODADA_PAYMENT_SIMULATION=false`, and a newly generated unique Django secret (at least
50 characters) in the secret manager. Pilot never seeds demo identities/catalog/visits.
Provision an independent cryptographically generated `RODADA_BFF_HOST_SECRET`
(at least32 characters); missing, short or repetitive values now refuse pilot
preflight before database contact. Default demo retains a process-local random
fallback shared by Next/Django. This validation does not measure entropy or certify
ingress/TLS; see the [Spec025 preview runbook](../../docs/ops/spec025-preview-rollout.md).
Unsafe configuration fails before migration; documented active demo PINs refuse startup.
Do not promote a populated public-demo database. Startup cannot prove secret uniqueness;
release operator owns generation/isolation. One replica remains required by process-local
Web refresh coordination. See [protected provisioning](pilot-provisioning.md).
# Controlled multitenant activation on an existing shared runtime

Do not create a service/database per Venue. Before an approved shared-runtime
activation, verify backup, current deployment/configuration and pilot health.
If release mode is `demo`, set `RODADA_DEMO_SEED_ON_START=false` in the reviewed
change to prevent automatic writes to existing Aderlan credentials/guest policy
on restart. This also skips automatic Play reviewer provisioning. Default remains
`true` for existing isolated demo bootstrap. Only literal `true`/`false` is valid.
Enabling tenant UI with demo seeding still enabled fails preflight before database
contact. Enabled tenant UI requires an explicitly provisioned strong shared BFF
secret; the runtime-generated demo fallback is insufficient for this gate.
To add A/B hostnames without overwriting existing trusted aliases, use
`DJANGO_ADDITIONAL_ALLOWED_HOSTS=e2ea.rodada.bar,e2eb.rodada.bar`.
It is additive to `DJANGO_ALLOWED_HOSTS`, is not a wildcard, and by itself
never provisions VenueDomain rows or activates tenant UI. Keep the original
`DJANGO_ALLOWED_HOSTS` value unchanged in Railway.
These settings do not disable migrations, authorize activation, prove origin TLS,
or complete the original separate-preview criterion. See the [#151 checkpoint](../../specs/025-tenant-host-routing/railway-151-checkpoint.md)
and [runbook](../../docs/ops/spec025-preview-rollout.md).
