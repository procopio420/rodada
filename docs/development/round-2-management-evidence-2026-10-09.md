# Round 2 Management focused closure evidence

Owner: Management agent. Isolated branch `release/round2-management`.
Implementation SHA: `2e0bb5354c40370f384f841037e1426b735dcae2`.
Policy/schema contract commit: `d412f2a`; migration is generated and owned by
release orchestrator (`venue/0005_operationalalertpolicy_guest_request_danger_seconds_and_more.py`).

## Behavior and criterion proposals

- **018-011: MISSING → PASS proposed.** A fresh BILL_REQUEST remains only its
  original DispatchTask before the configured warning age. Evidence:
  `tests.test_guest_request_alerts.GuestRequestAlertTests.test_fresh_warning_claim_escalation_terminal_resolution_and_recurrence`.
- **018-023: MISSING → PARTIAL proposed.** Venue-versioned warning/danger
  thresholds create one source-linked in-app episode for OPEN/CLAIMED bill or
  service requests, preserving original creation age, ownership and destination.
  Canonical DONE/CANCELLED resolves automatically; claim/acknowledgement does not.
  Exact task provenance is visible on manager alert detail. Push/staff-zone
  recipient routing and an exact navigable task action screen remain absent.
- **013-009 and 013-012 remain PASS within existing alert configuration scope.**
  New guest SLA fields use existing reauthentication, expected_version conflict,
  typed before/after audit and canonical server-confirmed UI. Legacy client PATCH
  retains the existing guest threshold values.
- **018-012/018-024 remain MISSING:** no queue aggregate sustained condition or
  recovery hysteresis implemented in this slice. No schema invented to obscure
  that gap. NotificationDelivery/provider/push preferences remain independent.

Relevant code: `apps/api/modules/management/alerts.py`,
`apps/api/modules/management/views.py`, `apps/api/modules/venue/models.py`,
`apps/web/components/operational-alerts.tsx`,
`apps/web/app/manage/alerts/[id]/page.tsx`,
`apps/web/app/manage/alerts/settings/page.tsx`.

## Executed validation

Environment: Linux local isolated worktree, Python3.13 venv, actual PostgreSQL
on 127.0.0.1:55462, disposable database `test_rodada_round2_management`, Django
production URLConf/authentication and actual canonical DispatchTask persistence.
Disposable credentials are development-only. No provider settlement is exercised.

From `apps/api`, with POSTGRES_HOST=127.0.0.1, POSTGRES_PORT=55462,
POSTGRES_DB=rodada_round2_management and disposable test credentials:

```sh
/home/lucas/projects/rodada/venv/bin/python manage.py test tests.test_operational_alerts tests.test_guest_request_alerts --noinput -v 1
/home/lucas/projects/rodada/venv/bin/python manage.py test tests.test_guest_request_alerts.GuestRequestAlertConcurrencyTests --noinput -v 1
```

First run: 16 PASS in21.671s; zero failure/skip. The additional concurrency test
was added after that run and executed separately: 1 PASS in0.815s, zero skip.
Eight concurrent evaluations using four PostgreSQL connections produce one
DANGER episode and one ACTIVATED lifecycle event without changing the task.
The implementation tree tested corresponds to the stated SHA.

From `apps/web`:

```sh
npm run typecheck
npm run build
RODADA_VISUAL_PORT=3132 RODADA_REFERENCE_PORT=3133 npm run test:visual -- tests/visual/management-alerts.spec.ts
```

Typecheck and production build PASS. Focused browser gate: 6 PASS in15.8s,
including axe/layout at360/430/768, typed conflict and existing acknowledgement/
resolved-history regression. Browser tests use explicitly mocked transport for
presentation and do not count as real backend or SSE-outage evidence.
Original reference exports, hashes and acceptance thresholds remain unchanged.

Initial attempts failed before validation: wrong disposable PostgreSQL password
(auth failure; corrected using container credentials), npm from repository root
(no package.json; corrected cwd), Turbopack refused dependency symlink outside
worktree (resolved with local dependency copy). No test behavior was weakened.

Full visual suite is being executed separately; final outcome is appended when
available. Canonical release gates/matrices remain orchestrator-owned.
