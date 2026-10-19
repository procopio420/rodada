# E06-03 — canonical CSV menu through the UX2 journey

Reuse the permanent opt-in integration test instead of treating its three skips
in the ordinary suite as evidence. The test-only delta replaces removed legacy
navigation with the existing contextual Tab helper, categorized catalog actions,
optional summary and canonical order confirmation. It also selects station cards
by their actual canonical reference plus the unique test label.

Preserve all existing business assertions: 143 imported products (112 BAR,
31 KITCHEN), Brahma 600 ml at 1200 cents, Coxinha de Queijo com Alho at 350 cents,
one order with two lines, exposure 1550 and payments zero. Both production queues
must require explicit NEW → PREPARING → READY actions. There is no product, API,
financial policy, retry or visual baseline change. The complete multi-surface
AC-20 remains pending beyond this Web/production evidence.

Run only with RODADA_E2E_MENU=1 in a disposable local PostgreSQL database named
rodada_web_e2e. Do not seed/reset any merchant or shared Android fixture. The
existing guarded CSV importer and per-file isolation are reused unchanged.
