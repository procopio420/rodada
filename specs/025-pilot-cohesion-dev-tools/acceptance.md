# Aceite

Attendance styling follow-up (2026-10-12): production build/TypeScript and all 223 visual cases passed without baseline changes. Removal scenarios at 360/390/430 verify the product-specific accessible label, icon-only content, 44px touch target, focus restoration and unchanged lost-response/paid/advanced-stage safeguards. Closing still requires confirmation and canonical zero-balance restrictions. Inspected the 390px screenshot; captures are attendance-sections-360/390/430.png under visual-artifacts/pilot-cohesion. Existing backend/payment behavior and POS presentation are preserved; no live order mutation. Local frontend restarted with the final build; Attendance HTTP200 verified.

Always-visible search (2026-10-12): production build/TypeScript passed. Mobile 360/390/430 checks confirm search remains visible with no expanded/selected category, typing reveals a product from another category, clearing restores collapse and draft remains intact. Full visual run: 222 passed, one unrelated Bar1440 accessibility evaluation timed out; that exact scenario passed unchanged in an isolated rerun (1.3s). All 223 cases covered without baseline/tolerance changes. Local frontend stopped before build and restarted afterward; Attendance HTTP200 verified.

Grouped Todos follow-up (2026-10-12): production build/TypeScript and all 223 visual cases passed without baseline changes. Mobile 360/390/430 checks verify no Outros tab, Brahma 600 ml in Cervejas even without category, all-active-product counts and category/name ordering in Todos, disabled unavailable items, excluded inactive products and collapse/reopen without losing drafts. Exact current/legacy Brahma names were checked separately. No API, database, price or order mutation.
- [x] Agora não monta formulários de clientes ou ícones; detalhes sob Ver mais.
- [x] Cinco seções selecionáveis por link/hash, voltar/avançar; ações e retornos.
- [x] DEV indisponível sem flag; não autorizado recebe 403; Venue isolado.
- [x] Criação com PIN hash, replay idêntico único, payload diferente 409.
- [x] Remoção revoga acesso sem apagar histórico; própria conta/último OWNER protegidos.
- [x] UI não confirma mutation ambígua; mantém intenção/chave e reconsulta conflito.
- [x] Backup local legível e auditoria; zero Tabs abertas e filas antigas após limpeza.
- [x] Nenhum Payment novo/alterado pela limpeza; Products não alteram snapshots/preços.
- [x] Build/types, npm run test:visual e integração PostgreSQL aprovados.


Evidência local em 11/10/2026: API273fc83/Web2d932b3; build/TypeScript,
36 testes API/PostgreSQL, 209 testes visuais e 15 jornadas Web/API/PostgreSQL.
Web padrão sem flag: status false, página404, gateway403. Releitura da demo após
reinício confirmou zero comandas/filas abertas e igualdade dos 16 Payments.
Relatórios/logs em visual-artifacts/demo-functional/runtime/pilot-*.log e
apps/web/playwright-report/. Nenhuma baseline/tolerância alterada.

### Attendance refinement

Partial-removal validation (2026-10-12): closing is the final Attendance action after the bill; multi-unit removal opens a dialog starting at one, with bounded minus/plus controls. Remaining units and net subtotal refresh canonically. Production build/TypeScript, 108 PostgreSQL financial/concurrency tests, two real integration journeys and 226 visual cases passed without changing baselines. Responsive quantity-dialog evidence: visual-artifacts/pilot-cohesion/partial-removal-390.png. Existing payment records were preserved during local schema migration.
- Opening a Tab presents the ordering workflow before its bill. Net Subtotal is visible; original subtotal and financial details require Mais detalhes and retain exact cent values.
- Category filters and global accent-insensitive search preserve drafts and mandatory choices; unavailable items cannot be added.
- Unrecognized products remain discoverable; inactive items are absent from Attendance.
- POS retains its full financial summary. Responsive 360/390/430 checks and visual suite pass without baseline relaxation.

Attendance refinement evidence: production build/TypeScript passed; 213 visual cases passed without baseline relaxation, including 360/390/430 category/search/cart/bill tests; real PostgreSQL Attendance order-production-delivery-table lifecycle passed. Search normalization was additionally checked for accents and numeric units. No database/product/payment mutation was introduced.

### Attendance follow-up
Remove an unpaid NEW item through Spec 017; canonical charge reversal updates subtotal without Payment creation. Repeating after lost response uses identical key/body; 202 never hides or marks item cancelled. Prepared items require the authorized workflow. Category collapse/reopen preserves cart; centered title has no cart icon; original subtotal appears only in discrete button-like Mais detalhes.

Follow-up evidence: production build/TypeScript passed. Full visual run passed 213 cases; three removal cases initially failed because their list fixture contradicted the canonical detail fixture. After correcting the fixture, all three passed in a focused rerun against the same final build (216 cases covered). Two real Web/API/PostgreSQL journeys passed, including cancellation, preserved item history, zero payable/exposure and no Payment creation. No visual baseline/tolerance changes. Live demo item remained untouched.

