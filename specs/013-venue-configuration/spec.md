# Spec 013 — Venue Configuration

**Status:** Draft for implementation  
**Owner capability:** Venue configuration orchestration

## Objective

Let manager/owner configure a Venue safely from Rodada without database access, while each domain remains owner of its own rules and validations.

## Product problem

A production POS cannot depend on developer/database edits for tables, stations, staff, business date, guest ordering, service charge, thresholds or providers. At the same time, one generic JSON settings bucket would make domain ownership and safe rollout impossible.

## Scope

Typed configuration for:
- Venue profile;
- staff management entry points;
- role/capability policy;
- FulfillmentStations;
- Zones;
- ServicePoints;
- Tables/FloorPlans;
- guest ordering modes/defaults;
- business-date cutoff;
- operating hours;
- service-charge policy;
- SLA/alert thresholds;
- payment-provider bindings;
- printer endpoints/station bindings;
- catalog defaults;
- limited feature/capability switches;
- validation, audit and safe live changes.

## Explicitly out of scope

- arbitrary key/value settings;
- ERP/master-data suite;
- accounting/fiscal setup;
- secrets displayed in UI;
- custom workflow scripting;
- multi-company corporate administration;
- editing canonical facts/history through configuration.

## Ownership principle

Venue Configuration is an **orchestration surface**, not the owner of all rules.

Examples:
- staff membership semantics: Spec 008;
- table lifecycle: Spec 004;
- service charge calculation: Spec 011;
- payment capabilities: Spec 006;
- notification lifecycle: Spec 018;
- cash rules: Spec 012.

Configuration calls domain-owned commands and stores typed policy records in the appropriate module.

## Domain concepts

### VenueProfile

- display_name;
- timezone;
- locale/currency (BRL for pilot unless explicitly extended);
- optional public contact/display metadata.

Changing currency after financial data exists is out of scope for P0 and blocked.

### VenueOperationsPolicy

Typed operational settings:
- business_date_cutoff_local_time;
- optional operating_hours schedule;
- default guest ordering policy;
- default cash review threshold reference;
- other explicitly modeled fields only.

### VenueConfigurationChange

Audit/provenance record:
- venue_id;
- section;
- resource id;
- old snapshot/hash;
- new snapshot/hash;
- actor;
- reason when required;
- applied_at;
- effective_at;
- change_mode.

### Change mode

Each config mutation declares one of:

- IMMEDIATE_SAFE: takes effect for new actions immediately without invalidating active work;
- VERSIONED_NEW_CONTEXT: new Tabs/occupancies/orders use new policy while active contexts keep captured policy;
- REQUIRES_QUIET_STATE: blocked until affected active state is absent/resolved.

No generic operator chooses this mode; it is defined by the domain command.

## Invariants

1. No arbitrary configuration key may bypass typed domain validation.
2. Every config mutation is authorized server-side and audited.
3. A live config change cannot silently rewrite an active Order, Payment, CashShift, TableOccupancy or closed report.
4. Policies affecting historical calculation are snapshotted/versioned when the domain requires reproducibility.
5. Provider secrets are stored through secure integration infrastructure; config surfaces only references/status/capabilities.
6. Deactivating a physical/catalog resource with active dependencies must fail or use a domain-defined safe transition.
7. MANAGER and OWNER permissions differ by sensitivity.
8. Guest/public projections never expose internal provider credentials, staff config or operational thresholds not meant for guests.
9. Business date is based on Venue timezone + configured cutoff.
10. Feature switches represent named product capabilities, not hidden arbitrary flags.

## Venue profile

OWNER can edit legal-independent display profile fields. MANAGER may edit operational display fields if granted.

Timezone change:
- requires OWNER;
- must not rewrite historical timestamps/business dates;
- new business-date computation uses new timezone only from explicit effective boundary;
- should normally be REQUIRES_QUIET_STATE or scheduled at next business date.

## Staff management entry points

Gerência provides links/views for:
- memberships;
- role;
- status;
- sessions/devices;
- revoke.

Actual commands use Spec 008.

P0 keeps baseline roles STAFF/CASHIER/MANAGER/OWNER. Venue may enable documented capability overrides; do not add arbitrary custom-role designer unless future need justifies it.

## FulfillmentStations

Manager can:
- create station;
- rename/display-order;
- activate/deactivate when safe;
- configure which operational staff can manage station availability through access policies.

A station with active queued OrderItems cannot be destructively deleted. Deactivation affects new routing only after validation; historical routing snapshots remain.

## Zones and ServicePoints

Use Floor/Dispatch domain commands.

