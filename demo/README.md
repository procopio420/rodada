# Local release demo

Run from the repository root, with Docker Compose and Python 3 available:

```sh
bash scripts/demo-smoke.sh
# Optional restart exercise, only when no tests use this PostgreSQL instance:
RODADA_DEMO_RESTART=1 bash scripts/demo-smoke.sh
```

This creates the isolated `rodada-demo` Compose project, persistent PostgreSQL 17,
ASGI API, durable SSE dispatcher and production Web build. No Redis is required.
The script provisions explicitly test-only Venue/staff identities, then conducts a
shift exclusively through HTTP commands. Subsequent runs create new shift resources
and compare Management deltas against the previous canonical report. Money is
**MANUAL_TEST**: cash drawer/test terminal declarations and test refunds. There is
no PSP confirmation, actual settlement, live Tap or printing claim.

- Web: `http://localhost:3119/staff`, `/kitchen`, `/bar`, `/manage`, `/cash`.
- API: `http://localhost:18764`; readiness `/ready/`.
- Android debug: emulator URL `http://10.0.2.2:18764/`.
- PostgreSQL: localhost port 55459, database `rodada_demo`.
- Local-only QA identities: Venue `release-demo`, operator `release-staff` (PIN
  `1357`, STAFF), `release-owner` (PIN `2468`, OWNER). These are disposable test
  credentials, never production credentials. Ordinary Bia/Ana fixtures from
  `seed_demo` are also installed, under `bar-do-aderlan`.

```sh
cd apps/attendance-android
./gradlew -ProdadaApiBaseUrl=http://10.0.2.2:18764/ testDebugUnitTest assembleDebug lintDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb shell am start -n com.rodada.attendance/.MainActivity
```

For a phone on the same Wi-Fi, build debug with the host's LAN URL instead; Web and
API demo ports are reachable on the LAN. The stack is for local test data only.
Keep the normal release cleartext policy intact. API URL changes require rebuild.

Reverify saved financial history without replaying new business commands:

```sh
python3 scripts/demo-full-shift.py --verify --evidence /tmp/rodada-demo-shift.json
docker compose -f demo/compose.yaml exec -T db psql -U rodada -d rodada_demo -v ON_ERROR_STOP=1 < demo/reconcile.sql
```

The JSON contains IDs, cents and outcomes, never bearer tokens or PINs. Verification
compares the recorded Management report, so run it before other shifts change that
report. SQL is read-only and independently sums canonical facts without multiplying
rows through joins. The aggregate transfer effect must be zero; cash movement sum
must match each shift's immutable expected snapshot and observed count.

Run PostgreSQL tests in a separate disposable test database (pytest creates
`test_rodada_release_validation`, not the operational demo database):

```sh
cd apps/api
POSTGRES_DB=rodada_release_validation POSTGRES_USER=rodada \
POSTGRES_PASSWORD=demo-local-only POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=55459 \
python -m pytest --ds=rodada_api.settings
```

`docker compose -f demo/compose.yaml stop` preserves history. `start db api dispatcher
web` resumes it. Do not use `down -v` unless deliberately discarding the entire test
history. To retry after a harness failure, inspect the traceback and persisted
commands; do not fabricate receipts or repair balances with SQL. A failed runner
is a failed run, even when earlier requests committed.

Dependencies use the repository's bounded API requirements, locked Web package
versions and PostgreSQL major image. Rebuilding later may resolve newer API patch
versions; the release evidence records versions actually used.

Windows sem Docker/WSL: [stack nativa isolada](WINDOWS.md), mesmos serviços/limites com evidência específica de ambiente.
