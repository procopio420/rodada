# Acceptance — Spec 017

## Draft edit

**Given** an item is still unconfirmed client draft  
**When** staff changes Product/modifiers  
**Then** draft changes directly and no OrderCorrection/audit history is required.

## Wrong accepted item

**Given** a confirmed ACCEPTED unpaid item and authorized STAFF  
**When** they choose “item lançado errado”  
**Then** original item becomes CANCELLED through legal transition, original snapshot/Charge remain, reversal effect removes open responsibility, and correction is audited.

## Preparing cancellation authorization

**Given** item is PREPARING  
**When** ordinary STAFF attempts cancellation without required capability  
**Then** backend denies/requests manager approval and production state is unchanged.

## Ready rejection

**Given** item is READY and customer rejects it  
**When** manager applies correction  
**Then** original READY history and delivery task history remain, task resolves by exception, optional waste can be recorded and any replacement is a new OrderItem.

## Modifier mistake remake

**Given** original confirmed item has wrong modifier snapshot  
**When** a remake with corrected modifiers is created  
**Then** original snapshot is untouched and new OrderItem has its own corrected immutable snapshot and fulfillment lifecycle.

## Station mistake comped remake

**Given** kitchen mistake requires same item remade without additional customer charge  
**When** manager approves comped remake  
**Then** replacement/remake has normal price snapshot/Charge plus explicit matching courtesy (or canonical equivalent defined by Billing), producing intended zero additional responsibility without fake zero-price Product.

## Customer changes mind after delivered

**Given** item is DELIVERED  
**When** customer complains/changes mind  
**Then** system does not roll state backward; correction records complaint and offers explicit replacement/courtesy/refund options according to policy.

## Paid refund

**Given** item responsibility was already paid and money should be returned  
**When** correction is approved  
**Then** original Payment remains, Spec 006 Refund is created idempotently, and correction links the refund.

## Transferred responsibility

**Given** original item belongs historically to Tab A but unpaid financial responsibility was transferred to Tab B  
**When** item is cancelled  
**Then** operational correction remains linked to original item/A history while financial reversal applies to current responsibility on B.

## Double correction concurrency

**Given** two devices attempt terminal cancellation of the same item concurrently  
**When** both commit  
**Then** only one terminal correction/reversal is applied; the other gets current correction state.

## Retry idempotency

**Given** a remake request committed but client timed out  
**When** retried with same idempotency key  
**Then** no duplicate remake OrderItem, Charge or courtesy is created.

## Waste marker

**Given** a prepared item is discarded  
**When** authorized staff records PREPARED_NOT_SERVED  
**Then** WasteMarker is stored for operational analytics but no inventory deduction/accounting entry is invented.

## Realtime failure

**Given** WebSocket is down but API healthy  
**When** cancellation succeeds  
**Then** canonical state changes via API and station can recover by polling/revalidation.

## Offline

**Given** API is offline  
**When** staff tries to cancel/remake  
**Then** UI may save a pending note but does not mark canonical item cancelled or stop production as if server confirmed it.

## UX-34 — revisão sem devolução (recorte local)

- [x] Parcial 1000 em consumo 3800, item NEW de 800: gerência aplica reversão,
  payable 3000/exposição 2000, sem Refund/CashMovement ou alteração de Payment.
- [x] Capability, gerente ativo, isolamento de Venue e reauth recente preservados.
- [x] Replay/concorrência têm efeito único; saldo/estágio alterado rejeita com rollback.
- [x] Desconto/serviço existentes são lidos canonicamente; zero legado é suportado.
- [x] UI oferece ação executável sem exigir pagamento elegível e conserva o
  mesmo comando em resposta ambígua; jornada real PostgreSQL passou.

Ver Spec 026/revalidation.md para checks e limites. Não conclui gates amplos de
correção paga parcial, produção avançada, transferências, provider ou piloto.

## Audit/analytics (critério original)

**Given** corrections occurred  
**When** Gerência reviews timeline  
**Then** original item, stage, reason, actor/approver, replacement/waste and financial disposition are traceable without a staff blame leaderboard.

## T03b — critérios do recorte manual

Evidências em Spec026/revalidation.md; gates externos permanecem abertos.

- [x] Mesmo Refund após duplo toque, resposta perdida, reload e readback falho.
- [x] Payload congelado; PIN recente, sessão divergente/revogada e storage falho
  não descartam nem adotam intenção ambígua. Rejeição inicial segura permite edição.
- [x] Replay divergente rejeitado; saldo/refundable, Payment/snapshots, ledger e
  auditoria preservados; concorrência produz um único efeito em PostgreSQL.
- [x] Jornada real Web/API e mobile360/390/430; visual completo, build/tipos e lint
  registrados sem declarar provider, piloto, aparelho ou deploy homologados.

T11d/026 local: resolução de alvo por capability/Venue sem mutation e sem alterar
reauth das ações financeiras. Item/payment/correction e Tab canônicos validáveis
inclusive após encerramento/aplicação; envelope preservado e outra sessão bloqueada.
Critérios/testes e limites em specs/026-operational-ux-friction/revalidation.md.
Reconciliação gerencial, aparelho físico e piloto permanecem abertos.

T12b.3/026: item/correção históricos conferíveis sem mutation financeira; pagamento
explícito validado junto do item/Tab e sessão. IDs inválidos, sem acesso e ausentes
não exibem alvo alternativo; intenções existentes ficam intactas.
