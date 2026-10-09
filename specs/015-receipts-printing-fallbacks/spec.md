# Spec 015 — Receipts, Printing & Production Fallbacks

**Status:** Implemented P0; hardware verification pending

**Owner capability:** Document rendering + print delivery adapters

## Objective

Define customer receipts/checks and printer-backed operational fallbacks while keeping Orders, Payments and Fulfillment—not paper/printers—as the source of truth.

## Product problem

Bars still need paper for customer checks and sometimes for kitchen/bar fallback. Printers fail, disconnect and retry unpredictably; naive retry can duplicate production. Rodada must remain usable without a printer and must distinguish a reprint from a new production instruction.

## Scope

- customer bill/check;
- payment receipt;
- digital receipt;
- printing;
- production fallback tickets;
- network/Bluetooth adapters where supported;
- PrintJob lifecycle/idempotency/retry;
- printer health/errors;
- reprint audit;
- station-to-printer mapping;
- formatting and degraded behavior.

## Explicitly out of scope

- NFC-e/SAT/fiscal documents;
- tax invoice certification;
- printer as fulfillment truth;
- generic document-management system;
- silently printing unconfirmed Orders;
- provider-specific printer concepts in core domain.

## Domain concepts

### ReceiptDocument

Immutable rendered-data snapshot or reproducible document reference for one purpose.

Kinds:
- CUSTOMER_CHECK;
- PAYMENT_RECEIPT;
- DIGITAL_RECEIPT;
- PRODUCTION_TICKET.

Fields conceptually:
- id;
- venue_id;
- kind;
- source_type/source_id;
- source_version;
- rendered_at;
- business_date;
- content_version/template_version;
- canonical_data snapshot/hash;
- non_fiscal=true in P0;
- created_by/system provenance.

A document may be re-rendered into multiple output formats without changing source truth.

### PrinterEndpoint

Configured output device behind an adapter.

Types:
- NETWORK;
- BLUETOOTH_ANDROID;
- other future adapter types.

Fields:
- venue_id;
- label;
- adapter_type;
- connection reference/config;
- enabled;
- capabilities (width/cut/status support);
- last_health status.

Secrets/credentials stay in infrastructure boundary.

### StationPrinterBinding

Maps a FulfillmentStation to zero or more printer endpoints for production fallback.

May include priority and enabled purposes.

### PrintJob

One attemptable delivery of one ReceiptDocument to one PrinterEndpoint.

States:
- QUEUED;
- SENDING;
- PRINTED;
- FAILED_RETRYABLE;
- FAILED_FINAL;
- CANCELLED.

Fields:
- document_id;
- printer_endpoint_id;
- purpose;
- idempotency_key;
- attempt_count;
- created_at;
- last_attempt_at;
- provider/device result;
- reprint_of_job_id optional;
- requested_by;
- reason for reprint when required.

## Source-of-truth invariants

1. Printing never creates or confirms Order, OrderItem, Charge, Payment or fulfillment state.
2. A production ticket can only represent a canonical confirmed Order/OrderItem unless explicit offline-recovery mode is invoked.
3. Failure to print does not roll back a confirmed Order/Payment.
4. KDS/Bar screens remain canonical operational surfaces when available.
5. Printer retry with same PrintJob cannot generate a second logical production instruction.
6. Explicit reprint is a new PrintJob marked REPRINT and linked to original.
7. A PAYMENT_RECEIPT marked paid is generated only from canonical confirmed Payment state.
8. CONFIRMATION_PENDING is never printed/presented as definitively paid.
9. Customer check reflects a versioned snapshot/time and is not a fiscal document.
10. Production ticket content uses confirmed OrderItem snapshot, including variants/modifiers/notes from Spec 010.
11. Printer health is advisory; database state remains authoritative.
12. All money uses integer cents.

## Customer check / bill

Purpose: show current Tab consumption before/final payment.

