# Financial foundation audit — 2026-10-09

Repository audit read AGENTS, product/architecture/design/domain contracts, Specs
001, 002, 006, 009, 010, 011, 012 and 017, and Access/ledger/Ordering/Management code.
There is no `.codegraph` directory in this checkout.

| Foundation | Existing behavior | Gap addressed by 011 |
| --- | --- | --- |
| Charges / Orders | Captured item prices and one charge per item; order replay | Commercial adjustments never alter those snapshots |
| Adjustment | Cancellation / replacement courtesy only | Discount, courtesy, service, reduction, reversal, allocation, policy snapshots |
| Settlement | Confirmed money and confirmed refunds derive exposure; partial payments | Post-payment policy and net-receipt guard; stale service and payment versions |
| Access | Venue memberships, capability overrides, expiring privileged PIN reauth | Reauthorized pricing services; exact pending approvals and both actors |
| House Account | Tab lock, limit snapshots, derived exposure, attention | Service/reversal limit enforcement and adjustment invalidation |
| Tab Operations | Balanced net financial transfers, versioned replay, paid/in-flight blockers | Persisted commercial/treatment components travel with each unpaid transfer |
| Management | Business-date reports, gross/net ledger aggregates, receipts by method | Discounts/courtesy/service/removals and revenue/pass-through independently reconstructed |
| Cash | Physical cash movements come from actual payments/refunds | Commercial amounts feed the same payable; service never becomes a product or cash movement |
| Customization | On retained Spec 010 branch, immutable variant/modifier snapshots | Real customized remake/courtesy/payment integration |
| Corrections | Append compensation and explicit refund-required exceptions | Reverse remaining net consumption; refund bound uses discounted item value |

Current origin/main lacks the retained Spec 010 branch's commits. The pricing PR
uses `feat/product-modifiers-variants` as its base to isolate pricing changes.
No provider-specific SDK or printing code is changed.

Existing post-production corrections can intentionally record an over-receipt as
an explicit REFUND_REQUIRED case. Pricing does not remove that orchestration;
ordinary discount/courtesy commands reject over-receipt before writing. Payable
consumption never becomes negative. Payment-to-item settlement allocation remains
outside Spec 009 P0; refund helpers state that payment selection is required.
