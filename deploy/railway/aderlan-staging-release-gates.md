# Rodada — staging release gates (12/10/2026)

**Scope:** isolated Aderlan demo only. Never silently convert the public demo into a live bar deployment. Baseline `main` at `a36e788`; the deployed Railway branch `deploy/railway-aderlan-demo-20261009` was independently observed at `cae1d2f` (10/10) before this change. Those SHA values are snapshots, not ongoing claims.

## Implemented as code

- `scripts/verify-aderlan-staging.py`: read-only gate for /staff, /attendance, /bar, /kitchen, /manage, /cash and /reports. No redirects or HTTP Basic are accepted, response must be non-empty HTML HTTP 200. Only loopback is allowed by default; `--public-demo` opts into **one exact** HTTPS demo hostname. JSON output contains no credentials.
- `.github/workflows/railway-demo-build.yml`: build container + disposable PostgreSQL, verify seven pages, and submit canonical test order to both production stations. No live PSP.
- `deploy/railway/start.sh`: existing demo seed/published credentials; must not be deployed to real merchant production.

## Staging promotion checklist

1. Review this branch's CI including full Docker image build, startup, migrations and seed.
2. Promote reviewed, pinned commit to a **separate staging target**; do not blindly track `main` or overwrite an active venue DB.
3. Inspect Railway environment source SHA and health. Run `python3 scripts/verify-aderlan-staging.py --base https://rodada-web-demo.up.railway.app --public-demo` **read-only** on the existing demo.
4. Verify application login and live test order/stations against disposable data after the deploy, using isolated test credentials only.
5. Verify migrations compatibility, business-date configuration, SSE health, auth revocation, rollback and restore before an assisted onsite pilot.
6. Do not add customer or employee data; the public demo has known test PINs, so it is not production-safe.

**External/promotion gates:** actual Railway release of the reviewed SHA; physical Android/PWA acceptance; printer and PSP status. This PR does not claim that any cloud environment was changed.
