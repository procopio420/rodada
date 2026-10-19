# E06: Focused Spec027 contracts in UX2

The optional Web visual workflow previously ran legacy navigation selectors (`Contas`, global table picker, separate start CTA) against UX2. Tests now traverse Mesas → contextual new Tab and the native UX2 catalog/send controls. Dirty tables do not offer creation. Required names, named standalone fallback and occupancy generation remain asserted.

Existing Spec027 start envelopes remain recoverable although UX2 opens the first Tab directly: the test seeds a legacy envelope and proves the original UUID/payload survives lost ACK and reload. Contextual Tab open, order confirmation and location moves retain their original payload equality assertions. The order test verifies draft survival and navigation lock while the outcome is unknown. HTTP fixtures are browser-only; this suite is not PostgreSQL or ledger acceptance evidence.

The operator options button keeps its approved painted dimensions and expands its invisible pointer target to at least 44×44. The existing geometry/hit ownership and accessibility helper remains unchanged.

Build, typecheck and focused-file ESLint passed. Focused run evidence is in focused.log. Independent review and CI are recorded in the PR; full visual-suite and real API regression acceptance remain separate gates. Depends on PR #235. No merge or deploy.
