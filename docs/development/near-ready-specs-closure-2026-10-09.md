# Independent near-ready specs closure — 2026-10-09

Branch: `feat/close-near-ready-005-008-010`. Base: `origin/main`
`23babc640f6818c3caf29fd158a2c12fcd860f21`, fetched again before delivery;
no upstream advancement at that check. Dedicated worktree:
`C:/Users/Erick Grotz/Documents/Projetos/Rodada/.worktrees/near-ready`.

| Spec | Final status | Outstanding acceptance |
| --- | --- | --- |
| 005 | COMPLETE_WITH_EXTERNAL_VALIDATION_PENDING | Real provider output/style approval at 48×48, provider credentials unavailable. |
| 008 | INCOMPLETE | Native original-session replay envelope needs Agent 3/4 coordination; physical BYOD/no-NFC/revocation walkthrough also pending. |
| 010 | COMPLETE | Owned acceptance verified; read-only mix service delivered. Management endpoint/UI integration is Agent 2's follow-up. |

These are acceptance-scope conclusions, not a production/release certification.
Acceptance text below is copied verbatim from the existing criteria; historical
verification sections/checkmarks were not treated as proof. A section with several
Given/Then scenarios remains one row, with all scenario text included.

## Implementation delivered

- 005: new regression uses the actual unconfigured HTTP adapter (no mock generator)
  and durable worker. Three failed attempts preserve Product availability and a
  real staff Order; upload/reset retain one ProductIcon. Existing generation,
  privacy, regeneration, upgrade and concurrent creation tests reexecuted.
- 008: first authenticated installation emits `auth.device_registered` exactly
  once with actor/session/device and minimal metadata. A version conflict returns
  Venue-scoped current membership ID/role/status/version. Real HTTP BYOD/replacement,
  independent device revoke/reinstall, membership suspension/revoke, refresh,
  lock/expiry, direct refund denial and recent-auth/idempotency tests added.
  Two PostgreSQL connections prove one role-update winner and one conflict.
- 010: `ordering.customization_mix.selection_mix` is an internal, read-only
  projection from immutable confirmed snapshots. It counts quantities, retains
  label/price revisions and deleted choices, exposes modifier attach denominators,
  handles legacy items and cancellations explicitly, and excludes correction-created
  children. Existing realtime audit bridge already fans out shared option changes;
  new tests verify visibility, stale-version rejection and atomic rollback.

No migrations, ledger/pricing semantics, management screens, Android navigation,
design tokens, visual infrastructure or CI files were changed.

## Reproduction and validation

Environment: Windows, Python 3.12.14 bundled runtime, Django 5.2.18, Node 24.19.0 bundled
runtime, PostgreSQL 17.6 official portable binaries. A disposable localhost-only
cluster at `127.0.0.1:55449` uses dedicated `rodada_customization_test` and
`rodada_web_e2e` databases. No existing database was seeded/modified.

| Gate | Result |
| --- | --- |
| Django check, SQLite and PostgreSQL | PASS, zero issues/silenced checks |
| Migration drift, SQLite and PostgreSQL | PASS, no changes detected |
| Catalog/Auth/Customization/Ordering PostgreSQL focused gate | 113 passed, zero failed/skipped (117.93s) |
| Final additional closure/concurrency run | 18 passed, zero failed/skipped; includes two availability/order races and original-session replay helper |
| BYOD final run including real refund deny/reauth/retry, next mutation after switch and valid guest isolation | 11 passed (24.25s), zero failed/skipped |
| API full SQLite regression | 333 passed, 20 failed, 27 skipped (494.26s) under Windows cp1252; all 20 failed printing snapshots pass on UTF-8 retry (20 passed, 0 failed, 0 skipped, 0.46s) |
| Web typecheck and production build | PASS (Turbopack), no source/config changes required |
| Real Web workflows against PostgreSQL | 9 passed, zero failed/skipped; Quick Catalog/upload/reset, auth denial/expiry, customization guest → kitchen, pricing/cash/printing workflows |
| Focused visual/accessibility | 9 passed, zero failed/skipped; Quick Catalog 360/390/430 and customization/adjacent editor, unchanged baselines |
| Ruff on new service/tests; diff whitespace check | PASS |
| Android JVM/build/lint | Not rerun: no Android files changed; no local JDK/SDK configured. Source/manifest inspected; no device/emulator validation claimed. |
| Real generated artwork | EXTERNAL_BLOCKED: runtime provider key not available; fixture upload/decoder tests are not art approval. |

Commands from `apps/api` (use the bundled Python executable on this host):

