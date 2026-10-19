# E04/E06 — canonical auto settlement on main20828711

Product6ac9ab90, base02d63ae8. Independent review identified P1: full receipt
promised keep-open though main complete_paid_tab closes settleable paid Tabs.
Correction preserves backend policy and removes impossible full-payment action.
Matching canonical CLOSED/zero-balance readback finishes context for both intent
schemas, independently of close_requested. Unknown identity/balance keeps intent.
Payment and TableOccupancy are independent; this slice never releases a table.

Executed in isolated PostgreSQL55652/API8152/Web3152, own test tenant:
- Seven real integration tests PASS42.4s, zero retries/skips: lost ACK replay with
  same payload/one Payment/zero Close, partial plus concurrent consumption and
  callback failure, storage failure, schemas1/2, wrong identity, CLOSED nonzero.
- 13 browser regressions PASS29.7s including360/390/430 POS/cash context.
- Build/typecheck PASS; final ESLint zero diagnostics. Earlier five-case run PASS
  retained separately; later run adds two adversarial cases without weakening guards.
- Independent R3 reviewer /root/finish_menu_and_ci_review examined6ac9ab90,
  confirmed P1 resolved, NO_FINDINGS_WITH_GAPS; final test-only negatives and
  seven-case/13-browser logs reviewed at a58259ec with the same outcome.
  Review is not qualified GitHub approval.

Gaps: full composed suite on updated main, native auto-close impact, final visual
prototype comparison and pilot acceptance. Main changed financial lifecycle;
this documents the difference before acceptance, not authorization of intentional
prototype deviations. No merge/deploy. Main reconciliation/historical navigation
have their own slices. Static/targeted PASS does not prove global readiness.
