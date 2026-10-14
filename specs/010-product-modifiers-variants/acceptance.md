# Acceptance — Spec 010

## Simple product backward compatibility

**Given** a Product with no variants or modifier groups  
**When** staff adds it  
**Then** it can still quick-add and confirm exactly as before.

## Required variant

**Given** a Product with P/M/G variants and no default  
**When** staff attempts to confirm without a variant  
**Then** server rejects with VARIANT_REQUIRED and creates no OrderItem/Charge.

## Required modifier

**Given** a SINGLE group “Ponto” with min=1 max=1  
**When** no option is selected  
**Then** confirmation is rejected.

## Multi-select bounds

**Given** “Adicionais” min=0 max=3  
**When** four options are submitted by a modified client  
**Then** server rejects regardless of UI state.

## Price calculation

**Given** base price 3000 cents, variant +500 and modifiers +300 +0  
**When** the item is confirmed  
**Then** unit price snapshot is exactly 3800 cents and no floating-point calculation is used.

## Zero-price removal

**Given** “SEM cebola” is an AVAILABLE REMOVE option priced 0  
**When** selected  
**Then** it appears in the confirmed snapshot and production display without changing price.

## Stale availability

**Given** bacon extra was selectable when cart opened  
**When** it becomes UNAVAILABLE before confirmation  
**Then** server rejects the bacon selection, identifies the affected option and does not silently remove/substitute it.

## Parent availability

**Given** ProductAvailability is UNAVAILABLE  
**When** a client submits otherwise valid variant/modifiers  
**Then** the Product cannot be confirmed.

## Snapshot immutability

**Given** a confirmed OrderItem with “Grande + bacon”  
**When** the Product, variant name or modifier price later changes  
**Then** historical OrderItem still displays the original names and cents.

## Post-confirm change

**Given** a confirmed item  
**When** customer asks to remove bacon  
**Then** the existing snapshot is not mutated; correction follows Spec 017.

## Production routing

**Given** a Product routed to KITCHEN with modifiers  
**When** confirmed  
**Then** it remains one KITCHEN OrderItem with structured preparation text; no hidden BAR work is created by a modifier.

## Permission denial

**Given** station staff without catalog-config capability  
**When** they attempt to edit modifier group structure  
**Then** backend denies it.

## Authorized availability

**Given** kitchen staff authorized for the Product station  
**When** they mark a modifier option unavailable  
**Then** actor/time/old/new state are audited and staff/guest receive realtime invalidation.

## Concurrency

**Given** availability changes concurrently with order confirmation  
**When** database validation sees the option unavailable before commit  
**Then** no invalid OrderItem/Charge is committed.

## Idempotency

**Given** a customized order confirmation times out client-side  
**When** the exact idempotency key is retried  
**Then** only one OrderItem and one financial effect exist.

## Guest UX

**Given** required choices exist  
**When** guest taps Add  
**Then** a compact choice flow opens; unavailable choices are labeled, price impact is visible, and notes remain secondary.

## Implementation evidence — 2026-10-09

All business evidence below uses actual Django/API persistence. Browser workflow
coverage forwards to the API; visual fixtures are used only for layout/a11y checks.