```sh
python manage.py check --settings=rodada_api.settings_customization_postgres
python manage.py makemigrations --check --dry-run --settings=rodada_api.settings_customization_postgres
python -m pytest tests/test_access_api.py tests/test_access_models.py tests/test_access_permissions.py tests/test_access_capabilities.py tests/test_access_security.py tests/test_access_management.py tests/test_access_invalidation.py tests/test_byod_closure.py tests/test_icon_closure.py tests/test_quick_catalog.py tests/test_catalog_upgrade.py tests/test_catalog_models.py tests/test_customization.py tests/test_customization_concurrency.py tests/test_customization_mix.py tests/test_customization_events.py tests/test_ordering_foundation.py --ds=rodada_api.settings_customization_postgres -rA
PYTHONUTF8=1 python -m pytest -rA
```

Web: `node node_modules/typescript/bin/tsc --noEmit`,
`node node_modules/next/dist/bin/next build`, and existing Playwright entrypoints.
Real integration environment: `RODADA_TEST_PYTHON=<bundled Python>`,
`RODADA_E2E_POSTGRES=1`, `POSTGRES_DB=rodada_web_e2e`, `POSTGRES_PORT=55449`,
`POSTGRES_HOST=127.0.0.1`, `RODADA_E2E_API_PORT=8215`, `RODADA_E2E_WEB_PORT=3215`.
Visual environment: `RODADA_VISUAL_PORT=3216`, `RODADA_REFERENCE_PORT=3217`,
a local python3 command alias; command filters `quick-catalog.spec.ts customization.spec.ts`.
Logs live in ignored `.validation/` in the worktree; summarized results are retained here.

### Failed intermediate checks (resolved or explicitly bounded)

- New test helper initially collided with Django's `self.client`; corrected in
  this new file before product-gap verification. Reproduction then showed **2 failed,
  4 passed, 1 PostgreSQL skip**: absent registration audit/current conflict state.
  Both regressions pass after the two Access fixes.
- First sandboxed broader SQLite attempt: **15 failed, 89 passed, 4 skipped,
  8 teardown errors**. Image/temp operations failed with Windows sandbox permission
  denial. Reexecuted outside sandbox; PostgreSQL initial suite: **109 passed**,
  no skips. No assertion or provider behavior was changed to bypass the denial.
- An initial new invalidation test incorrectly expected a detailed event payload.
  Existing shared bridge deliberately emits empty invalidations and reloads canonical
  Catalog. Corrected that new test to assert this documented privacy boundary;
  no shared bridge modification or extra publication was made.
- First Web build rejected an external node_modules junction. Dependencies were
  copied into the worktree; the normal production build passed unchanged.
- PostgreSQL-specific tests are explicitly skipped by the SQLite suite and are
  executed with real row locks in the PostgreSQL gate.

## Criterion evidence

References below name repository files or Python module/functions. `PG` means the successful focused PostgreSQL
gate; `Web` means the 9 real integration flows; `Visual` means the 9 focused layout
checks. Provider and physical-device gates never inherit PASS from fixtures.


### Spec 005

