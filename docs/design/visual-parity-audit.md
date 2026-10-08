# Visual parity audit — Web/PWA

Date: 2026-10-08
Reference: `prototype/index.html` + `prototype/design-system.css`
Implementation: `apps/web`

## Canonical contract

`apps/web/app/globals.css` is the Web/PWA implementation of the executable
prototype token contract. Product CSS consumes semantic custom properties; it
does not define per-screen color, radius, spacing, or touch-target values.

| Area | Before in Web | Canonical prototype value |
| --- | --- | --- |
| Application background | `#171512` | `#0f100e` |
| Main surface | `#211e1a` | `#191b17` |
| Control surface | `#2b2721` | `#24261f` |
| Accent | `#f2b84b` | `#f2c14e` |
| Primary control | implicit 48 px | 50 px |
| Standard touch target | implicit 48 px | 44 px |
| Shell side inset | 20 px | 16 px (24 px at 620 px+) |
| Font | Inter-first | system UI, 15 px / 1.4 |

The one intentional component-level exception is the disabled ProductIcon
placeholder text. The prototype's `--color-text-subtle` fails WCAG AA contrast
on `--color-surface-2`; the Web component uses `--color-text-muted` instead.
This preserves the visual hierarchy while satisfying the design system's
accessibility requirement.

## Surface inventory and mapping

| Actual surface | Route | Prototype mapping | Status |
| --- | --- | --- | --- |
| Staff authentication | `/staff` | none | Shared canonical styling applied; no direct reference exists. |
| Bar production | `/bar` | Cozinha station pattern | Canonical production queue, availability, loading/empty/error states. No direct Bar prototype. |
| Cozinha production | `/kitchen` | `#kitchen` | Partial, API-backed counterpart. Header, panels, fields, status, buttons, empty/loading/error states and tokens aligned. |
| Cliente / guest ordering | `/guest/[token]` | none | Shared canonical styling applied; no direct guest reference exists. |
| Gerência | `/manage` | none | Mobile-first bottom navigation and shared primitives aligned. No direct management reference exists. |
| Cash operations | `/cash` | none | Shared operational/financial primitives aligned. |
| Refunds | `/refunds` | none | Shared warning, field, panel and action primitives aligned. |
| Legacy Web POS | `/pos` | prototype PDV conceptual only | Audited but not used as a parity target: Atendimento is Android native under ADR 0007. It remains API-backed and visually uses the shared contract. |

The static prototype also contains Dispatch and Conta da Casa concepts. There is
no corresponding Web/PWA route in this codebase; they are not claimed as
pixel-perfect Web parity targets. The prototype Quick Catalog create flow has
no connected Web API/UI implementation. Cozinha/Bar render an explicitly
disabled visual shell and limitation notice rather than a fake mutation.

## Shared vocabulary standardized

The Web contract now provides one implementation for AppShell, ProductHeader,
Panel (including semantic left-edge variants), Field, Button, StatusBadge,
DataRow, InlineNotice, ProductIcon placeholder, EmptyState, loading state,
money/tabular-number treatment, guest cart and management bottom navigation.

`ProductionBoard` consumes these primitives for both Cozinha and Bar. Its
availability toggle and order-state mutations remain the existing API-backed
operations. It adds visible `AVAILABLE`/`UNAVAILABLE`, `NEW`/`PREPARING`/`READY`,
loading, empty, saving and failure states; no domain behavior was replaced.

## Screenshot comparison

The Playwright suite renders:

1. `prototype/index.html`, switches to its Cozinha state, and captures the
   reference.
2. The real `/kitchen` page against deterministic intercepted API responses.
3. Reference, actual, pixel diff, side-by-side image and JSON statistics.

Artifacts are written to the ignored `visual-artifacts/` directory so they are
available locally without bloating Git. The test fixes Chromium, locale,
timezone, scale factor, viewport and fixture data, and removes animation.

Latest measured 390 × 844 comparison:

| Reference | Actual | Changed pixels | Difference |
| --- | --- | ---: | ---: |
| Prototype Cozinha | API-backed `/kitchen` | 29,260 / 329,160 | 8.8893% |

This is explicitly a **partial-reference guard**, capped at 9.5%, not a claim
of pixel-perfect completion: the production screen does not yet have the
prototype's functional Quick Catalog flow and its live queue structure is not
the static prototype's identical DOM. The test must not be "fixed" by raising
the limit or accepting a new baseline without correcting a documented visual
difference.

The suite also captures `/kitchen` at 360, 390, 430, 768 and 1280 px, asserts
zero horizontal overflow, verifies an operational action is visible, and runs
axe with no detected violations for that deterministic state.

## Reproduction

```bash
cd apps/web
npm install
npx playwright install chromium
npm run typecheck
npm run test:visual
npm run build
```

Open `visual-artifacts/kitchen-390.side-by-side.png` and
`visual-artifacts/kitchen-390.diff.png` after the visual run. The matching
statistics are in `visual-artifacts/kitchen-390.stats.json`.

## Remaining gaps

- No direct prototype exists for Staff, Client, Gerência, Cash, Refunds or Bar.
  Their visual parity can only be asserted against the shared design contract,
  not an invented reference image.
- Quick Catalog is intentionally not a working mutation in the Web production
  board yet. Connect the specified autocomplete/resolve-or-create contract
  before declaring Kitchen/Bar fully comparable to the prototype.
- The static prototype's PDV, Dispatch and Conta da Casa screens are not Web
  implementation targets in the current architecture. Do not recreate Android
  Atendimento in React merely to make a screenshot compare.

## Drift prevention

- Change tokens in the prototype contract and Web contract together; run
  `npm run test:visual` before approving any Web UI change.
- Add a direct reference fixture and strict near-zero diff assertion when a
  screen has matching production functionality. Do not replace a reference
  image to hide a regression.
- Keep screenshots ignored and commit the test, fixture data and measured audit
  instead.
