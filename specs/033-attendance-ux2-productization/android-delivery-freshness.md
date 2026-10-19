# E03-07/E06 — Android delivery queue freshness

Base a9500077 (PR #251). Ownership: native refresh/state, presentation and release guards;
no API schema, financial policy, endpoint or compatibility fallback change.
Risk R3: operational/session recovery. Independent review required before integration; root reviewing frozen source.

## Implementation and acceptance

- Queue GET is isolated from core tabs/products/detail snapshot. Failure retains
  the last queue with explicit stale text and unknown count; refresh/realtime
  invalidation and existing30s HTTP fallback re-read it.
- Successful core HTTP read is operationally ONLINE with no SSE connection.
  Connected SSE signals alone cannot revive a failed core snapshot.
- Dispatch UNKNOWN blocks release on entry, an already open confirmation and
  the ViewModel mutation boundary. Occupancy ID/generation remain immutable.
- Session generation and coroutine cancellation are checked before publishing
  refresh results, including A→B→A. Old session refresh requests are rejected.
- Existing delivery terminal readback/POST/intent removal/fence are unchanged.
  Its already fenced queue GET now publishes freshness only on actual success;
  the filtered local fallback cannot be marked fresh.

## Validation plan

`LiveDeliveryFreshnessTest`: actual Django/PostgreSQL HTTP, queue503+retained
snapshot, real order and canonical charges on the same Tab, core503+healthy
queue, rejected release, Connected signal after failed core, restoration and
held canceled response across A→B→A. Only the Connected signal is injected;
HTTP ordering/queue/ledger are real. No assertion of physical device behavior.

`TableReleaseTest`: no mutation for cancellation, stale occupancy, busy/permission,
READY arrival and freshness loss after confirmation opens. `AttendanceNowUx2Test`:
matched fresh/stale captures preserve work/count—. Unit coverage asserts unknown
queue count independent of healthy core. Existing recovery regression retained.

Execution results and artifact paths will be appended after running the gates.

## Scope boundary discovered during review

This slice isolates **Dispatch deliveries** only. `readServiceRequests` is still
awaited before the core snapshot; a hanging service-call request can therefore
delay core refresh. That existing gap remains pending for the next isolated
slice. No claim that every operational queue is isolated. Session-fence work
in another branch must be composed and tested before integration.

## Verification resumed 2026-10-19

- Final native gates: `testDebugUnitTest assembleDebug assembleDebugAndroidTest
  lintDebug -ProdadaApiBaseUrl=http://10.0.2.2:18136/`: PASS, 128 JVM tests,
  zero failures/errors/skips. Emulated API36; real local Django/PostgreSQL.
- Real HTTP freshness rerun: 2/2 PASS, 36.121s; `live.log`. Actual canonical
  order/charges while Dispatch503, core503 negative, held queue while a second
  core refresh sees a newly created Tab, and canceled A→B→A refresh.
- Earlier UI failures are retained: wrong instrumentation class, obsolete
  combined Bia label, and a release happy-path fixture missing explicit fresh
  queue state. Production guards and assertions remain; fixtures/selectors
  are corrected to the canonical state/real separate display fields.
- Physical device, TalkBack, full epic parity and pilot remain unverified.