| Spec | Criterion (exact acceptance text) | Status | Implementation | Validation | Remaining work | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| 005 | Staff autorizado em Bar/Cozinha possui ação **+ Item**. | PASS | apps/web/components/quick-catalog.tsx | Web quick-catalog.spec.ts; Visual Quick Catalog | None | You |
| 005 | Campo de nome oferece autocomplete de Products existentes do Venue. | PASS | catalog.services.suggestions; apps/web/components/quick-catalog.tsx | test_fuzzy_suggestions_never_merge_and_are_venue_scoped; Web | None | You |
| 005 | Sugestões mostram nome, preço, estação, disponibilidade e ProductIcon. | PASS | catalog.serializers.product_payload; quick-catalog.tsx | test_suggestions_show_shared_product_details; Visual | None | You |
| 005 | Selecionar sugestão existente reutiliza o mesmo Product e o mesmo ProductIcon. | PASS | catalog.services.resolve_or_create_product | test_exact_normalized_match_reuses_product_icon_and_all_configuration; Web | None | You |
| 005 | Correspondência exata normalizada não cria Product duplicado. | PASS | catalog.models.normalize_product_name; Product constraint | test_exact_normalized_match_reuses_product_icon_and_all_configuration | None | You |
| 005 | Sem correspondência exata, UI oferece **Criar "{nome}"**. | PASS | apps/web/components/quick-catalog.tsx | Web quick-catalog.spec.ts | None | You |
| 005 | Confirmar nome novo executa resolve-or-create atômico e converge para um único Product em corrida concorrente. | PASS | catalog.models.Product.save; resolve_or_create_product | ConcurrentCatalogTests.test_postgres_concurrent_creation_and_worker_transaction_boundary (PG) | None | You |
| 005 | Quick create herda a FulfillmentStation atual. | PASS | apps/web/components/quick-catalog.tsx | Web quick-catalog.spec.ts asserts BAR | None | You |
| 005 | Nome e preço são suficientes para concluir Product novo no fluxo rápido. | PASS | catalog.serializers.QuickProductInput | Web quick-catalog.spec.ts | None | You |
| 005 | Product e ProductIcon 1:1 são criados juntos. | PASS | catalog.models.Product.save; ProductIcon OneToOne | test_exact_normalized_match_reuses_product_icon_and_all_configuration; test_icon_closure | None | You |
| 005 | Criar Product não depende da disponibilidade do provider de IA. | PASS | catalog.services.run_icon_job; generator.HttpIconGenerator | test_icon_closure real unconfigured adapter | None | You |
| 005 | Salvar Product novo sem upload manual inicia geração de ícone automaticamente, sem botão/toggle de geração. | PASS | catalog.models.Product.save; catalog.services.enqueue_icon | test_creation_never_calls_provider_and_timeout_keeps_sellable_product; Web | None | You |
| 005 | Enquanto gera, Product continua utilizável com placeholder ou ícone anterior. | PASS | catalog.services.run_icon_job; apps/web/components/product-icon.tsx | test_creation_never_calls_provider_and_timeout_keeps_sellable_product; Web | None | You |
| 005 | Falha de geração não altera disponibilidade nem impede pedidos. | PASS | catalog.services.run_icon_job; ordering.services.confirm_order | test_icon_closure; test_guest_staff_reference_and_ordering_survive_ai_failure | None | You |
| 005 | Asset gerado segue contrato 1:1, sem texto e adequado a tamanho pequeno. | EXTERNAL_BLOCKED | catalog.style.STYLE_CONTRACT; docs/product/icon-style.md | Square upload/decoder and rendering verified; real art at 48×48 not generated | Configure valid provider; review actual 48×48 artwork for safe area, style, legibility, text/logos | External |
| 005 | Primeira geração bem-sucedida é publicada automaticamente quando ainda não existe asset. | PASS | catalog.services.run_icon_job | test_deduplication_and_privacy_allowlist | None | You |
| 005 | Regeneração excepcional em edição não remove o ícone publicado atual até o novo ficar pronto. | PASS | catalog.services.enqueue_icon/run_icon_job | test_regeneration_retains_asset_and_alias_is_idempotent_after_completion; test_failed_regeneration_keeps_published_asset | None | You |
| 005 | Usuário pode substituir por upload manual. | PASS | catalog.services.replace_icon | test_validated_upload_and_public_asset_retrieval; Web decoded preview | None | You |
| 005 | Usuário pode remover o ícone e voltar ao placeholder. | PASS | catalog.services.replace_icon | test_upload_and_reset_fence_inflight_jobs; Web | None | You |
| 005 | Autocomplete, Staff, Bar/Cozinha e Guest usam a mesma referência de ProductIcon publicada. | PASS | catalog.serializers.icon_payload; apps/web/components/product-icon.tsx | test_guest_staff_reference_and_ordering_survive_ai_failure; Web | None | You |
| 005 | Renomear Product não cria outro ProductIcon nem perde o vínculo 1:1. | PASS | catalog.models.ProductIcon; catalog.views.ProductEditView | test_edits_preserve_icon_and_uploaded_assets | None | You |
| 005 | Alterar preço/disponibilidade não altera a identidade visual do Product. | PASS | catalog.models.ProductIcon | test_exact_normalized_match_reuses_product_icon_and_all_configuration; test_edits_preserve_icon_and_uploaded_assets | None | You |
| 005 | Provider/model/prompt/style_version ficam rastreáveis para geração. | PASS | catalog.models.IconGeneration; services.run_icon_job | test_deduplication_and_privacy_allowlist; real gateway adapter contract test | None | You |
| 005 | Nenhum dado de Customer/Tab/Order é enviado ao gerador. | PASS | catalog.style.product_context | test_deduplication_and_privacy_allowlist (explicit allowlist) | None | You |
| 005 | Geração possui rate limit, idempotência e deduplicação por conteúdo relevante + style version. | PASS | catalog.services.enqueue_icon/run_icon_job | test_manager_rate_limit; test_deduplication_and_privacy_allowlist; regeneration alias/revision tests | None | You |
| 005 | Fuzzy match nunca mescla dois Products automaticamente. | PASS | catalog.services.suggestions/resolve_or_create_product | test_fuzzy_suggestions_never_merge_and_are_venue_scoped | None | You |

