# Initial QA audit — 2026-10-09

Base: `b88c347d7a6f093de6321b0bc5890c4987d8d443`; isolated `release-qa` worktree. This initial audit is not final release verification. Per-criterion mapping is in `closure-qa-2026-10-09.json` (89 criteria, including both Spec 022 directories and duplicated Spec 023 bullets).

Fresh verification:

- PostgreSQL server: 17.11 Debian, localhost:55459, dedicated `rodada_rc_qa`; migration application completed and `makemigrations --check --dry-run` returned `No changes detected`. Initial history check warned DB absent; database was subsequently created and migrated before rerunning successfully.
- `python manage.py check`: no issues, no silencing.
- `python scripts/verify_realtime.py` against standalone uvicorn localhost:18765 and PostgreSQL: PASS. Verified live guest, separately spawned dispatcher process, duplicate command, replay, canonical balance on reload, cursor reset and connected-session revocation. Confirmation-to-event: 1234 ms. `redis_restart_verified=false`. This is a live smoke, not a busy-shift latency distribution or API/database restart proof.
- Full PostgreSQL suite started with `python -m pytest --ds=rodada_api.settings -q`; INTERRUPTED when the initial agent turn ended; log stops before a summary. No full-suite PASS or count is valid. Log `/tmp/rodada-qa-postgres.log`, former execution session 29510 is no longer running. No final success/count claimed. Initial plain `pytest -q` run uses SQLite despite POSTGRES environment, log `/tmp/rodada-qa-pytest.log`, former session81523 also ended without summary; it is not PostgreSQL or complete-suite evidence.
- `python manage.py check --deploy`: five warnings, none silenced: security.W002 (frame middleware), W003 (CSRF middleware), W004 (HSTS), W008 (HTTPS redirect), W009 (default weak key). These local settings are not deployment evidence; actual production proxy/secrets hardening must be validated.

No fresh Web, Android or emulator validation performed by this worktree: Web dependencies/build absent. Integrator runs the corresponding gates. Existing visual reports were inspected and explicitly identified as historical, not rerun.

Findings and remaining work:

- Plain pytest defaults to SQLite and skips row-lock gates. Explicit `--ds=rodada_api.settings` is required. Proposed CI PostgreSQL job expansion to the entire suite is currently uncommitted until the full local PostgreSQL suite finishes green.
- Web API integration defaults SQLite; require `RODADA_E2E_POSTGRES=1` with dedicated `POSTGRES_DB=rodada_web_e2e` for PostgreSQL integration evidence.
- Full-artboard visual comparisons are audits while selected equivalent primitives have strict 0.1% assertions. This does not close full Spec 023 parity. Hardware, native complete parity and stale/failure surfaces remain open.
- Class C offline READY is explicitly disabled; enabled replay acceptance is unimplemented. Emergency cash evidence/review/audit lifecycle and dependency-aware recovery remain missing or incomplete.
- Payment tests contain explicit provider fakes for domain invariants; these cannot prove real payment settlement. Approved merchant/SDK, NFC capture, real Pix confirmation, printer hardware and live rollout remain external blockers.
- Reviewed staff token namespace, current role/device replay authorization, venue-filtered realtime, SumUp untrusted-notification boundary and Paytime signature validation. No new reproduced P0 exploit was established during this initial audit; full negative suite and release-head review remain required.

Resume QA after integration for full PostgreSQL results, real HTTP busy-shift p50/p95/errors and independent totals, service/database restarts, visual/accessibility/native gates and final release recommendation. No release decision is made from this initial audit.
