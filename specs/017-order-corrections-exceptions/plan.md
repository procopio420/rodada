# Plan — Spec 017

Partial cancellation: add nullable positive cancelled-unit facts to OrderCorrection with backwards-compatible fingerprints, and a distinct negative partial-cancellation ledger kind so existing whole-line uniqueness stays intact. Derive remaining quantity from applied facts; prefetch corrections on operational projections. Prorate the current canonical net using integers and consume all rounding cents on the final cancellation. Keep Tab/item locking, stage/transfer/paid guards and immutable snapshots. Verify unit/rounding/replay and real PostgreSQL races, then the actual Web/API journey and mobile dialogs. Apply migrations to the preserved local demo only using authorized local authentication and restart matching API/frontend builds.

## Recommended sequence

1. **Domain/migrations**
   - OrderCorrection;
   - WasteMarker;
   - replacement/remake linkage;
   - correction version/idempotency.

2. **Correction policy/preview**
   - stage-aware options;
   - current financial owner via Spec 009;
   - exact financial disposition.

3. **Simple cancellation**
   - NEW/ACCEPTED;
   - open-responsibility reversal;
   - fulfillment/dispatch cancellation.

4. **Preparing/Ready exception**
   - manager approval;
   - waste;
   - station realtime.

5. **Remake/replacement**
   - new OrderItem;
   - copied/edited customization;
   - courtesy replacement integration.

6. **Paid corrections**
   - refund-required orchestration;
   - provider idempotency.

7. **Surfaces/analytics**
   - Atendimento “Corrigir item”;
   - station badges;
   - management timeline/reasons.

## Rollout

Start with unpaid NEW/ACCEPTED cancellation. Do not expose delivered/paid correction until refund/courtesy orchestration passes end-to-end tests.

## Testing strategy

- snapshot immutability;
- state-specific permission matrix;
- concurrent double correction;
- transfer lineage;
- replacement charge+courtesy net;
- dispatch history preservation;
- provider refund idempotency;
- offline no-fake-cancel.

## Dependencies first

Specs 009–011 and payment Refund semantics must be stable before advanced correction.

## Slice UX-34 (Spec 026 T02)

Reproduzir 3800/1000/800 em PostgreSQL de teste; distinguir revisão sem devolução
de estorno positivo. Implementar aprovação transacional sem refund com locks no
aggregate, autorização recente, replay pelo correction ID e suporte a pendência
legada de zero. Expor na revisão Web e testar rejeição por saldo/estágio alterado,
descontos/serviço, isolamento e resposta perdida. Gates financeiros e visuais
sem alterar baseline. Fora de escopo: remoção parcial paga e produção avançada.

## T03b — execução do estorno manual recuperável

1. Envelope antes do POST; guard síncrono, campos congelados e retomada explícita.
2. Validar sessão e fingerprint de replay CASH/correção; preservar locks/auditoria.
3. Testar perda após commit/readback, reload, PIN/sessão/storage, divergência e
   concorrência em PostgreSQL; jornadas Web/API360/390/430, visual completo/build.

T11d/026: resolver alvo por ID/capability/Venue e validar vínculo payment/correction, sem mutation. Conferência Android separada mantém o envelope e seleção anterior; evidências em specs/026-operational-ux-friction/revalidation.md.
