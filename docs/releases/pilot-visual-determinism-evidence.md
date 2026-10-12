# Pilot visual gate determinism — 2026-10-12

Base `defcd94`, fetched main including payment durability changes. Spec 023 owns
visual determinism; no product UI or golden baseline was changed.

The actual failing [main CI run](https://github.com/procopio420/rodada/actions/runs/38277399973)
passed 197 tests and failed the exact consecutive-image equality in
`parity.spec.ts:167`, management 430 px. Its downloadable trace proves a connectivity
mutation during the first screenshot: call@5503 begins at 97991.779 ms, ends at
98117.571 ms, and after@call@5503 (98119.623 ms) records a newly emitted
OperationalAlerts paragraph “Último estado confirmado. Alertas serão revalidados
pela API.” The second screenshot starts at 98121.533 ms. The trace logs fonts
already loaded before both captures. Relevant verbatim trace events and mutated
subtree are preserved in [trace excerpt](evidence/pilot-visual-ci-trace-excerpt.json).
Full original trace/screenshot are in that CI artifact; local copy
`/tmp/pilot-visual-ci/web-visual-and-integration`.

The shared fixture fulfilled an SSE `ready` event and immediately closed the
response. Client code therefore legitimately toggled ONLINE then RECONNECTING
on each randomly delayed reconnect (750–1250 ms). The manager alert component
conditionally emits the paragraph when not ONLINE, moving subsequent content.
This is a finite mock transport race, not evidence that fonts, financial values
or production reconnect logic are defective. A local unmodified 12-repeat gate
passed all 12, confirming the failure is intermittent rather than universal.

The fixture now explicitly represents an API-reachable, disconnected realtime
snapshot: its finite SSE response contains a comment, never a ready event implying
an open stream. Reconnects retain the same visible state. `setFixedTime` keeps Date
stable while allowing hydration/accessibility timers. Pausing timers was tested and
rejected because axe accessibility analysis requires them. Kitchen comparison
fixtures already explicitly pause/resume their own clocks; real realtime browser
and API recovery fixtures remain unchanged.

No screenshot tolerance, retry allowance, snapshot mask or exact byte assertion
was changed; no new golden image was accepted. The warning remains visible, rather
than concealing connectivity failure.

Fresh validation from `apps/web`:

- `npm ci`: clean install, zero audited vulnerabilities.
- `npm run build`: PASS.
- `npm run typecheck`: PASS.
- Baseline targeted gate `npm run test:visual -- --grep 'manage: responsive layout and accessibility at 430px' --repeat-each=12`: 12 passed (1.6 min).
- Corrected targeted repeated gate: **12 passed (1.4 min)**.
- Required full `npm run test:visual`: awaiting completion.
- `git diff --check`: PASS.

These are browser tests using intercepted fixtures, not deployed end-to-end,
physical Wi-Fi, payment-settlement, printer or fiscal acceptance evidence.
