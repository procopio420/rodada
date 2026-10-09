# Acceptance — Spec 011

## Item percentage discount

**Given** an eligible item net basis of 2000 cents  
**When** an authorized cashier applies 10.00% item discount  
**Then** a -200 cent Adjustment is persisted, the original Charge remains unchanged and payable decreases exactly 200 cents.

## Fixed discount bound

**Given** an eligible Tab basis of 3000 cents  
**When** a 3500-cent fixed discount is requested  
**Then** the server rejects it and no Adjustment is written.

## Courtesy

**Given** a manager grants full courtesy to a 1200-cent item with required reason  
**When** committed  
**Then** the item Charge remains, a -1200-cent COURTESY effect is recorded with actor/reason, and reporting classifies it as courtesy rather than zero-price sale.

## Service charge

**Given** eligible net consumption of 10000 cents and venue default 10.00%  
**When** service charge is assessed  
**Then** SERVICE_CHARGE effect is exactly +1000 cents and no Product/OrderItem is created.

## Service charge after discounts

**Given** gross consumption 10000 cents and 2000 cents of active eligible discounts  
**When** 10.00% service charge is calculated  
**Then** basis is 8000 cents and service charge is 800 cents.

## Reduce service charge

**Given** an active 1000-cent service charge  
**When** authorized staff reduces it to 500 cents  
**Then** original assessment remains queryable and a -500-cent SERVICE_CHARGE_REDUCTION effect records the change.

## Rounding/allocation

**Given** a Tab-level percentage discount whose proportional shares produce fractional cents  
**When** applied  
**Then** largest-remainder allocation is deterministic and allocated cents sum exactly to total discount.

## Permission threshold

**Given** STAFF lacks a requested discount threshold  
**When** they submit it directly  
**Then** server returns APPROVAL_REQUIRED or CAPABILITY_REQUIRED according to policy and no financial effect is committed.

## Manager approval

**Given** an approvable request above cashier threshold  
**When** a manager reauthenticates and approves  
**Then** one Adjustment is created with requester and approver; retrying the same idempotency key creates no duplicate.

## Partial payment safe edit

**Given** payable is 10000 cents and 4000 cents is already confirmed received  
**When** manager applies an Adjustment that leaves payable 8000 cents  
**Then** it may commit if policy permits and remaining balance becomes 4000 cents.

## Partial payment unsafe edit

**Given** 9000 cents already received  
**When** a proposed discount would reduce payable to 8000 cents  
**Then** server rejects with SETTLEMENT_CORRECTION_REQUIRED unless a valid refund/correction orchestration handles the 1000-cent over-receipt.

## Payment stale amount

**Given** a payment screen was opened before a pricing Adjustment  
**When** it attempts to create an integrated payment with stale balance/version  
**Then** backend rejects/revalidates instead of charging the stale amount.

## Refund helper

**Given** an item had allocated discounts  
**When** manager prepares item-based refund  
**Then** refund preview uses persisted net allocations and never refunds the undiscounted list price by mistake.

## Concurrency

**Given** two managers calculate discounts from the same pricing version  
**When** both commit concurrently  
**Then** one succeeds and the stale request must re-preview against the new basis.

## Audit / closing

**Given** discounts, courtesy and service charge occurred during a business date  
**When** daily close is generated  
**Then** gross consumption, each adjustment category, service charge and refunds are separately reconstructible without double counting.

## Executable financial evidence

The foundation audit is in `audit.md`. Detailed reproduction commands and measured
gates are in `evidence.md`.

| Acceptance / edge case | Executable evidence |
| --- | --- |
| Item percentage; original charge unchanged | `test_preview_replay_allocation_and_original_history` |
| Half-up rounding and largest remainder, 600 calculator combinations | `CalculatorTests.test_rounding_and_allocation` |
| Allocation across multiple order items | `test_multiple_items_rounding_is_persisted` |
| Discount greater than remaining / courtesy on paid consumption | `test_partial_payment_and_paid_courtesy_bounds` |
| Full courtesy and required reason | `test_full_courtesy_reason` |
| Manager approval, PIN, both actors and exact replay | `test_approval_reauth_and_exact_replay` |
| Stale approval has no effect | `test_stale_approval_never_applies` |
| Configurable 7.5%/10%, max/disabled policy and House limits | `test_policy_and_staff_threshold`, `test_service_disabled_maximum_and_house_exposure` |
| Service after discounts, refresh and removal | `test_service_refresh_and_explicit_removal` |
| Reversal preserves service and authority | `test_service_reduction_reversal_and_reason_authority` |
| Historical policy treatment on removal | `test_service_removal_preserves_original_treatment_after_policy_change` |
| Post-payment policy and mandatory reason | `test_post_payment_policy_and_required_reason` |
| Payment stale version / in-flight money | `test_stale_payment_version_is_rejected`, `test_inflight_version_and_limit` |
| Refund after discount and item net-value helper | `test_refund_after_discount_preserves_pricing`, `test_reverse_and_net_refund_preview` |
| Unpaid adjusted transfers; paid transfer blocked | `test_unpaid_split_conserves_components`, Tab Operations regression suite |
| Discounted cancellation uses remaining net | `test_discounted_unpaid_cancellation_uses_net` |
| Complete customized remake/payment/close/reconciliation | `test_customized_bill_correction_and_management` |
| Two staff / same key / payment versus discount / service races | `PricingConcurrencyTests` (PostgreSQL) |
| Database forbids UPDATE/DELETE and inexact allocations | `test_postgres_append_only_and_allocation_sum` |
| Legacy upgrade preserves money, kind and reason | `PricingUpgradeTests` |
| Real cashier UI through PostgreSQL to reports | `tests/integration/zz-pricing.spec.ts` |
| Native exact cents, bill fields and persisted intent/version | `PricingContractTest` |

The complete scenario proves: original consumption 4800, remake consumption 2800,
gross 7600; Tab discount 800; courtesy 3200 (replacement 2800 + correction 400);
net consumption 3600; final service 360; payable and net received both 3960;
closed Tab exposure zero. The original Charges and Payments retain their amounts.

Explicit P0 boundaries: confirmed payments/refunds block financial transfers;
reversing transferred allocations requires an allocation-aware correction rather
than guessing the current owner. Refund assistance never claims payment-to-item
settlement allocation. Service is operationally classified as revenue or
pass-through, without inventing a fiscal or general-ledger treatment.
