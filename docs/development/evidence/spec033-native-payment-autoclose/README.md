# Canonical full-payment auto-close — native E04/E06

Source6145cade, baseline de6fe8e8 (#256/#257 composition). Native full receipt
no longer offers an impossible keep-open choice. Partial receipts remain;
full receipt uses the existing canonical settlement/readback engine unchanged.

Backend evidence target: isolated immutable worktree at02d63ae8, descendant of
current main20828711 plus033 contracts. API18138/proxy18139, local PG55501,
dedicated new spec033-native-autoclose-current tenant/operator/product/drawer.
No reset/flush, no Marina/table08 data reused. showmigrations read-only has
zero pending migrations. Private runner config mode0600, not versioned/logged.

Native gates:133JVM zero failure/error/skip; assembleDebug, assembleDebugAndroidTest
and lintDebug PASS1m49s. Subsequent test-only ensureLoaded fixture correction
compiled AndroidTest APK PASS4s. No engine/backend financial policy changed.

Runtime: `live.log` PASS1/1,13.861s; `ui.log` PASS3/3,14.31s.
Exact method status records1/0 (no skips) verified by strict runner.
Canonical snapshot: partial500 left OPEN/500 exposure, final500 closed Tab
with zero exposure; two confirmed500 receipts against1000 charge.
`http-mutation-counts.json`:2 Payment POSTs, zero Close POSTs; cash shift OPEN.
`runtime-manifest.json` binds source6145cade/backend02d63ae8 and installed APK
hashes. Three native presentation screenshots are component fixtures, not
claims of real cash/PSP collection or full-screen prototype parity.

Infrastructure history: An infrastructure interruption removed the AVD and
API/proxy processes before initial installation; infra-device-missing.log is
not a test pass. Missing processes were authoritatively revalidated and restarted
without wiping emulator data or re-seeding shared DB. PostgreSQL stayed available.

Reproduction: run scripts/spec033-native-payment-fixture.py once in the current
backend checkout with the allowlisted local PG env; start18138 API and18139
scripts/spec033-native-payment-proxy.py; build native for18139, install-r APKs;
python scripts/android-native-autoclose.py --config <private-file> --output
this evidence directory. No real cash/provider settlement is claimed: synthetic
cash register operations only. Old API18134 OPEN semantics are not accepted here.

Independent R3 source6145cade and final live/UI/screenshots reviewed by
separate context: NO_FINDINGS_WITH_GAPS, P1 resolved. Reviewer did not run the
emulator and relies on inspected bound logs/artifacts; no GitHub approval.

Pending: CI, physical device/TalkBack,
prototype parity approval for canonical financial difference and whole-E04/pilot.
Other two legacy LiveReceipt18131 methods need later composition fixtures;
this slice targets the partial-to-full settlement regression only.

Remote main advanced to146233b3 during this run; backend evidence remains
precisely scoped to02d63ae8/ancestor20828711. Further composition and regression
against the updated main are still required; no current-main-wide acceptance.
