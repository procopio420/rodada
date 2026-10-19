# E06-03 — real CSV menu integration

Candidate source: `4bbc5d6483964add44a95844db975bfa44a39b22`, branch
`test/033-venue-menu-navigation`, base `87306a677c63ca934fd4caed186545b78986d154`
(PR #249). Source-only test migration; product binaries are unchanged.

Executed with Django and PostgreSQL 17 in a newly created, dedicated local
cluster `rodada033-menu-resume-pg`, port55649, disposable DB `rodada_web_e2e`,
API8148 and Web3148. No shared Android/demo/customer database was reset.

```sh
RODADA_E2E_MENU=1 RODADA_E2E_POSTGRES=1 POSTGRES_HOST=127.0.0.1 \
POSTGRES_PORT=55649 POSTGRES_DB=rodada_web_e2e POSTGRES_USER=rodada_menu \
RODADA_TEST_PYTHON=/home/lucas/projects/rodada/venv/bin/python \
RODADA_E2E_API_PORT=8148 RODADA_E2E_WEB_PORT=3148 \
./node_modules/.bin/playwright test --config playwright.integration.config.ts venue-menu-acceptance.spec.ts
```

Results: **3/3 passed, zero skipped, zero retries, 1.4 minutes**.
360px18.4s, 390px14.2s, 430px15.4s. Each creates one actual two-line order after
contextual Tab creation and optional summary. It checks 143 CSV products,
112 BAR/31 KITCHEN, prices1200/350, exposure1550, payments0, and explicit
PREPARING/READY transitions in both production interfaces. The nine screenshots
are real test-Venue UI; they do not alone prove full prototype parity.

ESLint and typecheck passed on the migrated test. `build.log` records the prior
successful build of the identical product source in this worktree; changing a
test does not change that binary. No new visual baseline, product component,
financial policy, endpoint, replay behavior or assertion timeout was altered;
the full multi-surface journey uses a90-second overall budget.

An initial resumed run terminated during startup because the pre-existing
cluster55648 had an unknown role. It did not seed or reset that cluster. The
successful run uses the new cluster identified above. Earlier failed legacy-UI
iterations are not counted as passes.

Independent review: `/root`, separate from author `/root/finish_menu_and_ci_review`,
examined source4bbc5d64, helpers, fixture/reset semantics and every retained
business assertion. Outcome `NO_FINDINGS_WITH_GAPS`, sem achados reproduzíveis.
This agent review is not a GitHub approval. Candidate CI, updated-main integration
and formal GitHub approval remain separate gates. AC-20/22/24 and the complete
E06-03 task stay pending: this slice proves Web/Bar/Kitchen only, without native
Android, financial settlement, Guest QR, physical hardware or pilot sign-off.
No merge/deploy was performed.