| Acceptance | Evidence |
| --- | --- |
| Simple product / integer cents / quantity | `test_customization.test_zero_price_removal_and_simple_product`, existing ordering foundation, native CustomizationTest |
| Variants / required / single / multi / min / max | `test_validation_rejects_entire_order`, `test_minimum_multi_and_foreign_option_and_http_note_length`, native CustomizationTest |
| Product, variant and option gates | `test_variant_parent_and_option_active_gates`, existing stale Product tests |
| Pre-upgrade retry compatibility | `test_pre_upgrade_simple_order_fingerprint_still_replays` preserves the deployed simple-product fingerprint |
| Concurrent option availability / duplicate requests | PostgreSQL `test_customization_concurrency` (two transactions/connections, no SQLite substitute) |
| Immutable labels/cents/IDs/routing | `test_complete_persisted_burger_guest_kitchen_and_availability`, `test_snapshot_fields_cannot_be_mutated_through_model_save` |
| House Account limit / submitted-price tampering | `test_limit_includes_modifiers_and_ignores_client_price` |
| Partial payment / idempotent refund | Complete persisted burger scenario: 7600 consumption → 4600 after payment → 5600 after a 1000 refund; replay has one refund |
| Guest / native / backend parity | Shared schema equality and 3800 unit / 7600 quantity total in backend and Kotlin acceptance tests; real browser selector/pricer confirmed by API |
| Production / notes / removals | ProductionQueue snapshot equality and routing; `customization.spec.ts` visual/a11y tests at 360, 390 and 768px |
| Management / association / defaults / ordering | Real manager UI in `z-customization.spec.ts`; unique default and association priority test; editor visual/a11y tests at 360/390px |
| Permissions / Venue isolation / optimistic concurrency | `test_cross_venue_and_permissions_and_optimistic_versions` |
| Remake / correction compatibility | `test_remake_preserves_configuration_without_second_exposure` and existing corrections suite |
| Stale cart / retry after restart | Exact option ID in server rejection; visible client invalidation, explicit removal of unavailable selections; native full intent JSON round-trip |

### Demonstrated burger scenario

Manager creates Hambúrguer through the existing resolve-or-create contract, adds
Simples (2000) and Duplo (3000), required Ponto and optional Bacon (500) / Queijo
(300). Staff selects Duplo + Ao ponto + both extras with “Molho separado”, quantity
2. The server snapshots 3800 per unit, 7600 total and one Charge. Exact retry returns
the same Order. Kitchen receives the complete snapshot; a separate guest session
orders the same selection through the same pipeline. Bacon becomes unavailable and
new confirmation is rejected with its option ID; retry of the already confirmed
intent succeeds. Renaming/repricing/deleting choices and changing catalog routing
do not alter existing items. Partial payment, refund and House Account calculations
continue through the canonical ledger. The real browser scenario independently
creates and configures a burger via Gerência and confirms staff/guest totals.

### Operational boundaries

- Catalog availability is authoritative immediately at confirmation; UI refresh uses
  existing Web polling (5s) and Android polling (15s/resume/reconnect). SSE is not
  added in this branch.
- Modifier quantities/duplicate options, negative option deltas, ingredient stock,
  SKU matrices and Spec 011 discounts/service charge are outside P0.
- Dedicated variant/modifier sales-mix analytics is a follow-up. AuditEvents already
  retain configuration and availability history.
- No connected physical Android device/emulator walkthrough is claimed; native
  unit tests, debug APK build and lint are the native validation gates.

### Final gate results

- Backend: **221 tests pass on PostgreSQL 17, no skips**, including real row-lock
  races, legacy retries, corrections, ledger, House Account and full-shift smoke.
  SQLite regression run also passed (216 tests at that point, 9 PostgreSQL-only
  skips); the final ordering/customization focused run passed 25 tests.
- Migrations: all migrations applied to a fresh dedicated PostgreSQL database;
  `makemigrations --check --dry-run` reports no changes.
- Android: **32 unit tests pass**, `assembleDebug` and `lintDebug` pass.
- Web: TypeScript check and optimized production build pass.
- Web visual: **116 tests pass**, including six dedicated customization/editor
  layout/a11y tests; reference comparisons remain strict and no baseline was reset.
- Browser integration: **6 tests pass against PostgreSQL**, including the manager →
  guest → kitchen customization/availability workflow. The SQLite integration run
  also passed 6 tests; PostgreSQL is the concurrency evidence.

Generated Web images/reports remain in `apps/web/test-results/`,
`apps/web/playwright-report/` and `visual-artifacts/`. Native APK and unit/lint reports
remain in `apps/attendance-android/app/build/`. These build outputs are not committed.

### T08a — evidência de repetição
- [x] Android preserva IDs/nota, valida catálogo atual e bloqueia seleção removida/indisponível/legado; preço atual e snapshot histórico imutável comprovados em unitários e PostgreSQL.
- [ ] Journey completa Android/API e repetição Web/guest.

