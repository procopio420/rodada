# Rodada — code-quality cleanup and zero-debt acceptance

**Campaign branch:** `chore/quality-debt-eradication`, stacked on [#129](https://github.com/procopio420/rodada/pull/129). **Tracking PR:** [#133](https://github.com/procopio420/rodada/pull/133). No main merge, deploy, production migration or Play release is authorized by this campaign.

## Measured starting point (PR #129 CI, 2026-10-13)

| Area | Diagnostic baseline | Source |
| --- | ---: | --- |
| API Ruff `E4,E7,E9,F` | 69 | API run 38486428548 |
| Web ESLint Next/TypeScript | 90 | Web run 38486428679 |
| Android `lintDebug` | Blocking gate passed | Android run 38486428579 |
| Android Kotlin compiler | 4 file-level warnings (Locale x2, redundant `!!`, clipboard) | Android run 38486428579 |

**Total 159** is a count of static diagnostics, *not* independently confirmed production defects. It is not a universal assessment of architectural debt. The [reproducible inventory](../../scripts/quality/debt_inventory.py) writes `findings.json` and `summary.md`, uploaded as `code-quality-inventory` in the existing Web workflow. Re-run it on the actual head SHA before citing remaining counts.

### Initial rule distribution

- Ruff: E402 23, E702 12, E701 11, F405 8, F401 7, E731 3, F403 2, F811 2, E741 1.
- Web: `react-hooks/refs` 51, `react-hooks/set-state-in-effect` 27, `react-hooks/exhaustive-deps` 3, `react-hooks/immutability` 2, `@typescript-eslint/no-unused-expressions` 2, and five distinct single-rule diagnostics.
- Web hotspots: `components/order-workspace.tsx` (39 findings), `components/guest-ordering.tsx` (14), `components/house-account.tsx` (10).

## Execution order and ownership

1. **API baseline zero:** preserve Django settings exports and model registry side effects; remove dead imports, move ordinary imports to file top, split multiple statements and replace assigned lambdas with functions. Run `ruff check apps/api --select E4,E7,E9,F` and complete PostgreSQL suite; compare resulting inventory to baseline.
2. **Android safety:** clean compiler warnings, clipboard API, and money formatting without floating-point round-trips; run `testDebugUnitTest`, `assembleDebug`, `lintDebug`. Distinguish Gradle/toolchain deprecation notices from Kotlin/app warnings. Preserve release signing checks.
3. **Web easy findings:** remove dead expressions/variables and `prefer-const` safely. Keep full TypeScript check, Next build, BFF integration and visual/a11y suites.
4. **Web React Hooks refactor:** replace render-time `ref.current` reads with explicit committed React state (but retain refs for synchronous in-flight idempotency guards in event handlers); untangle effects into fetch/lifecycle boundaries without losing draft recovery, tab context, money idempotency or session revocation. Group by independent surface: `order-workspace`, `guest-ordering`, `house-account`, then other components. **Do not just suppress `react-hooks/refs` and `set-state-in-effect`.**
5. **Architecture beyond lint:** identify complexity, duplicate contracts, circular dependencies and oversized multi-responsibility modules. Candidate areas: Android `AttendanceScreen.kt` (65 KB), `OperationsViewModel.kt` (53 KB), API `access/services.py` (31 KB), `corrections/services.py` (29 KB), Web `order-workspace.tsx` (28 KB). These are investigation triggers, not proof of a defect. Refactor in independently testable slices.
6. **Promote strict gates:** when *actual* Ruff and ESLint totals on the same reviewed SHA reach **0**, change API CI to full blocking Ruff and Web CI to `npm run lint` full blocking, then remove the interim added-line-only allowances. Keep the separate dangerous-directive guard. Preserve workflow path filters and avoid parallel duplicate full suites.

## Non-negotiable invariants

- Financial values remain integer cents at domain/storage boundaries; confirmed payments never inferred from network success, and idempotency, settlement, refund and append-only ledger semantics stay intact.
- Tenant/Venue boundaries cannot weaken, including async SSE, host resolution, Web BFF and Android native transport.
- Offline draft recovery, replay, in-flight request blocking and session invalidation must retain existing behavior.
- No use of `eslint-disable`, `@ts-ignore`, `noqa`, `as any`, `|| true` or snapshots updates merely to force green. Narrow explicit Django-star-import exceptions are allowed only when exports are required by Django's settings convention, with comments.
- No destructive operation on shared demo/production, real venue fixtures, production credential reads, or merge/deploy without separate authorization.

## Release-grade evidence

Each cleanup PR reports its **head SHA**, `findings.json` before/after by rule/file, exact test commands and run URLs, and separately records **NOT RUN** for missing cross-device/hardware/manual acceptance. A green incremental PR gate is not proof of baseline zero, and no zero-debt claim is valid before both full lint commands succeed. Changes to money/tenant/recovery/CI require review by another agent/session or human per [Code Review](CODE-REVIEW.md).

**Completion:** API full Ruff 0, Web full ESLint 0, TypeScript/build 0, Android unit/build/lint pass with reviewed warnings, full PostgreSQL + BFF + visual tests passing, independent R3 review, and no unexplained critical regressions. Architecture improvements can be tracked as separately scoped work when zero is not demonstrable from automated tools.