Includes:
- Venue display name;
- Tab label/reference;
- timestamp/business date;
- item quantity/name/customization;
- gross/subtotal;
- discounts/courtesy;
- service charge;
- payments already confirmed;
- remaining balance;
- non-fiscal label when appropriate.

If the Tab changes after generation, an old check remains historical; a new print uses a new document/source version.

UI should clearly indicate “Conta gerada às HH:MM” on digital/print where staleness matters.

## Payment receipt

Generated after a confirmed Payment.

Includes:
- Venue;
- Tab;
- amount/method;
- confirmed time;
- payment reference safe for customer;
- resulting Tab balance where useful;
- refund/reversal status if later queried digitally.

For Tap/Pix/Card, provider-specific mandatory receipt text may be injected by adapter-safe receipt metadata without making provider fields part of Tab domain.

Never include PAN/CVV or sensitive tokens.

## Digital receipt

A mobile-friendly rendered receipt accessible:
- from authorized GuestSession;
- from staff share flow using an opaque, revocable/expiring receipt token when configured.

P0 does not require email/WhatsApp delivery integration.

Receipt token:
- random/opague;
- scoped to document;
- no sequential IDs;
- may expire;
- does not grant Tab mutation access.

## Production ticket fallback

Production ticket exists as **fallback** for station operations, not canonical queue state.

Generation trigger modes per station:
- DISABLED;
- ON_DEMAND;
- AUTO_FALLBACK;
- OPTIONAL_MIRROR if venue intentionally wants paper alongside KDS.

P0 recommended default: ON_DEMAND/AUTO_FALLBACK, not mandatory mirror.

A production ticket is generated from confirmed OrderItems routed to that station.

Content:
- Order/short reference;
- Tab/destination current operational label where appropriate;
- item names/quantities;
- variants/modifiers/removals;
- exceptional notes;
- confirmed_at;
- prominent REPRINT marker when applicable.

Payment totals should not be included unless operationally necessary.

## Preventing accidental duplicate production

### Logical print identity

Initial production dispatch key:
station + confirmed order/order-item batch + production_generation.

Only one initial logical ticket may be created for that key.

Retry:
- same PrintJob/logical ticket;
- no new production generation.

Reprint:
- explicit user action;
- new job linked to original;
- ticket displays “REIMPRESSÃO” prominently;
- audit records actor/reason if venue policy requires.

KDS must not create a second OrderItem/task because a ticket was printed/reprinted.

## Auto-fallback

AUTO_FALLBACK may trigger when:
- station KDS heartbeat/read-model is unhealthy beyond threshold;
- API is healthy and Order is canonical;
- printer endpoint is healthy enough to accept job.

It must not trigger merely because one WebSocket message was delayed.

Deduplication ensures that repeated health checks do not enqueue duplicate logical production tickets.

When KDS recovers, it re-fetches canonical queue and can show that fallback ticket was issued; no duplicate work item is created.

## Network printer

Preferred server/LAN adapter where available:
- endpoint/address stored as config reference;
- adapter reports send success/failure and health when protocol supports it;
- timeout is not automatically treated as “not printed”; uncertain result may require operator-visible state to avoid blind duplicate print.

## Bluetooth printer

Supported primarily from Android where device/SDK permits.

Rules:
- paired/authorized device configured as PrinterEndpoint;
- local print result is reported back to backend PrintJob;
- if backend cannot be reached, local print of canonical cached document is allowed only when document was already server-created and job identity was reserved/known;
- otherwise treat as manual contingency, not canonical print success.

PWA Bluetooth is not a P0 requirement.

## Printer state

Normalized health:
- ONLINE;
- DEGRADED;
- OFFLINE;
- UNKNOWN.

Detectable detail may include:
- paper_out;
- cover_open;
- connection_error.

Only report a condition if adapter can actually know it. UNKNOWN is valid.

Printer status never blocks unrelated POS operation.

## Print lifecycle / ambiguity

If adapter reports definitive failure before accepting data:
- FAILED_RETRYABLE.

