# Acceptance — Spec 010

## Simple product backward compatibility

**Given** a Product with no variants or modifier groups  
**When** staff adds it  
**Then** it can still quick-add and confirm exactly as before.

## Required variant

**Given** a Product with P/M/G variants and no default  
**When** staff attempts to confirm without a variant  
**Then** server rejects with VARIANT_REQUIRED and creates no OrderItem/Charge.

## Required modifier

**Given** a SINGLE group “Ponto” with min=1 max=1  
**When** no option is selected  
**Then** confirmation is rejected.

## Multi-select bounds

**Given** “Adicionais” min=0 max=3  
**When** four options are submitted by a modified client  
**Then** server rejects regardless of UI state.

## Price calculation

**Given** base price 3000 cents, variant +500 and modifiers +300 +0  
**When** the item is confirmed  
**Then** unit price snapshot is exactly 3800 cents and no floating-point calculation is used.

## Zero-price removal

**Given** “SEM cebola” is an AVAILABLE REMOVE option priced 0  
**When** selected  
**Then** it appears in the confirmed snapshot and production display without changing price.

## Stale availability

**Given** bacon extra was selectable when cart opened  
**When** it becomes UNAVAILABLE before confirmation  
**Then** server rejects the bacon selection, identifies the affected option and does not silently remove/substitute it.

## Parent availability

**Given** ProductAvailability is UNAVAILABLE  
**When** a client submits otherwise valid variant/modifiers  
**Then** the Product cannot be confirmed.

## Snapshot immutability

**Given** a confirmed OrderItem with “Grande + bacon”  
**When** the Product, variant name or modifier price later changes  
**Then** historical OrderItem still displays the original names and cents.

## Post-confirm change

**Given** a confirmed item  
**When** customer asks to remove bacon  
**Then** the existing snapshot is not mutated; correction follows Spec 017.

## Production routing

**Given** a Product routed to KITCHEN with modifiers  
**When** confirmed  
**Then** it remains one KITCHEN OrderItem with structured preparation text; no hidden BAR work is created by a modifier.

## Permission denial

**Given** station staff without catalog-config capability  
**When** they attempt to edit modifier group structure  
**Then** backend denies it.

## Authorized availability

**Given** kitchen staff authorized for the Product station  
**When** they mark a modifier option unavailable  
**Then** actor/time/old/new state are audited and staff/guest receive realtime invalidation.

## Concurrency

**Given** availability changes concurrently with order confirmation  
**When** database validation sees the option unavailable before commit  
**Then** no invalid OrderItem/Charge is committed.

## Idempotency

**Given** a customized order confirmation times out client-side  
**When** the exact idempotency key is retried  
**Then** only one OrderItem and one financial effect exist.

## Guest UX

**Given** required choices exist  
**When** guest taps Add  
**Then** a compact choice flow opens; unavailable choices are labeled, price impact is visible, and notes remain secondary.
