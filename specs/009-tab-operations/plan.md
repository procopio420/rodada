# Plan — Spec 009

## Recommended sequence

1. **Domain/migrations**
   - Tab versioning if needed;
   - TabTransfer + TabTransferLine;
   - balanced ledger transfer effect;
   - merge/reopen provenance.

2. **Transferability service**
   - exact open amount;
   - blockers for confirmed/refunded/in-flight payments;
   - interaction with Adjustments.

3. **Commands**
   - location move;
   - split/move responsibility;
   - merge duplicate Tabs;
   - cancel empty;
   - reopen.

4. **API contracts**
   - preview before commit;
   - normalized conflict/non-transferable errors;
   - idempotency keys.

5. **Atendimento UX**
   - location move;
   - item-based split;
   - merge survivor selection;
   - paid-state blockers;
   - reopen for authorized roles.

6. **Realtime/Management**
   - invalidate affected Tabs;
   - timeline facts;
   - post-close exception.

## Rollout

Ship location move first because it has no ledger effect. Ship financial transfer only after ledger transfer invariants and concurrent tests pass.

Do not silently migrate historical Orders/Payments.

Spec 026 T06d: first reproduce stale destination generation and lost audit reason
through the existing HTTP command; validate generation under the existing
Table/Occupancy locks and pass reason to audit. Exercise paid/unpaid moves,
exact replay, permission denial and move/release races in disposable PostgreSQL.
Keep the Attendance Web movement UI outside this backend correction.

Web continuation: narrow Attendance gateway, always-mounted ActionDialog for
reload recovery, source contextual read before confirmation and immutable
session-scoped intent before POST. Verify auth, operation and Tab/table readback.
Test mobile, ambiguity, storage/session and real PostgreSQL journeys; preserve
existing drafts, independent occupancy lifecycle and financial history.

## Testing strategy

- property/invariant tests for balanced transfer;
- concurrent double-transfer;
- split/merge with and without payments;
- idempotent retry;
- identifier/session behavior;
- daily-close reopen behavior;
- E2E Atendimento split of unpaid Tab.

## Dependencies first

Specs 001, 004, 006 and 008 authorization. Spec 011 must define how adjusted lines report transferability before broad rollout of discounted-item moves.

## Execution
Dedicated `tab_operations` module, transfer lines as balanced responsibility facts, narrow
ledger totals and correction guard integrations, authenticated preview/commit API and native
Attendance operation sheet. Preserve existing transport; AuditEvent is the durable event contract.

## Continuation after PR #47

1. Fast-forward the feature branch to current main; preserve provider ownership.
2. Correct terminal-payment blockers and batch responsibility queries; verify on PostgreSQL.
3. Read operation state atomically and expose audit actor/session/device provenance.
4. Integrate balanced transfer effects into management open exposure without treating them as sales.
5. Preserve Android server rejection through a failed refresh and offer state-valid operations only.
6. Validate persisted HTTP workflows, full-shift smoke, row-lock races and Android unit/build/lint gates.
7. Record evidence and remaining adjacent-owner integrations; open a follow-up PR without merging.

### T07d — valor parcial Android
Solicitar teclado decimal, mostrar erro para texto inválido/zero e bloquear preview/commit de novo comando; retirar fallback de parse para zero. Testar callback do preview com centavos exatos e ausência de commit, mantendo recuperação pendente e validação server-side.