### Spec 008

| Spec | Criterion (exact acceptance text) | Status | Implementation | Validation | Remaining work | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| 008 | Authentication happy path<br>**Given** an ACTIVE StaffMember membership in a Venue and a new Android app installation never registered with Rodada  <br>**When** the staff member enters a valid PIN  <br>**Then** the backend registers the installation automatically as UNTRUSTED, issues a staff session scoped to that Venue and the app shows the current operator without manager approval. | EXTERNAL_BLOCKED | access.services._complete_login; Android AuthApp/AuthViewModel | ByodClosureTests.test_first_untrusted_login_orders_and_records_registration_and_domain_provenance (PG); source enters AttendanceScreen for any nonnull session | Physical Android first login/operator display walkthrough | External |
| 008 | BYOD device trust does not block routine work<br>**Given** an authenticated waiter on a personal Android installation with trust state UNTRUSTED  <br>**When** they view Tabs, confirm orders or perform another ordinary operation their membership authorizes  <br>**Then** the server evaluates staff capabilities and succeeds without a device-trust promotion or approval screen.<br><br>**And given** a valid login on another previously unknown installation  <br>**Then** it also succeeds without manager intervention; previous installations are not required to be removed first. | PASS | access.services._complete_login; ordering.views | BYOD first order and test_replacement_phone_operates_while_old_installation_remains_active (PG) | None | You |
| 008 | Revocation scope and reinstall<br>**Given** a registered installation is REVOKED  <br>**When** its existing sessions refresh or mutate  <br>**Then** they are denied, regardless of the employee's role.<br><br>**And given** the same employee still has an ACTIVE membership and authenticates from a distinct, newly registered installation  <br>**Then** the new session is evaluated normally; the old device revocation is not falsely treated as a physical-device ban.<br><br>**And given** the membership is SUSPENDED or REVOKED  <br>**Then** login and mutations are denied from every installation. | PASS | access.services.update_device_trust_admin/update_membership_admin | BYOD installation revoke/reinstall and membership suspend/revoke scenarios (PG) | None | You |
| 008 | Payment eligibility is independent<br>**Given** a waiter authenticated on an Android phone lacking NFC, a supported PSP SDK or required provider provisioning  <br>**When** they use Rodada Atendimento  <br>**Then** normal orders and Tabs still work, while Tap on Phone is unavailable and supported payment fallbacks remain discoverable. | EXTERNAL_BLOCKED | AndroidManifest.xml; AuthApp; operations payment gate | API UNTRUSTED orders PASS; manifest NFC feature required=false; no auth NFC/PSP gate in source | Physical no-NFC phone: login, Tab/order, unavailable Tap and discoverable payment fallback | External |
| 008 | BYOD privacy and fallback<br>**Given** an employee uses their personal phone  <br>**Then** the POS does not require MDM enrollment, access to unrelated personal content or continuous location tracking to authenticate and serve orders.<br><br>**And given** the personal device is unavailable or unsuitable  <br>**Then** the Venue can serve the same customer via an authorized shared/loaner device or cashier flow. | EXTERNAL_BLOCKED | AndroidManifest.xml; InstallationIdStore; SecureSessionStore | Source: random installation UUID; INTERNET/NETWORK_STATE/NFC only, no contacts/photos/location/MDM; API independent installations PASS | Venue operator demonstrates authorized loaner/shared or cashier fallback and physical privacy UX | External |
| 008 | Permission denial<br>**Given** a STAFF user without refund capability  <br>**When** they call the refund mutation directly, bypassing UI hiding  <br>**Then** the backend rejects it with CAPABILITY_REQUIRED and creates no Refund or financial effect. | PASS | access.permissions.RequireCapability; ledger.views | BYOD test_refund_direct_denial_reauthentication_and_exact_retry; no Refund before authorization (PG) | None | You |
| 008 | Fast operator switching<br>**Given** a trusted shared device currently used by Ana  <br>**When** Bruno selects his identity and authenticates with his PIN  <br>**Then** the next mutation is attributed to Bruno, not Ana, while the station/device context may remain. | PASS | access.services.switch_operator | BYOD test_shared_switch_next_order_has_new_operator_session_and_same_device; StaffSwitchAndReauthAPITests switch/supersede (PG) | None | You |
| 008 | Session expiry<br>**Given** an expired session  <br>**When** a mutation is attempted and refresh is no longer valid  <br>**Then** no domain mutation occurs and the client asks for authentication again. | PASS | access.services._session_failure; Web auth | BYOD test_untrusted_refresh_lock_and_expiry_never_mutate (PG); Web expired cookies workflow | None | You |
| 008 | Revoked membership<br>**Given** a MANAGER revokes a staff membership  <br>**When** an existing session next refreshes or performs a protected mutation  <br>**Then** authorization fails even if the client UI has not yet received realtime invalidation. | PASS | access.services.update_membership_admin/_session_failure | BYOD all-installation suspension/revocation; StaffAuthAPITests.test_revoked_membership_blocks_existing_session_and_refresh (PG) | None | You |
| 008 | Lost device<br>**Given** an OWNER revokes a lost trusted device  <br>**When** any session bound to that device attempts a new protected mutation  <br>**Then** it is rejected and the revocation is visible in audit history. | PASS | access.services.update_device_trust_admin | AccessManagementAPITests.test_trusting_device_then_revoking_it_kills_bound_sessions; BYOD revoke (PG) | None | You |
| 008 | Privileged reauthentication<br>**Given** an authorized manager whose recent-auth window expired  <br>**When** they attempt a refund  <br>**Then** the server returns REAUTH_REQUIRED; after successful reauthentication the same intended action can be retried without creating a duplicate refund. | PASS | access.permissions.RequireRecentReauthentication; services.reauthenticate_staff | BYOD direct refund denial/reauth/exact retry with one Refund (PG) | None | You |
| 008 | Connectivity loss<br>**Given** Atendimento goes offline with an active session  <br>**When** a command classified by Spec 014 as queueable is captured  <br>**Then** its original actor/session context is retained; on reconnect the backend reauthorizes it.<br><br>**And given** that membership was revoked before replay  <br>**Then** the command is rejected rather than reassigned or silently accepted. | PARTIAL | access.services.authorize_replayed_command; Android PendingMutationIntentStore/OperationsViewModel | Original-session helper rejects locked session after fresh login (PG); native envelope contains staff/venue/device but no session ID | Agent 3/4 coordinate original-session envelope and server replay wiring, then offline/reconnect/revoke integration test | Other Agent |
| 008 | Concurrency<br>**Given** two managers concurrently update the same membership role from the same version  <br>**When** both requests arrive  <br>**Then** only one update succeeds without conflict; the other receives the current membership state. | PASS | access.services.update_membership_admin; views._service_error_response | MembershipConcurrencyTests two connections/Barrier: one winner, current role/version on conflict (PG) | None | You |
| 008 | Audit verification<br>**Given** login, operator switch, device revoke and role change events  <br>**When** audit is queried  <br>**Then** each record identifies what happened, when, actor where applicable, Venue and device/session provenance without storing PIN/token material. | PASS | access.services._audit/_complete_login; audit.services | BYOD registration/domain provenance and privacy; existing switch, role and device audit tests (PG) | None | You |
| 008 | Guest separation<br>**Given** a valid GuestSession  <br>**When** it is supplied to a staff-only endpoint  <br>**Then** the request is rejected regardless of the guest's Tab access. | PASS | access.authentication; guest_access separate namespace | BYOD test_real_guest_session_cannot_use_staff_order_endpoint; StaffCredentialNamespaceTests credential namespace (PG) | None | You |
| 008 | Cross-Venue isolation<br>**Given** a StaffMember belongs to Venue A but not Venue B  <br>**When** they try to mutate Venue B  <br>**Then** authorization is denied and no cross-Venue data is changed. | PASS | access.permissions/services Venue scope | StaffAuthAPITests.test_cross_venue_login_requires_membership; AccessManagementAPITests.test_other_venue_resources_are_not_manageable (PG) | None | You |

