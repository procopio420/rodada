# Reconciliation of the open Web queue against main20828711

Preserve canonical Dispatch ownership from #252 and the current automatic settlement policy. Compose #261, #260 and #255 with the migrated historical confirmation assertions from #219 and evidence from #249. Historical evidence is scoped to its recorded SHA, never a pass for this candidate.

The release dialog captures a required occupancy ID/generation pair when opened. Missing occupancy cannot open a release confirmation; replacement invalidates confirmation. Submit the captured pair, never refresh it at confirmation. API integration is gated on the main-reconciled #253 contract and real PostgreSQL checks.

Validation: typecheck/build, visual history/delivery/release/receipt regressions at 360/390/430 plus desktop where supported, auth/tenant and focused real PostgreSQL order/settlement/menu/release integration. Independent R3 review and current CI remain separate gates. No operational or pilot acceptance is implied.