Confirmed-item removal uses a native modal dialog with a labelled title, trapped focus and focus restoration. Escape closes only before submission or after a resolved rejection; pending, ambiguous or applied-but-unrefreshed corrections cannot be dismissed. Existing cancellation rules remain unchanged. Dialog uses existing surface, border, spacing and radius tokens; backdrop uses the background token.

Dialog validation: production build/TypeScript and three focused visual/a11y correction scenarios passed; no financial API changes or baseline changes.

Attendance action dialog evidence (2026-10-12): final production build/TypeScript passed; 220 visual cases passed against the stable final build, including 360/390/430 table dialogs, cancellation without mutation, explicit release/close confirmation, rejection alerts, focus restoration and unchanged adjacent POS. Two real Web/API/PostgreSQL journeys passed, including association and confirmed release. No baseline/tolerance changes or live demo mutations. Logs: action-dialog-visual-final.log and action-dialog-integration.log under visual-artifacts/demo-functional/runtime.

Cancelled-item visibility: build/TypeScript and six focused visual cases passed. Real PostgreSQL cancellation journey passed, verifying cancelled history remains persisted with canonical zero payable and no Payment creation. Attendance excludes cancelled lines; POS/history unchanged.

Attendance draft evidence (2026-10-12): production build/TypeScript passed; 223 visual cases passed, including 360/390/430 exact-selection aggregation, cent-based line total, draft-before-catalog ordering, list/header collapse preservation, minus-at-one removal, disabled empty confirmation and ambiguous-order collapse/quantity locks. Two real PostgreSQL journeys passed with quantity two, canonical exposure and preserved cancellation history. No baseline relaxation or live demo mutation. Evidence: attendance-draft-visual-final.log, attendance-draft-integration.log under visual-artifacts/demo-functional/runtime and attendance-draft-390.png under visual-artifacts/pilot-cohesion.

Summary placement follow-up (2026-10-12): compact bill precedes confirmed orders at 360/390/430; closing remains the final action. Production build/TypeScript and all 226 visual tests passed without baseline changes. Local Attendance HTTP 200 confirmed.

Final Attendance layout refinement (2026-10-12): Pedido atual uses the shared full-width OperationalHeading with cart icon; compact summary follows catalog immediately before Fechar comanda. Build/TypeScript and all 226 visual cases passed without baseline changes. Local screen and gateway connectivity verified.

Wrong-entry bill disclosure (2026-10-12): compact Correções excludes applied pre-fulfillment mistaken removals; their signed amount is separately disclosed as Itens retirados por engano. Zero remaining correction row is omitted, mixed corrections retain their own amount, and full POS aggregate remains unchanged. Production build/TypeScript, 46 correction/pricing API tests plus focused mixed-reason regression, and all 229 visual cases passed without baseline changes. Demo frontend and API readiness verified.

Final wrong-entry disclosure requirement (2026-10-12), superseding the separate-row presentation: mistaken removals appear in neither Correções nor a dedicated bill-detail row. Canonical subtotal remains unchanged. Production build/TypeScript and 12 focused visual cases passed, including omitted rows and mixed correction values at 360/390/430. Demo screen HTTP 200 and API readiness confirmed.

Attendance history refinement (2026-10-12): right-aligned Histórico icon/text trigger at the end of Abrir comanda opens a read-only native dialog; closed Tabs never join the open list and inspection does not change the selected Tab. Build/TypeScript passed. History, focus restoration and adjacent ordering/removal/dialog checks passed at 360/390/430. Local screen and API readiness verified.

History header placement (2026-10-12): accessible icon-only Histórico control is inside the heading surface at the right edge of Abrir comanda, with minimum 44px touch area. Build/TypeScript and seven focused history/dialog visual cases passed at 360/390/430; demo HTTP 200 verified.

History return action (2026-10-12): Voltar uses full-width secondary border/accent surface and separated spacing. Build/TypeScript and seven focused visual history/dialog checks passed at 360/390/430 with focus restoration preserved. Demo HTTP 200 verified.

Integrated release validation (2026-10-12): integrated explicit kitchen/bar preparation start from main; build/TypeScript, 61 ordering/correction/pricing API tests and all 232 visual cases passed without baseline changes. Subsequent Spec 026 documentation update also integrated; no executable code changed after validation. Demo frontend HTTP 200 and API readiness confirmed.

## T04 — aceite do recorte local

- [x] A→B→A e nova Tab preservam linhas/configurações isoladas; confirmar limpa
  só a Tab enviada, sem transportar linhas para outra conta.
- [x] Reseleção revela o workspace; recolher explícito preserva rascunho e foco.
- [x] Descarte confirmado afeta só a Tab ativa; cancelar preserva conteúdo/foco.
- [x] Leitura falha mantém destino; durante switch/envio/ambiguidade não editar,
  trocar, recolher ou descartar; catálogo atual continua revalidando as linhas.
- [x] Jornada Web/API/PostgreSQL e360/390/430, visual completo/build/tipos/diff.

Memória apenas enquanto workspace montado. Reload e recuperação durável T05 abertas.