### Spec 010

| Spec | Criterion (exact acceptance text) | Status | Implementation | Validation | Remaining work | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| 010 | Simple product backward compatibility<br>**Given** a Product with no variants or modifier groups  <br>**When** staff adds it  <br>**Then** it can still quick-add and confirm exactly as before. | PASS | catalog.customization.price_customization; ordering.services.confirm_order | test_zero_price_removal_and_simple_product; test_pre_upgrade_simple_order_fingerprint_still_replays (PG) | None | You |
| 010 | Required variant<br>**Given** a Product with P/M/G variants and no default  <br>**When** staff attempts to confirm without a variant  <br>**Then** server rejects with VARIANT_REQUIRED and creates no OrderItem/Charge. | PASS | catalog.customization.price_customization | test_validation_rejects_entire_order, VARIANT_REQUIRED without items/Charge (PG) | None | You |
| 010 | Required modifier<br>**Given** a SINGLE group “Ponto” with min=1 max=1  <br>**When** no option is selected  <br>**Then** confirmation is rejected. | PASS | catalog.customization.price_customization | test_validation_rejects_entire_order, MODIFIER_REQUIRED (PG) | None | You |
| 010 | Multi-select bounds<br>**Given** “Adicionais” min=0 max=3  <br>**When** four options are submitted by a modified client  <br>**Then** server rejects regardless of UI state. | PASS | catalog.customization.price_customization | test_validation_rejects_entire_order; test_minimum_multi_and_foreign_option_and_http_note_length (PG) | None | You |
| 010 | Price calculation<br>**Given** base price 3000 cents, variant +500 and modifiers +300 +0  <br>**When** the item is confirmed  <br>**Then** unit price snapshot is exactly 3800 cents and no floating-point calculation is used. | PASS | catalog.customization.price_customization | CustomizationMixTests.test_quantity_cents_zero_removal_and_replay_read_only: 3000 + variant delta500 +300 +0 =3800 (PG) | None | You |
| 010 | Zero-price removal<br>**Given** “SEM cebola” is an AVAILABLE REMOVE option priced 0  <br>**When** selected  <br>**Then** it appears in the confirmed snapshot and production display without changing price. | PASS | catalog.customization.price_customization; customization-text.tsx | test_zero_price_removal_and_simple_product (PG); Visual customization | None | You |
| 010 | Stale availability<br>**Given** bacon extra was selectable when cart opened  <br>**When** it becomes UNAVAILABLE before confirmation  <br>**Then** server rejects the bacon selection, identifies the affected option and does not silently remove/substitute it. | PASS | catalog.customization.price_customization | test_complete_persisted_burger_guest_kitchen_and_availability; Web z-customization exact stale choice (PG) | None | You |
| 010 | Parent availability<br>**Given** ProductAvailability is UNAVAILABLE  <br>**When** a client submits otherwise valid variant/modifiers  <br>**Then** the Product cannot be confirmed. | PASS | ordering.services.confirm_order ProductAvailability gate | OrderingFoundationTests.test_unavailable_product_blocks_whole_order (PG); variant-parent/active gates | None | You |
| 010 | Snapshot immutability<br>**Given** a confirmed OrderItem with “Grande + bacon”  <br>**When** the Product, variant name or modifier price later changes  <br>**Then** historical OrderItem still displays the original names and cents. | PASS | ordering.models.OrderItem.save; snapshots | test_complete_persisted_burger_guest_kitchen_and_availability; mix historical revisions/deleted choices (PG) | None | You |
| 010 | Post-confirm change<br>**Given** a confirmed item  <br>**When** customer asks to remove bacon  <br>**Then** the existing snapshot is not mutated; correction follows Spec 017. | PASS | ordering.models.OrderItem.save; corrections canonical services | test_snapshot_fields_cannot_be_mutated_through_model_save; test_remake_preserves_configuration_without_second_exposure (PG) | None | You |
| 010 | Production routing<br>**Given** a Product routed to KITCHEN with modifiers  <br>**When** confirmed  <br>**Then** it remains one KITCHEN OrderItem with structured preparation text; no hidden BAR work is created by a modifier. | PASS | OrderItem.fulfillment_station_snapshot; production queue | test_complete_persisted_burger_guest_kitchen_and_availability (PG); Web guest → kitchen; routing retained after Product changed to BAR | None | You |
| 010 | Permission denial<br>**Given** station staff without catalog-config capability  <br>**When** they attempt to edit modifier group structure  <br>**Then** backend denies it. | PASS | catalog.customization_views.CustomizationView permissions | test_cross_venue_and_permissions_and_optimistic_versions (PG) | None | You |
| 010 | Authorized availability<br>**Given** kitchen staff authorized for the Product station  <br>**When** they mark a modifier option unavailable  <br>**Then** actor/time/old/new state are audited and staff/guest receive realtime invalidation. | PASS | catalog.customization_views.ChoiceAvailabilityView; existing realtime.signals bridge | CustomizationEventTests shared-option Product fanout, guest/staff visibility, audit provenance, rollback (PG); Web stale refresh | None | You |
| 010 | Concurrency<br>**Given** availability changes concurrently with order confirmation  <br>**When** database validation sees the option unavailable before commit  <br>**Then** no invalid OrderItem/Charge is committed. | PASS | confirm_order Product locks; ChoiceAvailabilityView locks | CustomizationConcurrencyTests.test_availability_transaction_commits_before_blocked_confirmation_validates (PG, two connections) | None | You |
| 010 | Idempotency<br>**Given** a customized order confirmation times out client-side  <br>**When** the exact idempotency key is retried  <br>**Then** only one OrderItem and one financial effect exist. | PASS | ordering.services.confirm_order fingerprint/Charge | CustomizationConcurrencyTests.test_concurrent_identical_intents_charge_once; exact replay tests (PG) | None | You |
| 010 | Guest UX<br>**Given** required choices exist  <br>**When** guest taps Add  <br>**Then** a compact choice flow opens; unavailable choices are labeled, price impact is visible, and notes remain secondary. | PASS | apps/web/components/product-customization.tsx; guest-menu.tsx | Web z-customization.spec.ts real required/optional choices, prices, stale recovery; Visual customization | None | You |

