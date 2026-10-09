# Release ownership and contract freeze — 2026-10-09

Baseline origin/main 7227f7d. All work occurs in fresh isolated worktrees. Existing dirty worktrees are preserved.

- Integrator owns API route registry/contracts, access, ordering shared contracts, ledger, house_account, payment_provider, catalog, printing, all shared financial migrations and final sequencing.
- Hospitality owns hospitality, guest_access, dispatch and guest UI, Specs 003/004/016. Request integrator approval before editing shared ordering/ledger or route registry.
- Management owns venue, management projection/configuration interface and manager UI, Specs 007/013/018. Alert storage belongs here; coordinate dependencies through current domain queries.
- Native POS owns Android, cash, corrections, tab_operations, Specs 009/012/017. Financial migrations and ledger changes require integrator sequencing.
- QA owns QA scripts, CI, fixtures/reports and isolated design files, Specs 014/022/023. Initially inspect other owners' files without edits and send findings.

Freeze existing endpoint shapes and capability names; additive fields only after review. No renamed endpoints or changed cents/source/error semantics. PostgreSQL is authority; HTTP commits commands; SSE invalidates projections. Venue scoping and current authorization are checked on every command. Identity optional, Tab mandatory. Guest generation revoked on release; occupancy is independent of financial closure. Monetary cents are integers; financial history append-only; payment confirmation comes from canonical server evidence. Inference always exposes source/confidence/provenance. Cash corrections preserve original closure snapshots. No simulated provider result can prove settlement. Fiscal issuance remains outside accepted scope.

Migration ownership: owners may propose domain-local migrations; integrator reviews dependencies and applies/cherry-picks sequentially. No agent edits shared financial migrations. Every submitted commit must list exact tests and criterion-level evidence, outstanding blockers and any cross-owner change request. Red commits are not integrated.

Execution capacity: tool permits three child agents concurrently plus integrator. Exactly four specialized agents will be created; Native POS starts when the initial QA audit releases a slot. QA can resume after another owner finishes.
