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