## Handoffs and external gates

1. **Agent 3 + Agent 4 / Main Orchestrator — Spec 008 original session on replay.**
   `PendingMutationIntentStore.kt: RecoveryIntent/baseJson/loadFor` retains staff,
   Venue and device, not session. `OperationsViewModel.kt: selectTab/confirmOrder`
   rebuilds retained intent using the current `StoredSession`;
   `OperationsRepository.kt: confirmOrder` submits current authorization.
   Persist/validate the original session envelope, preserve it through refresh,
   reject expired/revoked original sessions before queued execution, and never
   reattribute an intent after logout/new login. Coordinate request-contract and
   recovery-policy changes with the orchestrator. Regression required: capture
   command, revoke/expire original session, login again on same installation,
   reconnect/replay; zero new domain/financial effects. The existing
   `authorize_replayed_command` helper already provides original-session denial,
   and its new-phone regression passes. No workflow/storage files owned by Agent 3
   were changed here. Spec 008 remains INCOMPLETE for this implementation dependency.

2. **Agent 2 — Spec 010 analytics integration.** Use
   `modules.ordering.customization_mix.selection_mix(venue_id=..., start=..., end=...)`.
   Add authorized read endpoint/cockpit binding in Management, converting business
   dates with the Venue's timezone/cutoff. Input bounds must be timezone-aware;
   end is exclusive. Output is deterministic gross selection facts; cancelled
   units are separate, correction children excluded, and label/price revisions
   preserved. `selected_units/product_units` supplies attach-rate inputs. Do not
   label snapshot base/delta totals as net sales or infer inventory consumption.
   No ledger joins/calculation changes or Management UI/report files are included.
   The task for a basic domain projection is complete; product-facing analytics
   belongs to the cockpit owner's scope.

