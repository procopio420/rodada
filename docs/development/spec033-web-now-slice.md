# Spec033 — Web Agora / shell slice

Contract: PR216 `specs/033-attendance-ux2-productization/`, E01-03/04/06,
E03-04/06/07. Visual reference PR212 `ec26e26b164692b1e22e0fc1b7c7c45d401a7ca0`.
Base: origin/main `dcb3a795`. Depends on PR218 additive staff task projection;
new workspace presentation is a separate dependent slice. No merge or deployment.

Existing: table selection validates canonical assignment, order workspace keeps
per-Tab drafts and intents, service queue has claim/completion recovery, delivery
queue and table lifecycle commands are functional. Those engines are reused.
Changes: Agora is entry; separate queue selector and counts; canonical read-only
task opening; contextual table page; fixed three-action navigation; destination
picker; searchable no-table Tabs; scoped PR212 palette and measurements.
No navigation claims/completes a task or creates a Tab.

## Evidence and remaining gates

- `npm run typecheck`, `npm run build`: PASS locally.
- `npm run test:auth`: 4 PASS. `npm run test:tenant`: 10 PASS.
- `node --experimental-strip-types --test tests/dispatch-target.test.mjs`: 3 PASS.
- Real PostgreSQL port55635 / isolated `rodada_web_e2e`, Django PR218 `52244ecd`
  at18135 and actual BFF/Next at32635: `ux2-now.spec.ts` 5 PASS after table-page / queue-verb followup on `d30751cd`. Covers360/390/430/1280, context/filter return,
  no writes during navigation, real request remains OPEN/unclaimed after opening.
- Full `npm run test:visual` invoked, interrupted after first3 legacy attendance
  tests failed on replaced navigation selectors. NOT PASS. Existing regression
  suites need journey-preserving migration to new UX and complete execution.
- Reference and real screenshots produced in `docs/development/spec033-web-now-evidence/`.
  Prototype inspected at all4 widths. These show different fixture populations;
  not an equivalent-state pixel parity PASS. Initial inspection found inherited
  uppercase/condensed heading; corrected by scoped normal case/stretch.
- New contextual-task component is pending root workspace slot integration,
  mounted recovery tests and independent R3 review. It is not acceptance evidence.

## Parity matrix

| Screen/state | Prototype | Web | Android | Differences | Result |
| --- | --- | --- | --- | --- | --- |
| Header / bottom nav | inspected360/390/430/1280 | rendered real login | separate owner | live venue/staff instead of demo meta; native gate pending | partial |
| Agora calls | three demo tasks | canonical requests and TABLE fallback | separate owner | safe Tab label projection pending; contextual actions integration pending | partial |
| Agora deliveries | four demo items | canonical READY tasks/detail | separate owner | separate page styling and station/title parity pending | partial |
| Mesas list | inspected | scoped grid/search and no-table list | separate owner | financial balances intentionally not invented; summary endpoint carries identity only | partial |
| Mesa context | inspected | page reuses existing commands | separate owner | advanced organization and lifecycle flow parity pending | partial |

Financial/domain divergences remain explicit: prototype blocks release when Tabs
are open, whereas existing canonical backend supports independent occupancy release
without closing Tabs. This slice preserves the backend contract and does not claim
that divergence approved/resolved. Table summary endpoint deliberately omits
financial positions to avoid N+1; no fake zero balance is rendered.

Physical Android device, full native parity, complete E2E, independent review,
CI, operator homologation and pilot remain pending. No Epic/AC is marked complete.