Manager may:
- create/rename/reorder Zones;
- create/move/deactivate ServicePoints.

Moving a ServicePoint is IMMEDIATE_SAFE for current location context if domain allows. Deactivation with active Tabs/tasks requires explicit resolution.

## Tables and FloorPlan

Use Spec 004:
- create physical Table + opaque QR;
- label;
- guest_ordering_mode override;
- active/out-of-service controls;
- FloorPlan canvas;
- placements/grouping are operational state, not static config.

Deleting a Table with history is prohibited. Archive/deactivate instead.

## Guest ordering policy

Typed settings:
- venue default: DISABLED | JOIN_ACTIVE | DIRECT;
- per-Table override;
- optional requirement for active occupancy;
- guest service-request categories enabled;
- explicit global emergency block.

Changes do not revoke already confirmed Orders. Immediate block prevents new guest mutations as Spec 004 defines.

## Business date cutoff

Persist:
- Venue timezone (IANA zone);
- cutoff local time, e.g. 06:00.

Rule:
business date for timestamp is derived according to Venue timezone and cutoff.

Changing cutoff:
- OWNER/MANAGER with capability;
- effective from next not-yet-started business date by default;
- historical DailyOperationsSummary keeps original business_date/version;
- active shift/day shows pending effective change.

## Operating hours

Optional schedule used for:
- guest messaging;
- management comparisons;
- expected closing reminders.

It does **not** automatically block staff POS mutations in P0. Hard operating-hours enforcement needs explicit future policy.

Exceptions/holiday hours may be added later; do not build calendar ERP now.

## Service charge policy

Configured through Spec 011 typed policy:
- enabled;
- default basis points;
- staff/cashier/manager thresholds;
- ordinary opt-out behavior;
- reason requirements.

Changes default to VERSIONED_NEW_CONTEXT:
- existing open Tab retains captured service-charge policy version unless manager explicitly re-assesses under allowed rules;
- new Tabs use new policy.

## SLA thresholds

Typed per operational context:
- fulfillment warning/danger age by station;
- Dispatch task thresholds;
- queue-size thresholds;
- bill/service-request age.

Spec 003/018 consume these. Threshold change affects alert evaluation, not underlying task timestamps.

Validate warning < danger where both exist, non-negative durations/counts and sensible upper bounds.

## Alert thresholds/routing

Spec 018 owns lifecycle. Config surface controls:
- enabled actionable alert rules;
- severity thresholds;
- role routing;
- cooldown;
- escalation delay;
- push eligibility.

No “notify every event” global toggle.

## Payment provider configuration

Domain-facing binding:

VenuePaymentProviderBinding:
- provider adapter type;
- enabled methods;
- environment/account reference;
- status: UNCONFIGURED | PENDING | ACTIVE | ERROR | DISABLED;
- normalized capabilities.

Secrets/API credentials:
- encrypted/secret store;
- never returned to ordinary read API;
- masked/replaced through dedicated setup flow.

Provider-specific fields stay in adapter configuration boundary. Tab/Payment domain stays neutral.

Changing/disabling provider:
- cannot invalidate PROCESSING/CONFIRMATION_PENDING Payments;
- new attempts may be blocked/redirected only after validation;
- outstanding reconciliation remains tied to original provider.

## Printer configuration

Spec 015 owns receipt/printing semantics. Venue Configuration exposes typed setup for:

- PrinterEndpoint label/type/enablement;
- network/Bluetooth connection reference without exposing secrets;
- station → primary/fallback printer bindings;
- permitted print purposes;
- health/status readout.

Changing a printer binding never changes historical Order routing or makes printing the source of truth. Disabling/removing the last printer is allowed when KDS/digital operation remains healthy; the UI must state the resulting fallback capability.

## Catalog defaults

Typed defaults may include:
- default currency inherited from Venue;
- default Product availability for quick-create;
- station default context;
- icon style version reference.

Do not put Product-specific prices/options in Venue config.

## Feature/capability switches

Allowed only for named deployable capability boundaries, e.g.:
- guest_ordering_enabled;
- tap_to_pay_enabled;
- guest_payment_enabled;
- passive_fulfillment_telemetry_enabled.

A switch cannot bypass required provider/config/dependency validation.

Feature switches are not permission checks.

## Validation / preview

Sensitive changes support:
- validate;
- preview impacted active resources;
- apply.

Examples:
- deactivating station returns active queued items;
- changing provider returns pending payments;
- changing cutoff returns effective business date.

Server is authoritative; UI cannot force apply by skipping preview.

## Safe changes during active service

### Immediate-safe examples
- rename Zone/Table display label;
- SLA threshold;
- guest global block;
- alert cooldown.