3. **External/Main Orchestrator — Spec 005 art.** Follow Catalog README provider
   and persistent-storage/worker setup. Generate actual food/drink/branded-category
   examples with `rodada-icon-v1`; review at 48×48 across normal/unavailable/selected
   contexts for central 80% safe area, legibility, consistent style, no text/logos.
   Retain provider/model/job/asset evidence. No credentials were read or fabricated;
   deterministic solid fixtures prove storage/rendering only. Rendering components
   currently have their own layout sizes; no shared tokens were altered to make
   48px art acceptance appear passed.

4. **External/Venue operator — Spec 008 physical BYOD and fallback.** Demonstrate
   first PIN login on a fresh installation without approval, ordinary Tab/order on
   a no-NFC phone, replacement installation, remote revoke, app session termination,
   no personal-content/MDM request, and authorized shared/loaner or cashier service.
   Source review shows random installation identity, encrypted session storage,
   no contacts/photos/location permissions and NFC optional. API tests do not prove
   physical app behavior or actual Venue fallback readiness.

## Integration review

GitHub open-PR searches (repository-scoped and explicit `repo:... is:pr is:open`)
returned no open PRs at investigation/delivery check. Fetched remote branches were
inspected, including `feat/quick-catalog`, `impl/008-*`,
`feat/product-modifiers-variants`, `feat/operational-realtime`, release and visual
branches. They were treated as independent refs, not assumed merged or cherry-picked.
Existing managed worktrees belong to the orchestrator/other work; this checkout
does not modify them. `origin/main` remained at the base SHA on the final fetch.
Main Orchestrator owns integration/release validation and merging this PR.

Implementation commits: `2f6b8ab5379f1ad521d43f7f068912cc4fbab419` (Access), `fc555a36bbbcb3ed58cbf52484d71a590d8875ef` (selection mix), `8c37217` (exact switch/guest scenarios).

### Global regression locale diagnosis and exact skips

