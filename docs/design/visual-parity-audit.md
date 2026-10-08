# Web visual foundation audit — PR #40

Date: 2026-10-08. Reference: `prototype/index.html` and `prototype/design-system.css`.

## Scope and evidence

This prepares the shared Web visual foundation, not every planned product capability. The original author's work is preserved on `feat/web-pixel-perfect`; current main (including PRs #41/#42) was merged and conflicts reconciled without removing House Account limits, guest stale safeguards or BYOD documentation. No Android implementation or backend business rule was expanded by PR #40.

| Surface | Before completion | Current implementation |
| --- | --- | --- |
| Staff `/staff` | Unassociated form labels | Explicit accessible labels, keyboard and failed-login coverage |
| Bar `/bar`, Kitchen `/kitchen` | Long content squeezed actions; unavailable catalog form dominated queue | Responsive queue and passe first, readable status/actions, compact explicit Quick Catalog limitation |
| Guest `/guest/[token]` | Successful orders disappeared when context omitted orders | Receipts from successful API responses retained during this session; accurate confirmed/preparing/ready labels |
| Management `/manage` | Hash highlighting failed; initial zero metrics; pending cash hidden | Working navigation, loading/error snapshots, pending cash/refund exceptions before metrics |
| Cash `/cash` | Closed pending review inaccessible through normal point selection | Canonical pending shift loaded when no active shift exists, inline manager PIN and explicit review success |
| Refunds `/refunds` | Missing labels and invisible initial failures | Labeled controls, explicit loading/auth/network failures |
| Legacy POS `/pos` | Missing labels; long names stressed layout | Shared responsive contract and labeled controls; Atendimento remains Android |
| Shared shell | Token drift and no requested credit | Prototype semantic tokens, contrast-safe disabled text, discreet WhatsApp developer footer with fixed-control clearance |

Hosts are `gerencia`, `cozinha`, `bar`, `cliente` under `rodada.ai`; `app` and `pedido` remain compatibility aliases. Manifest and ADR 0010 now agree with the runtime.

## Measured parity, without hiding differences

The original audit reported an 8.8893% full Kitchen mismatch with a 9.5% cap. On this Windows machine the original development composition measured approximately 10.0857%. The completed production composition measures **10.3387% (34,031 / 329,160 pixels)** at 390 × 844. These are different environments/build modes and are not a valid improvement percentage.

Full-page Kitchen comparison remains a generated audit artifact, not a pixel-perfect assertion: production has real auth/navigation, queue actions, passe, the requested footer and a compact unavailable catalog notice; the reference has a different static composition and unconnected creation flow. Increasing the old threshold would conceal these differences.

Instead, seven equivalent reference/production primitives have strict **0.1% maximum mismatch** gates: primary, secondary, danger, disabled button, field, badge and panel. All seven measured **0%** locally. Their reference uses the actual prototype CSS; production uses actual Web CSS. This does not assert full-screen pixel identity for screens with no matching reference.

## Deterministic visual and accessibility coverage

The 87-test suite covers eight surfaces at **360, 390, 430, 768 and 1280 px**, plus empty, held loading, explicit error, long/crowded content and warning states for seven operational screens. Management fixtures include manager House Account controls and spending-limit attention inherited from main. Separate tests cover navigation, failed login, saving/failure/retry and the reference comparisons.

Fixtures intercept APIs only in visual tests. Chromium, locale, timezone, clock start, device scale and data are controlled; animations are removed and fonts awaited. Every main surface is captured twice and checked for identical pixels. Screenshots, diffs, pairs and statistics are generated under ignored `visual-artifacts/` and uploaded by CI.

Checks include zero horizontal overflow, important control targets at least 44 × 44 px, keyboard focus, footer URL and clearance from fixed controls, and no detected axe WCAG A/AA/2.1 violations in covered states. No JavaScript/hydration errors are allowed in the main surface matrix. Kitchen 360 px and Management 390 px were also visually inspected. Automated checks do not replace a human audit on physical devices.

## Real API verification

Four separate browser tests use actual Next BFF and Django, with no intercepted product responses: staff login/secure cookies, idempotent order replay, production availability and transitions, guest QR/order confirmation, revoked visit, management navigation, cash opening/count/close/divergence review with inline reauthentication, absent refund eligibility, capability denial, expired session cookie cleanup, canonical/alias host routing and manifest.

Local integration uses disposable SQLite. CI is configured for an isolated PostgreSQL 17 database named `rodada_web_e2e`; the harness refuses other database names. Test accounts/catalog exist only in that isolated harness, never as production defaults. Before the final main reconciliation, backend validation passed 132 tests. After incorporating PRs #41/#42, the full suite passed **153 tests, 2 skipped**, with clean Django checks and no migration drift. The two PostgreSQL-only concurrency cases are skipped under local SQLite; their CI execution is not claimed. The new HTTP tests required local socket access outside the sandbox. Two fixture/rehearsal lookups were made deterministic by product ID rather than timestamp/UUID order; no business semantics changed.

## Reproduction and CI

From the repository root install the API test dependencies with `python -m pip install -e "apps/api[dev]"`. Then:

```sh
cd apps/web
npm ci
npx playwright install chromium
npm run typecheck
npm run build
npm run test:visual
npm run test:integration
```

Both suites own their production servers; build first. Set `RODADA_TEST_PYTHON` to an absolute Python executable if `python` is unavailable. Integration ports are 8100/3110; visual port is 3100. See `apps/web/README.md`.

Web CI runs typecheck, build, all visual gates and real PostgreSQL integration, retaining screenshots/reports/traces for seven days. API CI remains separate. Check conclusions on the final pushed SHA before merge; local results alone do not prove CI success.

## Explicit remaining debt

- Quick Catalog resolve/create is unavailable: the notice is after operational queues, with no fake save or invented API.
- Guest receipts are confirmed orders from the current browser session. The context API omits order history; there is no new live status feed or persisted receipt history after reload.
- Production updates use the existing five-second polling model. Stale snapshots show failure and pause mutations; older polls cannot overwrite a post-mutation snapshot.
- Cash selection prioritizes an active shift over an older pending review; the dashboard still flags that pending review. A dedicated selector for historical pending shifts remains future work.
- Management shows existing operational data, not invented revenue/analytics. Initial failures do not become successful zero metrics.
- No direct prototype exists for Staff, Bar, Guest, Management, Cash or Refunds. Dispatch is not a new Web screen; the House Account panel is inherited from main, not implemented by this visual PR.
- No physical Android/browser pilot, deployment or production-data acceptance is claimed by this PR.

Future equivalent full-screen references should receive strict image gates. Update prototype and Web tokens together and keep fixtures separate from real integration evidence.

## Delivery blocker

The connected Git/connector identity is `evgrotz`. Git push to `procopio420/rodada` returned HTTP 403 (write permission denied); updating PR metadata through the GitHub connector also returned 403. Local commits are preserved, but the remote PR has not received them. CI on the completed branch and merge are therefore unverified and blocked. Grant repository write access or connect an authorized account, then push `feat/web-pixel-perfect`, check the exact resulting head and merge only after green checks. No merge SHA or deployment is claimed.
