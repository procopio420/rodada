# Web queue reconciliation — 2026-10-19

Candidate branch `reconcile/queue-web-20261019`, worktree `mission-web`. Base main `20828711208ec3e991d5dca8808b37eacd07c81f`. Historical attached logs keep their original SHA scope.

## Source mapping

- #261 head53966656 merged as d268d8c5; includes canonical automatic settlement fixes6ac9ab90/a58259ec and the composed Web chain through #254.
- #260 fae2dbb7/8d3a85e4 → a9cdb21c/a32ce36b (history origin, return focus, three-width read-only regression).
- #255 4bbc5d64/76350317/893746a5 → d6eb1fab/e2b152f5/f13acc73 (real canonical CSV menu journey and historical evidence).
- #219 1851ec4a →1f499a04. fb494fa4 obsolete UI selector patch was inspected during conflicts and skipped: current attendance.spec.ts and attendance-removal.spec.ts already scope confirmed lines to the canonical `Pedidos confirmados` region, preserving its intent with the current journey.
- #249 latest7d7f0c1e →be0ee333 retains the completed148-case historical run, without claiming it for this candidate.
- #253 aff4fffc hospitality source and tests are byte-identical to this candidate. Only API differences are #219 fulfillment_station_snapshot in order payload plus two foundation regressions. Dispatch API has zero delta from main, preserving #252 owner/claim contracts.
-97ce2587 requires a discriminated release dialog carrying its occupancy pair. Missing occupancy cannot create release confirmation; current-occupancy replacement disables confirmation; POST always uses captured values.

## Review correction

Independent reviewer `/root/review_253` identified a P1: an unsent draft prevented the explicit Close label but new full receipt could still automatically close canonically. Fix rejects newly prepared full-or-higher Attendance receipt before persistence/POST when draft prevents closure, preserving true partial receipts and all frozen pending recovery payloads. A new real PostgreSQL/browser regression exercises360/390/430, full+overpayment zero writes/intent, partial lost ACK exact replay with one Payment and the draft preserved. Test result follows final execution.

## Executed evidence

At97ce2587 before the draft correction: typecheck/build PASS; visual23/23 PASS45.3s covering history3, cash-context2, Dispatch freshness6, delivery9, release3; real PostgreSQL API26/26 PASS50.953s. Auth4, tenant10, gateway2 and Dispatch target unit cases passed.

Initial setup failure: Turbopack rejected an external node_modules symlink. Replaced it with local copied dependencies; no config change. An initial gateway run overlapped an unfinished build and got ECONNRESET; rerun after completed build passed2/2. An accidentally broad ESLint invocation hit18 existing management/component synchronous-effect errors; correct changed-file lint result is recorded separately.

Real database is exclusively synthetic `rodada_web_e2e` in dedicated local container `rodada-mission-web-e2e-20261019` on loopback55479; API8310/Web3310. No shared demo/production DB access.

No CI, GitHub approval, physical-device parity, pilot sign-off or production GO is inferred. No push, PR, merge or deploy executed by this worker.

## Final release-fence composition

417f3a9a merges parent #25394a4349e. Resolutions retain UX2 attendance-web's deferred recovery initialization/session scope, contextual table/queue pages, required captured dialog pair and stronger freshness/replacement guards. Queue acceptance keeps its migrated SERVICE_REQUEST contextual journey plus original occupancy release pair. Demo script uses parent253's identical original-pair contract and file mode. The realtime verification script now captures the original pair before release, byte-identical to253. API source delta beyond253 remains only fulfillment_station_snapshot. No Android resolution was edited; parent253 additions are inherited unchanged.

Current final Web source82bc4ca6 had build/typecheck and57-file focused ESLint PASS; visual23/23 final pass (see visual-final.log). Initial real15-case run had13PASS/2 explicit global30s timeouts; budgets now status60s/lifecycle120s without retries or assertion changes. Final integration startup failed on retained synthetic slug because ordinary startup assumes an empty disposable DB. This failure is preserved in integration-final.log; container-only reset and composed final integration are pending.

Independent reviewer identified the draft guard issue; fix source480b3824 and frozen-full follow-up08f5b5c9 supplied for re-review. Final merge417f3a9a resolution review/current CI remain pending.

## Follow-up after full validation — 2026-10-19

The initial composed integration reported three draft-summary selector failures
and two obsolete full-payment/open-Tab assumptions. Tests now inspect the actual
`1× product` summary, canonical automatic closure after lost POST response and
failed readback, original persisted payment phase, a single drawer movement and
zero redundant close calls. The concurrent-consumption fixture uses a genuinely
partial first receipt so the second Order is valid while the Tab is OPEN.

The full pre-reconciliation visual run had623 PASS and one stale catalog picker
selector. Reproducing it through the current category/product picker exposed a
real swallowed readback failure: `load` handled the exception without notifying
`rename`. The read now returns success/failure, and rename explicitly reports an
unconfirmed result when revalidation fails. The original negative success and
released-busy-state assertions remain. Focused catalog browser regression PASS;
typecheck/build PASS. Five financial PostgreSQL cases and full final visual
suite remain running when this entry was committed.

Independent read-only review `/root/review_253` examined this source/test delta:
NO_FINDINGS_WITH_GAPS; final gates still required. Generated pip egg-info changes
were excluded. Parent25312f8e2f6 test-only follow-ups are inherited without
changing reviewed Web product behavior.
