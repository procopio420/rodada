# Specs 023/024 — reconciliação estrutural com main (2026-10-14)

Esta commit de merge reconcilia a branch `codex/spec023-024-completion` com `main` em `e2b059100f24aba18777ca6648fa379f8b15fbb7`. **Não é homologação**, nem confirma os gates da Spec 023 ou a aceitação comercial da 024.

## Estratégia

- Das 265 diferenças de branch em relação à base `8afd1200c7fd3047e82939486e6b6afc84b14c7f`: 86 já tinham conteúdo idêntico à main; 72 foram incorporadas (incluindo a correção de 401/reautenticação no `OperationsHttpClient`); 107 arquivos divergentes preservaram o conteúdo mais atual de `main`.
- Todo o histórico original permanece preservado como pai da commit de merge; as versões anteriores podem ser comparadas e reaproveitadas sem perder evidências.
- Priorizou-se evitar substituir fluxos modernos de idempotência, recuperação, isolamento de tenant, lifecycle de mesa, pagamentos e UI por implementações mais antigas.
- **As 107 divergências selecionadas pelo lado de main não significam equivalência funcional**. É necessário reconciliar requisitos/asserções ainda não portados antes de concluir Spec 023/024. Este PR permanece draft e não deve ser mergeado até os gates finais.

## Arquivos que requerem confirmação de paridade funcional

