# Issue #106 — local shared-client runner

This runner exercises the implemented slices, not the complete 14-scenario
acceptance or onsite gates. Missing coverage keeps full release NO-GO.

Prerequisites: Docker, Python 3.13, Node 22+, JDK17, Android SDK37, an explicitly
disposable running emulator (API36/KVM), adb in PATH and Chromium dependencies.
Use the committed lockfile; do not reuse a remote/shared database or fixture.

```sh
python -m venv .venv
.venv/bin/pip install -e 'apps/api[dev]'
cd apps/web
npm ci
npx playwright install chromium
cd ../..
# Editable packaging may regenerate tracked egg-info metadata. Inspect it and
# preserve your changes before starting; the runner requires committed source.

docker run -d --name rodada-106-local-disposable --network host \
  -e POSTGRES_DB=rodada_android_post_drop -e POSTGRES_USER=rodada_test \
  -e POSTGRES_PASSWORD=local-ci-only postgres:17 \
  -c port=55608 -c listen_addresses=127.0.0.1
export POSTGRES_DB=rodada_android_post_drop POSTGRES_USER=rodada_test
export POSTGRES_PASSWORD=local-ci-only POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=55608
export ANDROID_HOME="$HOME/Android/Sdk"
export PATH="$ANDROID_HOME/platform-tools:$PATH"
# Use new, absent paths on every fresh DB/run. No evidence overwrite permitted.
export RODADA_POST_DROP_FIXTURE=/tmp/rodada106-local-fixture.json
export RODADA_POST_DROP_MARKER=/tmp/rodada106-local-marker.json
bash scripts/run-issue106-shared.sh
```

Stop only your own listeners on 8000/8101/3110 first. Other occupied ports cause
a fail-closed preflight. The runner validates configured and connected PostgreSQL
identity before migrations, requires a fresh fixture Venue, and records a digest
of PostgreSQL cluster system_identifier plus database name. Reusing the same
name on another cluster cannot reuse a receipt. Backend, proxy and BFF belong to
the same runner and are stopped on exit; the disposable database is preserved.
No Railway, production, deployment, provider or Play operation is performed.

Order: native committed-response loss/force-stop/replay -> table response loss ->
production Compose mixed order -> Guest/Web/Kitchen recovery/QR lifecycle ->
independent SQL -> test CASH partial/residual/drawer -> independent financial SQL.
Traces include successful actions and are redacted before export. Raw traces
remain local; inspect exported archives before publishing. Logs, receipts and a
machine-readable execution status are preserved in `artifacts/runs/<SHA-time>/`.
A successful slice status is explicitly separate from the full #106 GO gate.

Known remaining acceptance includes unavailable-after-cart in all clients,
shared-journey authorization/tenant and concurrent command negatives, Android
canonical conflict recovery, isolated SSE outage, pending payment and
compensatory refund/report coverage. Existing domain tests are reusable evidence
of components, not replacements for those integrated UI paths.
