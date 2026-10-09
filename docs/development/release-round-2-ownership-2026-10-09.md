# Round 2 ownership and frozen integration contracts

Baseline main: 9b8e5e538753a9a753985ca0fb297e3cffa77320. PR62 and PR61
merged locally with original ancestry; pricing fix deduplicated by Git. No main merge.

Orchestrator exclusively owns financial invariants, provider services, access
API/authentication, cross-domain schema/migrations, release matrices and integration.
No change to ledger or canonical command shape without orchestrator review. Native
originating-session header is optional for other clients, mandatory in native
withAuthorizedAccess; mismatches are rejected before mutation. Unknown outcomes stay
unresolved. Keep reference fixtures/hashes/thresholds immutable.

- Hospitality: modules/hospitality and dispatch service/view additions, hospitality
  focused tests, specs003/004/016. No shared ordering models/views or migrations;
  propose required schema changes to orchestrator.
- Management: venue configuration and operational alert service/UI files, focused
  tests, specs007/013/018. No financial/access files or hospitality screens. Propose
  schema changes; orchestrator generates migrations.
- Reliability: native PendingMutationIntentStore, OperationsViewModel and
  CashShiftViewModel, focused new native tests; Web recovery files only after
  coordinating exact paths. Auth and HTTP provenance contract is frozen; do not
  change it independently. Specs014 and recovery criteria. No core API edits.
- Visual QA: Web production components/styles and focused visual tests, spec023;
  native screen presentation only after coordinating with reliability. No tokens,
  snapshots/reference exports, baseline or threshold changes. Own full kitchen
  visual comparison and realistic state verification.

Each agent works in its own worktree and supplies isolated commits plus evidence.
Only orchestrator integrates; agents do not merge or deploy. Criterion status changes
require exact behavior/evidence and are proposed to orchestrator, never edited in
canonical matrices independently. Shared gates are still executing; no completed
Phase2/pilot assertion is made by assigning bounded closure work.