- `.github/workflows/android-live-post-drop.yml`
- `.github/workflows/android.yml`
- `.github/workflows/web.yml`
- `README.md`
- `apps/api/modules/hospitality/views.py`
- `apps/api/modules/ledger/services.py`
- `apps/api/rodada_api/urls.py`
- `apps/api/tests/test_availability_commands.py`
- `apps/api/tests/test_corrections.py`
- `apps/api/tests/test_hospitality_tables.py`
- `apps/api/tests/test_ledger_payments.py`
- `apps/api/tests/test_order_intent_concurrency.py`
- `apps/api/tests/test_ordering_foundation.py`
- `apps/api/tests/test_payments_concurrency.py`
- `apps/api/tests/test_production_batches.py`
- `apps/api/tests/test_tab_location_safety.py`
- `apps/attendance-android/README.md`
- `apps/attendance-android/app/src/androidTest/java/com/rodada/attendance/operations/TableReleaseTest.kt`
- `apps/attendance-android/app/src/androidTest/java/com/rodada/attendance/ui/AttendanceNavigationTest.kt`
- `apps/attendance-android/app/src/main/java/com/rodada/attendance/operations/AttendanceScreen.kt`
- `apps/attendance-android/app/src/main/java/com/rodada/attendance/operations/OperationsModels.kt`
- `apps/attendance-android/app/src/main/java/com/rodada/attendance/operations/OperationsViewModel.kt`
- `apps/attendance-android/app/src/main/java/com/rodada/attendance/operations/RecoveryPresentation.kt`
- `apps/attendance-android/app/src/main/java/com/rodada/attendance/operations/TablesScreen.kt`
- `apps/attendance-android/app/src/main/java/com/rodada/attendance/ui/AttendanceNavigation.kt`
- `apps/attendance-android/app/src/test/java/com/rodada/attendance/operations/RecoveryPresentationTest.kt`
- `apps/web/README.md`
- `apps/web/app/api/attendance/[...path]/route.ts`
- `apps/web/app/refunds/page.tsx`
- `apps/web/components/attendance-web.tsx`
- `apps/web/components/guest-ordering.tsx`
- `apps/web/components/order-workspace.tsx`
- `apps/web/components/pos-cash-receipt.tsx`
- `apps/web/components/production-board.tsx`
- `apps/web/components/tab-location-move.tsx`
- `apps/web/lib/client/availability-intents.ts`
- `apps/web/lib/client/guest-order-intent.ts`
- `apps/web/lib/client/manual-refund-intent.ts`
- `apps/web/lib/client/order-intent.ts`
- `apps/web/lib/client/production-batch-intent.ts`
- `apps/web/lib/client/production-item-intents.ts`
- `apps/web/package.json`
- `apps/web/tests/integration/attendance-removal.spec.ts`
- `apps/web/tests/integration/attendance.spec.ts`
- `apps/web/tests/integration/availability-intents.spec.ts`
- `apps/web/tests/integration/correction-without-refund.spec.ts`
- `apps/web/tests/integration/developer-staff.spec.ts`
- `apps/web/tests/integration/frontend-pilot.spec.ts`
- `apps/web/tests/integration/guest-catalog.spec.ts`
- `apps/web/tests/integration/guest-order-intent.spec.ts`
- `apps/web/tests/integration/guest-quantity.spec.ts`
- `apps/web/tests/integration/guest-repeat-order.spec.ts`
- `apps/web/tests/integration/management-alerts.spec.ts`
- `apps/web/tests/integration/manual-refund-intent.spec.ts`
- `apps/web/tests/integration/order-intent.spec.ts`
- `apps/web/tests/integration/pos-cash-receipt.spec.ts`
- `apps/web/tests/integration/pos-repeat-order.spec.ts`
- `apps/web/tests/integration/printing.spec.ts`
- `apps/web/tests/integration/production-batch.spec.ts`
- `apps/web/tests/integration/production-configuration.spec.ts`
- `apps/web/tests/integration/production-item-intents.spec.ts`
- `apps/web/tests/integration/production-regions.spec.ts`
- `apps/web/tests/integration/quick-catalog.spec.ts`
- `apps/web/tests/integration/repeat-order.spec.ts`
- `apps/web/tests/integration/service-requests.spec.ts`
- `apps/web/tests/integration/start_api.py`
- `apps/web/tests/integration/tab-drafts.spec.ts`
- `apps/web/tests/integration/tab-location-move.spec.ts`
- `apps/web/tests/integration/tab-pagination.spec.ts`
- `apps/web/tests/integration/tab-search.spec.ts`
- `apps/web/tests/integration/table-entry.spec.ts`
- `apps/web/tests/integration/workflows.spec.ts`
- `apps/web/tests/integration/z-customization.spec.ts`
- `apps/web/tests/integration/zz-pricing.spec.ts`
- `apps/web/tests/visual/availability-intents.spec.ts`
- `apps/web/tests/visual/guest-repeat-order.spec.ts`
- `apps/web/tests/visual/order-intent.spec.ts`
- `apps/web/tests/visual/parity.spec.ts`
- `apps/web/tests/visual/pos-repeat-order.spec.ts`
- `apps/web/tests/visual/production-batch-independent.spec.ts`
- `apps/web/tests/visual/production-batch.spec.ts`
- `apps/web/tests/visual/production-item-intents.spec.ts`
- `apps/web/tests/visual/repeat-order.spec.ts`
- `apps/web/tests/visual/tab-drafts.spec.ts`
- `apps/web/tests/visual/tab-location-move.spec.ts`
- `apps/web/tests/visual/table-entry.spec.ts`
- `docs/design/system.md`
- `scripts/android-post-drop-proxy.py`
- `specs/001-core-pos/acceptance.md`
- `specs/006-payments-tap-on-phone/acceptance.md`
- `specs/006-payments-tap-on-phone/spec.md`
- `specs/012-cash-management/acceptance.md`
- `specs/012-cash-management/plan.md`
- `specs/012-cash-management/spec.md`
- `specs/014-connectivity-degraded-operation/acceptance.md`
- `specs/014-connectivity-degraded-operation/spec.md`
- `specs/017-order-corrections-exceptions/acceptance.md`
- `specs/017-order-corrections-exceptions/plan.md`
- `specs/017-order-corrections-exceptions/spec.md`
- `specs/023-updated-prototype-visual-parity/acceptance.md`
- `specs/023-updated-prototype-visual-parity/plan.md`
- `specs/023-updated-prototype-visual-parity/spec.md`
- `specs/026-operational-ux-friction/acceptance.md`
- `specs/026-operational-ux-friction/plan.md`
- `specs/026-operational-ux-friction/revalidation.md`
- `specs/026-operational-ux-friction/spec.md`
- `specs/026-operational-ux-friction/tasks.md`

## Gates obrigatórios antes de merge

1. API real/PostgreSQL, migrações, regras de dinheiro/tenant e negativa de concorrência/idempotência.
2. Web typecheck, lint, build, integration e Playwright visual, incluindo guest, produção, recuperação e acessibilidade.
3. Android unit, lint, build e instrumentação real de navegação, recovery, autenticação e mudança de mesa.
4. Matriz Spec 023 de comparação integral de HTML ↔ Compose e fidelidade V02–V07 (não confundir testes visuais parciais com aceite).
5. Menu Spec 024: homologação comercial externa do catálogo, preços e roteamento; sem publicação em produção.

Este merge encerra o **conflito estrutural Git**, não os riscos funcionais documentados.