If send outcome is ambiguous:
- job becomes FAILED_RETRYABLE_WITH_CAUTION or equivalent normalized uncertain state;
- UI says printer may have printed;
- automatic retry policy is conservative for PRODUCTION_TICKET;
- operator may choose explicit reprint, visibly marked.

For customer receipts, automatic retry can be more permissive if duplicate paper has no production consequence.

## Multiple stations/printers

- a Product/OrderItem routes to FulfillmentStation per canonical routing;
- station binding determines eligible printer(s);
- one station may have primary + fallback printer;
- one printer may serve multiple stations if configured;
- changing binding does not alter historical Order routing.

Failover printer gets the same logical document with controlled job identity.

## What remains operable without printer

Always:
- open/find Tab;
- confirm Orders if API healthy;
- KDS/Bar queue;
- Payment;
- Tab close;
- digital receipts;
- Management.

If all printers fail, system shows print exception but never blocks canonical transaction solely for lack of paper.

## API / commands / queries

Commands:
- create_customer_check(tab_id, expected_version);
- create_payment_receipt(payment_id);
- request_print(document_id, printer?, purpose, idempotency_key);
- request_reprint(job_id, actor, reason?);
- retry_print_job(job_id);
- update_printer_health(... adapter/system);
- configure_station_printer_binding(... Spec 013 orchestration).

Queries:
- receipt_document(id/token);
- print_job_status(id);
- printer_health;
- printable_documents_for_tab/payment.

## Permissions

- STAFF/CASHIER: print customer check/receipt;
- station staff: on-demand production ticket/reprint for own station;
- MANAGER: any reprint, printer/binding management, review print failures;
- OWNER: configuration privileges according to Spec 013.

Guest can view authorized digital receipt, not send production prints.

## Realtime

Print status may update requesting surface and Gerência.

Production queue does not depend on print realtime. Printer health changes may generate actionable notification only under Spec 018 rules.

## Concurrency / idempotency

- document generation uses source id/version;
- initial production logical key unique;
- print request idempotency prevents duplicate jobs;
- worker uses claim/lease to avoid two workers sending same attempt concurrently;
- explicit reprint always creates a new linked job with REPRINT semantics;
- retries update same logical job/attempt history.

## Connectivity / degraded behavior

### WebSocket down, API healthy
No special print restriction.

### Printer unavailable
Queue/retry or choose fallback; POS remains active.

### API unavailable
P0 does not generate new canonical production tickets because canonical new Orders cannot be confirmed.

Manual paper runbook may be used outside canonical system.

Optional future offline recovery printing may print PendingOrderIntent only with:
- OFFLINE / NÃO SINCRONIZADO watermark;
- recovery_id;
- explicit operator action;
- later reconciliation that prevents automatic initial production ticket from being mistaken as new work.

This optional mode is **not P0 default**.

## Formatting

Templates must be deterministic and versioned.

Thermal defaults:
- support common 58/80mm widths through renderer capability;
- text remains legible;
- modifiers/removals indented;
- no dependence on color;
- QR only when useful and opaque.

Digital rendering may be responsive HTML/PDF-like view, but fiscal styling must not imply legal tax document.

## Audit

Audit:
- explicit reprint;
- printer/binding config;
- manual cancellation;
- production fallback issuance where operationally material.

Ordinary automatic print attempt logs are technical telemetry; not every byte-send requires AuditEvent.

## Metrics/events

Events:
- receipt.generated;
- print.job_queued;
- print.succeeded;
- print.failed;
- print.reprinted;
- production.fallback_ticket_issued.

Metrics:
- print failure/retry rate;
- station fallback count;
- time order-confirmed -> fallback print;
- printer offline duration;
- reprint count/reasons.

Do not use reprint count as simplistic staff performance score.

## Security/privacy

- no sensitive card data;
- digital receipt token opaque/expiring;
- printer network credentials secret-managed;
- sanitize notes/content to printer-safe text;
- guest receipt scope cannot expose other Tabs;
- raw provider payloads are not printed.

