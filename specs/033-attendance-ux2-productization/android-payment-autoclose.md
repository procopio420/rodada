# E04/E06 — Full payment closes the Tab canonically

## Existing behavior and correction

Current main's ledger settles and closes the Tab when the confirmed payment
reduces exposure to zero. The native recovery engine already recognizes this
canonical CLOSED/zero state and avoids an additional Close mutation. Do not
change that engine or the backend financial policy.

The native full-payment page incorrectly offers “Só registrar; manter comanda
aberta”, which cannot be honored by this contract. Remove that contradictory
choice. Keep the single full receipt action; partial receipts remain available
and leave positive-balance Tabs open. Preserve payment intent/readback recovery.

## Evidence required

- Compose: full payment exposes only the closing action and original cash point;
  no misleading keep-open option. Pending confirmed recovery and zero-balance
  close remain covered.
- Real current-main + Spec033 API/PostgreSQL: partial payment leaves OPEN with
  canonical remaining balance, final payment yields CLOSED/zero, same exact two
  receipts and total, no extra Payment or unnecessary Close, cash shift unchanged.
- Independent R3 review, build/JVM/lint and emulator evidence. Old API18134
  behavior is not acceptable evidence of current payment settlement policy.

No merge/deploy, policy change, PSP/card/Pix settlement claim, or whole-E04
acceptance. Prototype simulation differs where it implies a fully paid Tab can
remain open: canonical financial contract takes precedence, difference recorded.

## Backend used for current-state evidence

Isolated worktree `ux2-native-payment-current-api` at `02d63ae8`, containing
current `origin/main` `20828711` plus Spec033 API/Web composition. Read-only
`showmigrations --plan` against local PG55501 reports no pending migration.
API18138/proxy18139; own synthetic tenant `spec033-native-autoclose-current`,
new operator/product/open drawer fixture only. No reset/flush or reuse of the
Marina/table08 operational fixture. Private runner config is mode0600 and
credentials are neither printed nor committed.

## Executed verification (source6145cade)

- 133 JVM zero failure/error/skip; Debug/AndroidTest assemble and lint PASS1m49s.
- Final test APK after ensureLoaded fixture correction: assemble PASS4s.
- Real API/PostgreSQL ViewModel regression:1/1 PASS13.861s, partial500 leaves
  OPEN/500, final500 yields CLOSED/zero, exactly2 confirmed payments/0ClosePOST.
- Compose account/receipt/zero-balance regressions:3/3 PASS14.31s,3 captures.
- Independent R3 other context reviewed source and final evidence:
  NO_FINDINGS_WITH_GAPS; misleading full-payment keep-open P1 resolved.

Evidence: docs/development/evidence/spec033-native-payment-autoclose/.
Remote main advanced to146233b3 during the run: tests prove backend02d63ae8
(descendant20828711) only; updated-main composition remains a separate gate.
