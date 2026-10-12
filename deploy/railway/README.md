# Railway temporary demo (not production)

This is a **temporary** demonstration containing Django API, SSE dispatcher and Next.js in one container, plus an independent Railway-managed PostgreSQL. Committing these files does not launch any cloud service.

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
Unsafe configuration fails before migration; documented active demo PINs refuse startup.
Do not promote a populated public-demo database. Startup cannot prove secret uniqueness;
release operator owns generation/isolation. One replica remains required by process-local
Web refresh coordination. See [protected provisioning](pilot-provisioning.md).
