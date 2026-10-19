# All Web PR coverage against candidate08f5b5c9
Checked ancestry first; residual commits by git cherry patch equivalence follow. Semantic exceptions documented separately.
## #219 `fb494fa40d81954d3dc3928e460b4c660a8b48c7` — PATCH/CONTENT VALIDATION
- RESIDUAL fb494fa4 test(attendance): scope confirmed line assertions to order history

## #221 `c5fe85ab626794feea10064fc0068fe09c7c53d1` — FULL HEAD ANCESTOR

## #224 `59809484c344ccf42900dba9e8e9146f1fba972f` — FULL HEAD ANCESTOR

## #225 `9f3a8be2a8334068a805fd3098b8377f3a423468` — FULL HEAD ANCESTOR

## #226 `eb3c634d3af059c1d48b8ce2aa05428f8dbe34ac` — FULL HEAD ANCESTOR

## #230 `d65cb7e183334e17bacb63c6684c9cb4ad22ea41` — FULL HEAD ANCESTOR

## #231 `bcde015b556bad5e37baa0de1c75bde4bb9c9fca` — FULL HEAD ANCESTOR

## #232 `be8a5f90e247950ac28e665a2630e232f0d7e126` — FULL HEAD ANCESTOR

## #235 `1cd60840c20944387a0958ef03c0cdabe16e4e68` — FULL HEAD ANCESTOR

## #238 `00001b443a61a0bfd80bdede07059c6444856e4f` — FULL HEAD ANCESTOR

## #239 `633aa3c9d639db34c9dfae709b38114a91481de5` — FULL HEAD ANCESTOR

## #240 `462d336a654235c6a170345cbe4d64e00171b57e` — FULL HEAD ANCESTOR

## #242 `37429cbd5210201d187ac05553d8a7b9f1a81d9e` — PATCH/CONTENT VALIDATION
- RESIDUAL f54482c0 test(web): send confirmed occupancy context in table release regressions
- RESIDUAL ffd4cb9e test(web): send confirmed occupancy context in table release regressions
- RESIDUAL 2eded610 test(web): preserve canonical occupancy preconditions for release
- RESIDUAL d120d4ef test(web): preserve canonical occupancy preconditions for release
- RESIDUAL b109fc6f test(web): bind workflow table release to original occupancy
- RESIDUAL 37429cbd fix(attendance): fence table release to confirmed occupancy context

## #243 `0f37fb03597a4c37c9f9477ae7d71cf6edb78064` — FULL HEAD ANCESTOR

## #245 `36f3444f9cb20810306182158f527114f95f457c` — FULL HEAD ANCESTOR

## #246 `ffa959b628732fa6e9a7cff3b24b154bd718dfb8` — FULL HEAD ANCESTOR

## #248 `5b9e7f97b1a3d12a08f2aff7ec346d2815ac2738` — FULL HEAD ANCESTOR

## #249 `7d7f0c1e5c9c47814bc0bfe36ca75380a7ce1b32` — PATCH/CONTENT VALIDATION

## #254 `1213420d966ebf5de09d2866d4b6d13fd5982f11` — FULL HEAD ANCESTOR

## #255 `893746a5072dd14460d6a4b16d99fa6d107ffd52` — PATCH/CONTENT VALIDATION

## #260 `8d3a85e408b4a83f045e833599b651638862f681` — PATCH/CONTENT VALIDATION

## #261 `5396665682911ec8e55301294f7c394c2e227f77` — FULL HEAD ANCESTOR

## Semantic mapping of non-equivalent historical patches

- #219 fb494fa4: both migrated tests already scope confirmed line assertions to `Pedidos confirmados`; preserving obsolete `Rodada 1` selectors would revert the UX2 test migration. attendance.spec.ts and attendance-removal.spec.ts retain their financial/order assertions.
- #242 f54482c0: table-turnover.spec.ts23-24 captures `originalOccupancy` at occupy and sends its pair at release.
- #242 ffd4cb9e: service-requests.spec.ts21/71 retains the original pair around guest revocation proof.
- #242 2eded610: guest-order-intent.spec.ts18/42 retains original pair in revoked recovery case.
- #242 d120d4ef: attendance-queue-acceptance.spec.ts37/103 retains original pair around canonical service queue proof.
- #242 b109fc6f: workflows.spec.ts83/142 and219/269 capture the original occupancy once for both real guest workflows and send that pair on release.
- #242 37429cbd: its historical implementation re-read occupancy at confirmation. Candidate97ce2587 deliberately strengthens this: pair captured when the dialog opens, discriminated type requires both fields, replacement invalidates confirmation, and submit uses the captured pair. Real replacement race and visual gate retain zero writes when stale.

These mappings establish code/test-content preservation at this candidate SHA. Tests execute separately; they do not establish a global pilot acceptance or justify closure before the candidate merges.

## Release candidate update417f3a9a

#253 head94a4349e is now a full head ancestor. All older Web ancestry/patch mappings above remain valid. API release, realtime consumer script and native parent fence additions are inherited unchanged; only conflict resolutions in UX2 attendance shell/queue test and equivalent demo Python mapping were required.