The initial quiet full run was interrupted after its 76% progress marker appeared
idle; it has no final PASS result. A verbose diagnostic retry completed all 380
collected tests: 333 passed, 20 failed, 27 skipped. Every failure was a parameter
of `tests/test_printing_snapshots.py::test_version_one_golden_outputs`: five
receipt kinds × widths 58/80 × original/copy. The fixture reads use implicit
`Path.read_text()` encoding; Windows default is cp1252. An unchanged-file retry
with `PYTHONUTF8=1` passed all 20 parameters in 0.46s. No source or fixture was
modified, no baseline changed, and no assertion suppressed. A 45-second diagnostic
stack also captured a slow local HTTP connection during the Tab E2E scenario;
that scenario subsequently passed. It was not a product-gap implementation.

The full retry was collected before the final two switch/valid-Guest tests were
added; those two are included in the final 11-test PostgreSQL BYOD run. There is
no claim of a fresh all-green full-suite process on the final 382-test collection.
Main Orchestrator/Agent 4 should use UTF-8 (or the Linux CI environment) for final
release-wide execution. Release-wide PostgreSQL financial/printing races remain
their gate; this branch's scoped PostgreSQL concurrency gate has no skips.

The 27 SQLite skips were exactly:

- `tests/test_byod_closure.py::MembershipConcurrencyTests::test_parallel_role_updates_only_one_wins_and_conflict_exposes_current_state`
- `tests/test_customization_concurrency.py::CustomizationConcurrencyTests::test_availability_transaction_commits_before_blocked_confirmation_validates`
- `tests/test_customization_concurrency.py::CustomizationConcurrencyTests::test_concurrent_identical_intents_charge_once`
- `tests/test_house_account.py::HouseConcurrencyTests::test_concurrent_orders_cannot_overspend`
- `tests/test_house_account.py::HouseConcurrencyTests::test_concurrent_replay_creates_one_order`
- `tests/test_payment_settlement_migration.py::SettlementOwnershipMigrationTests::test_existing_settlement_gets_owner_and_database_rejects_duplicate`
- `tests/test_payments_concurrency.py::PaymentConcurrencyTests::test_duplicate_intent_concurrent_confirmation_and_refund_reservation`
- `tests/test_payments_concurrency.py::PaymentConcurrencyTests::test_duplicate_webhooks_are_applied_once_under_postgres_inbox_lock`
- `tests/test_payments_concurrency.py::PaymentConcurrencyTests::test_one_transaction_cannot_settle_distinct_tabs_concurrently`
- `tests/test_payments_concurrency.py::PaymentConcurrencyTests::test_two_waiters_cannot_start_two_collections_against_one_balance`
- `tests/test_pricing_concurrency.py::PricingConcurrencyTests::test_concurrent_service_assessment_exactly_once`
- `tests/test_pricing_concurrency.py::PricingConcurrencyTests::test_discount_racing_payment_never_overcollects`
- `tests/test_pricing_concurrency.py::PricingConcurrencyTests::test_duplicate_request_one_fact_and_response`
- `tests/test_pricing_concurrency.py::PricingConcurrencyTests::test_postgres_append_only_and_allocation_sum`
- `tests/test_pricing_concurrency.py::PricingConcurrencyTests::test_two_distinct_adjustments_one_version`
- `tests/test_printing_concurrency.py::PrintConcurrencyTests::test_cross_endpoint_initial_production_dispatch_is_one_job`
- `tests/test_printing_concurrency.py::PrintConcurrencyTests::test_idempotent_creation_and_skip_locked_worker_claim`
- `tests/test_printing_concurrency.py::PrintConcurrencyTests::test_postgres_rejects_direct_snapshot_sql_update`
- `tests/test_printing_concurrency.py::PrintConcurrencyTests::test_same_reprint_command_is_audited_once`
- `tests/test_printing_concurrency.py::PrintConcurrencyTests::test_simultaneous_documents_and_different_initial_keys`
- `tests/test_quick_catalog.py::ConcurrentCatalogTests::test_postgres_concurrent_creation_and_worker_transaction_boundary`
- `tests/test_release_concurrency.py::ReleaseConcurrencyTests::test_distinct_manual_payments_cannot_overcollect_same_balance`
- `tests/test_release_concurrency.py::ReleaseConcurrencyTests::test_order_and_partial_shift_payment_preserve_limit_and_ledger`
- `tests/test_tab_operations.py::TabOperationConcurrency::test_two_concurrent_splits_cannot_overdraw`
- `tests/test_tab_operations.py::TabOperationRetryConcurrency::test_concurrent_identical_split_creates_destination_once`
- `tests/test_tab_operations.py::TabOperationRetryConcurrency::test_payment_and_split_share_the_financial_aggregate_lock`
- `tests/test_web_completion.py::CatalogConcurrencyTests::test_same_normalized_name_converges_under_concurrency`
