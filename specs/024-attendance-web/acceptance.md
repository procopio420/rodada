# Acceptance

## Pilot service queue — 2026-10-10
- [ ] Agora shows service/bill type, destination, server age (unknown when absent), and own/other/unassigned responsibility.
- [ ] Another operator's claim disables claim/completion; server conflict reloads authoritative ownership without success.
- [ ] Lost command response retains task/action for retry; no optimistic removal or new task is created.
- [ ] Initial read error/stale snapshot disables mutations and never reports a measured empty queue; recovered GET restores actions.
- [ ] Mobile long content passes touch/accessibility checks; financial gateway exclusions remain enforced.
1. Anonymous visitors see staff login; login enters Atendimento and logout clears it.
2. A comanda receives customized, quantity-aware orders in the canonical production pipeline.
3. Unavailable products cannot be confirmed; ambiguous retries use the original payload/key.
4. Delivery and table lifecycle commands use existing server contracts.
5. No payment controls or financial gateway commands; unpaid closure remains rejected.
6. Host and local route carry Atendimento metadata/manifest; mobile has no overflow.
7. Typecheck/build and mandatory visual suite pass; real API evidence is distinguished from fixtures.

## Verification — 2026-10-09

- TypeScript check and production Docker build passed.
- 10 real Django API integration tests passed using an isolated disposable SQLite
  database, including Atendimento ordering, production, delivery, table lifecycle,
  payment-gateway rejection, canonical unpaid-close rejection and logout.
- 7 focused browser checks against the final deployed Docker image passed, including
  360/390/430/1280px accessibility and layout, host identity, manifest, financial
  route rejection and exact-payload retry after catalog invalidation.
- Existing local PostgreSQL demo: Bia login, Contas rendering and logout passed at
  `http://localhost:3119/attendance`. No new financial demo commands were submitted.
- Full existing visual regression suite: 177 passed. The two additional retry/host
  checks were included in the seven focused final-image checks above.

The companion preserves order intents only while the page remains open; it has
no offline mutation queue or reload recovery. Plain LAN HTTP does not carry the
production secure session cookies; phone access needs an HTTPS proxy.