### T08b — repetição staff Web local
- [x] Snapshot com IDs, seleção e preço atuais, diferenças explícitas, bloqueios de legado/produto/configuração inválidos e configuração distinta do default comprovados em testes de navegador. Original preservado na jornada PostgreSQL.
- [ ] Repetição guest/Web POS e verificação publicada.

### T08c — evidência local guest
- [x] Revisão atual por IDs/preço/configuração, sem defaults; cancelar preserva draft e inclusão não envia.
- [x] Releitura impede visita/Tab/token divergentes e bloqueio/revogação/falha/conteúdo alterado; configuração distinta não se funde.
- [x] PostgreSQL/Web em 360/390/430: nova intenção, resposta perdida/replay sem duplicação, histórico/Payments preservados; bloqueio de mesa após revisão impede inclusão.

Detalhes, checks completos e limites em specs/026-operational-ux-friction/revalidation.md.

### T08d — repetição no PDV Web
- [x] Revisão por IDs/preço/configuração atuais, exclusões e bloqueios, sem defaults ou envio automático.
- [x] Cancelamento/falha preservam draft; inclusão única na mesma Tab; personalização, recebimento ambíguo, encerramento e conteúdo alterado bloqueiam repetição.
- [x] Web/API PostgreSQL 360/390/430: preço atual, nova intenção, replay sem duplicação, histórico/snapshot/Payments e draft da outra Tab preservados.
- [x] 371 testes visuais PASS (7,2 min), tipos/build e diff finais PASS; sem alteração de baseline/tolerância.

### T09a — quantidade guest local
- [x] +/− acessíveis, zero remove, agrupamento por configuração idêntica e edição conserva quantidade; limite 99 rejeita inclusão/edição/repetição inteira sem perder draft.
- [x] Variantes/opções/notas diferentes permanecem distintas, ordem de option IDs não cria configuração nova; controles e payload pendente preservados nos bloqueios.
- [x] Web/API PostgreSQL 360/390/430: quantidade agrupada enviada uma vez, replay idêntico, exposição/charges corretos e Payments preservados; bloqueio real de mesa em 390.
- [x] 385 testes visuais PASS (7,3 min), tipos/build/diff PASS; resultado final e limites em Spec 026/revalidation.md.

### T09b — evidência local guest
- [x] Busca global por nome, acentos/caixa/espaços nas bordas, categorias consistentes, retorno ao limpar, fallback e vazio; fixture de 146 produtos.
- [x] Filtros/atalho preservam configuração, quantidade, draft e intent; indisponibilidade, bloqueio e revogação respeitados; primeira inclusão não desloca catálogo.
- [x] Web/API PostgreSQL 360/390/430: categoria real, seleção cruzando filtros, bloqueio de mesa, foco/draft e replay sem duplicar Order/Charge.
- [x] 393 testes visuais PASS (7,6 min), Ruff/tipos/build/diff PASS; detalhes na Spec 026. Não implica paridade global, aparelho físico ou publicação.

T10b/Spec026: resumo separa variação/modificador/nota/semântica confirmados, mantém legado independente e não consulta configuração atual para reconstruir preparo. Validar igualdade independentemente de preço/quantidade, mobile e Web/API PostgreSQL.

Evidência T10b local:5 unitários,6 Web/API PostgreSQL,47 PostgreSQL e408 visuais completos PASS; tipos/build/diff PASS. Lote e validação publicada permanecem pendentes; detalhes na revalidation da Spec026.


### T10c.1 — API de lote (evidência local)
- [x] Lote compatível, replay imutável e rejeição integral por estado/quantidade/snapshot/configuração/Venue.
- [x] Concorrência, rollback de Dispatch, auditoria por comando e preservação financeira em PostgreSQL.
- [x] T10c.2: revisão e recuperação Web mobile entregue em slice própria; não faz parte de T10c.1.