## Migration / backward compatibility

No existing domain record changes required beyond optional receipt/print references. Historical payments can generate digital receipt from persisted safe canonical fields when possible; exact provider receipt text may be unavailable.

## Depends on

- Spec 001 Ordering/Fulfillment.
- Spec 003 station/dispatch context.
- Spec 006 confirmed Payment/Refund semantics.
- Spec 008 permissions.
- Spec 010 customization snapshots.
- Spec 011 pricing presentation.
- Spec 014 degraded-mode rules.

## Integrates with

- Spec 013 may expose PrinterEndpoint and station-binding configuration through Gerência once Spec 015 contracts are available.

## Enables

- paper check/receipt;
- KDS production fallback;
- operational continuity without making printers mandatory.

## Deliberately deferred

- fiscal documents;
- certified tax printers;
- mandatory offline production printing;
- direct messaging/email receipt delivery;
- printer fleet management suite.

## Implementation contract — 2026-10-09

P0 supports staff-authorized immutable checks, partial/payment receipts, closed-Tab receipts,
and station-scoped production snapshots. Canonical ledger `totals` supplies all financial
values, including adjustments, refunds and transfers; Spec 011 pricing rules are not duplicated.
Production starts ON_DEMAND. Automatic KDS-health fallback and Bluetooth remain disabled
until trustworthy heartbeat/device contracts and real hardware verification exist.

Delivery states distinguish QUEUED, SENDING, FAILED_RETRYABLE, FAILED_FINAL,
DELIVERY_UNCERTAIN, SPOOL_ACCEPTED, OUTPUT_READY, PRINTED and CANCELLED.
Only explicit operator paper confirmation marks PRINTED. Spool acceptance and file generation
never prove paper output. Expired sending leases become uncertain, never automatically resent.
Only definitive failure before submission permits bounded automatic retry. All other outcomes
require explicit linked, watermarked reprint. Initial production dispatch is unique per
order/station/endpoint; retries retain the same job. Each attempt has a fencing token.
Browser HTML and portable text are supported at 58/80mm; ESC/POS uses sanitized ASCII
transliteration by default, with cutting opt-in after device verification. Local worker
configuration maps opaque connection references to LAN addresses or OS spool queues;
credentials and network addresses never come from customer document data.
Fiscal issuance requires separate Aderlan/accountant/provider approval and is excluded.


### Implemented API and rollout boundary

The module is `documents_printing`. Staff APIs under `/printing/` cover document creation,
printer/binding configuration, job status/history/failure filtering, explicit linked reprint,
safe retry, cancellation and audited paper confirmation. Outbound bridge claims/results
are authenticated and fenced. Public receipt links expire after 24 hours and are revocable;
GuestSession receipt reads are scoped to the authorized Tab. Digital delivery reuses the
same immutable check/payment/closed-Tab snapshot rather than introducing competing totals.

Financial item presentation reuses the existing Tab responsibility read model. A transferred
share identifies the original item/quantity and the canonical transferred quantity or amount;
printing never invents fractional quantities or reallocates discounts. PostgreSQL prohibits
receipt UPDATE/DELETE even through raw SQL. Receipt token URLs are redacted by the existing
credential logging boundary.

Verified P0: browser/HTML/text, browser-generated PDF, sanitized ESC/POS, file/LAN/CUPS
adapter boundaries, on-demand station ticket, durable queue/retry/recovery, permissions,
audit, management configuration and failure pagination. Not enabled: automatic KDS-health
fallback, Bluetooth/native Android printing, direct native Windows spooler, provider-specific
mandatory receipt metadata and fiscal issuance. Existing Android ordering/payment flows
remain canonical; printer integration is optional and outside their critical transactions.
These deferred capabilities require explicit device/provider/heartbeat contracts; they are
not inferred from an unverified Aderlan printer model.
