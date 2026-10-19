# Existing receipt regressions aligned with canonical settlement

Source dc9eb695, base2fa7d535. Test-only; no financial policy or product changed.
The composed155-case run ended150PASS/2FAIL/3opt-in menu skips; its two failures
expected paidOPEN and new consumption after canonicalCLOSED. Original log retained.

Five real Django/PostgreSQLUTF8 tests PASS47.9s, no skips/retries. Includes POS
lostACK/drawer, full receipt lostACK+same-payload replay+confirmed checkpoint+
readback503+reload/no further Payment/zero Close, permission denial, genuine
partial+new consumption/keep-open, real UX2 partial/full page. One Payment effect
and CashShift exact movement/amount checks remain. Build and ESLint PASS.

Independent R3 reviewer /root/finish_menu_and_ci_review inspected source dc9eb695,
original failures and preserved assertions: NO_FINDINGS_WITH_GAPS, execution was
pending at initial review. Final log review remains required before integration
readiness. Agent review is not qualified GitHub approval. Full-composition rerun
and CI candidate still pending; no global UX2 acceptance/merge/deploy implied.