Evidência T10c.1: 96 testes PostgreSQL PASS (108.595s), incluindo 17 testes novos
de lote, Dispatch, ordering, turno completo, customização, ledger/Payments e
concorrência financeira/correções/pedidos. Django check/migration drift, compilação
Python, tipos Web e diff PASS. Ruff dos arquivos novos PASS; os arquivos existentes
models/views/urls mantêm 12 avisos (10 RUF012/2 I001), reproduzidos em HEAD ad5d64f.
Não houve alteração de UI: visual/build Web e jornada browser/mobile não executados
nesta slice. Log: visual-artifacts/spec026/runtime/t10c-postgres-final.log.

### T10c.2 — evidência local
- [x] Seleção explícita e revisão obsoleta bloqueada; sem auto-preparo.
- [x] Envelope anterior ao envio, replay original, sessão/armazenamento/readback protegidos e resultado por linha.
- [x] Web/API PostgreSQL mobile360/390/430, tipos/build/visual completo sem relaxar baselines.

T10c.2:425 visuais completos PASS (8.9m), incluindo17 de lote, mais1 teste
de volume51/limite50 executado separadamente após discovery;6 Web/API PostgreSQL
PASS (50.1s),49 PostgreSQL PASS (66.270s),5 unitários, tipos/build/diff PASS.
Sem baseline/tolerância novos. Capturas fixture/reais360 inspecionadas;390/430
cobertas por testes. Ledger/Payments/snapshots e12 comandos/12 auditorias/24
transições/12 entregas verificados na base exclusiva de teste. Não há script
Web lint/test genérico; executados test:visual/test:integration/test:production
por CLI Node documentada. UX23/T10d, aparelho, piloto e publicação seguem abertos.

### T10d.1 — evidência local
- [x] Itens verificados distintos avançam independentemente; mesmo item/lote/legado protegidos.
- [x] Intenções persistidas sobrevivem mudança de estado/reload; replay original, rejeição e falha isolados.
- [x] Web/API mobile PostgreSQL, regressões financeiras, tipos/build/visual completo.

438 visuais completos PASS (9.4m),29 focados,6 Web/API PostgreSQL (1.0m),
49 PostgreSQL (70.813s),5 unitários,tipos/build/diff PASS. Sem baseline/tolerância
novos. Base exclusiva:18 comandos/18 auditorias/18 transições de comando,
6 transições de setup,12 entregas,6 Payments; replay,ledger e snapshots preservados.
Capturas fixture/reais360 inspecionadas;360/390/430 testados nas duas estações.
Logs:visual-artifacts/spec026/runtime/t10d1-{focused,integration,postgres-tests,
readback,build,visual}.log. Web não possui script test/lint genérico.
UX23/T10d parcial; lote/legado/disponibilidade permanecem protegidos. Próximo
recorte T10d.2. Aparelho,piloto,tempo humano e publicação não verificados.

### T10d.2 — evidência local
- [x] Item fora do lote avança; linhas selecionadas e barreiras conservadas.
- [x] Journals separados e vinculados à sessão; replay/readback preservados.
- [x] Web/API PostgreSQL mobile, regressões financeiras, tipos/build/visual completo.

447 visuais completos PASS (9.2m),38 focados PASS (51.1s),6 Web/API PostgreSQL
PASS (1.1m),49 PostgreSQL PASS (68.929s),5 unitários,tipos/build final/diff PASS.
Sem alteração de baseline/tolerância/export. 360/390/430 nas duas estações;
capturas fixture360 inspecionadas. Base exclusiva:18 comandos/18 auditorias,
30 transições,12 entregas,6 Payments; command_id/ledger/snapshots preservados.
Logs:visual-artifacts/spec026/runtime/t10d2-{focused,integration,postgres-tests,
readback,build-final,visual-final}.log. Sem script Web test/lint genérico.
UX23/T10d parcial; próximo T10d.3: investigar disponibilidade por produto,
versionamento e recuperação antes de liberar esse escopo. Legado/QuickCatalog
e novo lote durante pendência conservam barreiras. Aparelho/piloto/publicação
não verificados; sem commit/push/merge/deploy.
