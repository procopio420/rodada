# Issue #106 — local shared-client runner

This runner exercises all 14 automated scenarios on one disposable shared stack.
The scenario result and reviewed automated GO are separate from onsite gates.
The verified execution is recorded in [the matrix](issue-106-resumption-matrix.md).

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

The runner additionally executes native stale-cart/offline/revocation, Web/Guest
isolation, shared HTTP concurrency, SSE/KDS recovery, native contextual readback,
negative financial capabilities, both business-cutoff sides and final read-only
SQL reconciliation. Zero opening float creates no CashMovement. Guest release
revocation is authoritative through generation/occupancy, not a required terminal
`revoked_at` marker. Catalog and clock-policy faults touch only the guarded fixture.

A successful run initially exports NO-GO until an independent reviewer inspects
the exact SHA and artifacts. Record the actual review (not self-approval) as JSON:

```json
{"sha":"FULL_TESTED_COMMIT_SHA","independent":true,"open_p0_p1":0,"reference":"TRACEABLE_REVIEW_REFERENCE"}
```

Then regenerate and verify using the same checkout, fixture, versions and capture:

```sh
python scripts/build-issue106-report.py "$CAPTURE" --fixture "$RODADA_POST_DROP_FIXTURE" \
  --versions "$CAPTURE/versions.json" --sha "$TESTED_SHA" --run-url "$RUN_URL" \
  --pr "$PR_URL" --review "$REVIEW_JSON"
python scripts/e2e_evidence.py "$CAPTURE/manifest.json" --sha "$TESTED_SHA" --root "$CAPTURE"
```

`CAPTURE`, `TESTED_SHA`, `RUN_URL`, `PR_URL` and `REVIEW_JSON` refer to the actual
run and review. The compiler validates the final SQL's hashes of its intermediate
receipts; an edited receipt invalidates invariant promotion. Never rewrite receipt
SHAs to reuse another run. Raw traces stay local; publish only inspected sanitized
archives. No external payment settlement, physical Wi-Fi, device, printing,
fiscal or ingress certification follows from automated GO.

CI PR jobs export factual artifacts even for incomplete runs; manual dispatch
also enforces the full validator and remains NO-GO without exact-SHA independent
review. A green scenario job alone never supplies that review.
