# Plano
1. Inventariar UI, API e dados locais, preservar alterações existentes.
2. Fazer disclosures/seções reais por hash usando componentes/tokens atuais.
3. Reutilizar membership e revogação existentes, adicionar criação transacional
   idempotente e área DEV desabilitada por padrão; proteger último OWNER.
4. Validar permissões, secrets, retries, isolamento de Venue e navegação mobile.
5. Guardar backup local, corrigir Products e encerrar testes com trilha explícita.
6. Build/visuais/integração real, reabrir demo e documentar limites/backlog.

### Attendance refinement
Reuse category metadata and existing product/cart components. Isolate presentation taxonomy in a helper built from the existing photographed-menu CSV, with explicit category overrides. Add compact BillSummary mode only for Attendance, at the end of selected Tab. Verify category/search/cart invariants, disclosure and adjacent POS behavior.

Use the existing Spec 017 cancellation API through the restricted Attendance BFF; no financial domain change. Isolate cancellation UI and revalidation. Preserve existing confirm retry and disable navigation while cancellation is unresolved. Reuse quiet-button tokens for the details disclosure.

Confirmed-item removal uses a native modal dialog with a labelled title, trapped focus and focus restoration. Escape closes only before submission or after a resolved rejection; pending, ambiguous or applied-but-unrefreshed corrections cannot be dismissed. Existing cancellation rules remain unchanged. Dialog uses existing surface, border, spacing and radius tokens; backdrop uses the background token.

Reuse a native ActionDialog and existing correction styling. Wrap only existing Attendance controls, preserve payloads and validate mobile/a11y and existing journeys.

Use a focused AttendanceDraft component for quantity controls, existing customization snapshots and line prices. Keep selected Tab mounted while collapsed, expose aria-expanded, and reuse existing accent/spacing/touch tokens. Verify mobile layout, draft preservation, zero-quantity removal and ambiguous locks.

Reuse the presentation category mapping for an exact Brahma 600 ml/600ml override. Keep Outros only as an internal uncategorized fallback; replace its navigation with Todos. Reuse category order, sort names within groups, count all active products and keep the existing collapse/search interactions. Verify 360/390/430 grouping, unknown-product visibility, unavailable/inactive behavior and draft preservation; run production build and the complete visual suite.

Keep search mounted outside catalog disclosure. A nonempty normalized query reveals global results even when the last category remains collapsed; clearing restores that collapse. Align category highlights with the expanded state. Validate searching from collapse at 360/390/430 and preserve selected draft lines. Stop the local frontend before rebuilding, then restart it with the resulting build to avoid serving stale manifests.

Scope visual styling to Attendance: reuse shared heading/icon primitives, add only the trash symbol to the icon vocabulary, use compact Surface2 confirmed rows and accent-tinted closing action. Keep removal accessible names product-specific and 44px touch targets; maintain the original dialog/conditions and POS layout. Run existing cancellation lost-response/paid/advanced-stage checks at 360/390/430, inspect screenshots, then the full visual suite.

Move the existing compact bill section immediately before confirmed orders in Attendance only. Preserve draft placement, financial disclosure, POS ordering and final closing action. Verify summary-before-confirmed ordering at 360/390/430.

Latest Attendance layout: reuse OperationalHeading for the full-width draft heading; restore the compact summary immediately before closing. Keep ordering and financial behaviors unchanged.

Expose a read-only signed aggregate of applied pre-fulfillment wrong-entry cancellations. Compact bill separates this aggregate from displayed corrections, preserving canonical financial totals and original full POS summary.

Final disclosure requirement: omit wrong-entry removal rows entirely from the compact bill. Retain the signed read-only aggregate solely to exclude mistaken removals from displayed Correções; canonical totals and audit remain unchanged.

Reuse ActionDialog for read-only closed Tab history; move its discreet icon/text trigger to the end of Abrir comanda, right aligned. Keep open-list filtering independent and do not mutate active selection or drafts.

History trigger placement supersedes footer position: icon-only Histórico control lives at the right edge inside the Abrir comanda heading surface, using existing touch and accent tokens.

Reuse secondary button and existing accent surface styling for the history dialog return action; retain quiet defaults in other dialogs.