### Versioned-new-context examples
- service charge default;
- certain Tab policy defaults;
- catalog defaults.

### Requires-quiet-state examples
- disable payment provider with pending attempt;
- deactivate only station serving active queued items;
- currency change;
- destructive-like structural changes.

When blocked, response includes exact active blockers.

## Permissions

MANAGER by default:
- floor/station/guest settings;
- SLA/alert thresholds;
- operational catalog defaults;
- view provider status.

OWNER by default:
- staff manager/owner roles;
- payment provider credentials/binding;
- business-critical security settings;
- timezone/currency-sensitive changes;
- capability override policy.

Venue may grant narrower explicit capabilities via Spec 008, but no self-escalation.

## API / commands / queries

Configuration queries are sectioned, not one JSON blob:
- get_venue_profile;
- get_floor_configuration;
- get_guest_policy;
- get_pricing_policy;
- get_alert_policy;
- get_payment_provider_bindings.

Commands call domain owners:
- update_venue_profile;
- update_business_date_policy;
- configure_station;
- configure_zone/service_point/table/floorplan;
- update_guest_policy;
- update_service_charge_policy;
- update_sla_alert_policy;
- configure_payment_provider_binding;
- configure_printer_endpoint / station_printer_binding;
- update_catalog_defaults.

All mutation responses include effective_at/version and blockers/warnings where relevant.

## Realtime

Immediate-safe changes may invalidate affected clients:
- catalog/floor/guest policy;
- alert rules;
- provider capability availability;
- printer/binding configuration where connected clients consume it.

Clients re-fetch canonical config. Realtime payload need not contain secret/sensitive config.

## Concurrency / idempotency

- config records/versioned resources use optimistic concurrency;
- idempotency for provider setup/apply and any mutation with external side effect;
- concurrent editors receive stale-version conflict and current snapshot;
- domain command ensures active-resource checks and config mutation are transactional where needed.

## Error / degraded behavior

Configuration mutation is online-only.

If API/realtime unavailable:
- existing apps continue with last known safe configuration only for operations Spec 014 permits;
- manager UI marks config stale;
- no local provider/permission/service-charge policy mutation is assumed active.

## UX — Gerência

Under Gestão/Mais:
- Estabelecimento;
- Pessoas e dispositivos;
- Salão/ambientes;
- Produção;
- Pedidos do cliente;
- Pagamentos;
- Preços e serviço;
- Alertas e SLAs;
- Caixa.

Mobile-first:
- section summaries + status;
- forms short and domain-specific;
- show “entra em vigor agora / próximo turno / bloqueado por X” before save;
- dangerous changes require explicit confirmation, not generic settings maze.

## Metrics/events

Events:
- venue.configuration_changed with typed section/reference;
- provider.binding_changed;
- business_date_policy.changed;
- operational_threshold.changed.

Management may show config timeline for investigation.

Do not produce analytics from mere viewing/editing activity.

## Audit

Every mutation records actor/session/device, old/new typed state, effective boundary and reason where required.

Secrets are never copied into AuditEvent.

## Security/privacy

- strict OWNER/MANAGER capability checks;
- secret values write-only/masked;
- CSRF/session protections;
- no public guest exposure of internal configuration;
- configuration text sanitized;
- provider webhooks/credentials remain adapter-owned.

## Migration / backward compatibility

Current hardcoded/default values become typed records with behavior-preserving defaults:
- existing guest mode stays as configured per Table;
- business cutoff defaults to current documented behavior until explicitly changed;
- payment provider binding reflects existing adapter setup if present;
- no active resource is auto-deactivated.

## Depends on

- Specs 001–008 domain foundations.
- Spec 011 service-charge semantics.
- Spec 012 cash thresholds.
- Spec 018 alert rule/routing semantics.
- ADRs 0004/0005/0007/0008.

## Enables

- production operation without DB edits;
- consistent alerting/closing/payment setup;
- pilot onboarding and repeatable Venue provisioning.

## Deliberately deferred

- arbitrary custom roles;
- config scripting;
- corporate multi-Venue inheritance;
- fiscal/accounting settings;
- generic feature-flag platform.

## Entrega executável Web — Spec 020

O contrato implementado nesta entrega e seus critérios verificáveis estão na [Spec 020](../020-web-operational-completion/spec.md). Inclui catálogo com fallback de ícones (IA/worker adiados pelo usuário), histórico da própria comanda guest, seleção/revisão de turnos antigos, relatórios operacionais e calendário auditado. Não marca todo o roadmap desta spec como concluído. Consulte [validação e limites](../../docs/development/web-operational-completion.md).
