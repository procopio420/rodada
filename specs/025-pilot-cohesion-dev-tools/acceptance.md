# Aceite
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
