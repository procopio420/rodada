# Tasks — Spec 028

**Legend:** [ ] = pending. Writing a spec does not count as implementing an item.

## Contracts / backend
- [ ] Trace Spec 015 state/route APIs and freeze backwards compatibility for legacy bridge.
- [ ] Add scoped PrintAgent identity (Access), lifecycle and audit migrations.
- [ ] Implement pairing start/status/approval: high-entropy single-use expiring codes, proof of possession, throttling and Venue membership.
- [ ] Implement device-scoped credential issue/rotation/revocation and API authentication middleware; never reuse staff refresh token.
- [ ] Add discovered devices and AgentPrinterRoute, route profile/capability/version CAS, schema+indexes+retention.
- [ ] Implement agent heartbeat/version and manager status APIs without conflating physical printer health.
- [ ] Implement agent-limited claim/results using existing PrintJob lease/attempt token and mapping checks.
- [ ] Preserve PrintJob initial production uniqueness across endpoints; no double print when multiple agents can reach one endpoint.
- [ ] Fault handling for pre-send error, ambiguous submit, interrupted result, revoked device and route move during send.
- [ ] Validate server-side private-LAN destinations; no arbitrary internet print from configured route.
- [ ] New backend tests: isolation, replay, races, negative auth, CAS, health and failover safety.

## Windows agent
- [ ] Skeleton at apps/printer-agent with typed contracts and tests; no Django model dependencies.
- [ ] Windows Service + optional local wizard/status window, no logged-in desktop session requirement.
- [ ] Installer setup/remove/repair + machine-scope DPAPI secrets/ACL and safe unpair.
- [ ] Windows Print Spooler printer/queue enumeration in service context.
- [ ] WinSpool GDI/raster WindowsDriver (non-RAW), print preview/test page and status normalization.
- [ ] Windows RAW spool adapter gated on verified ESC/POS profile; block raw commands to incompatible queue.
- [ ] LAN TCP adapter with private address validation, optional scoped discovery + manual IP.
- [ ] PrinterProfile registry (generic ESC/POS, WindowsDriver and conditional Bematech).
- [ ] Test ASCII/UTF-8/codepage behavior and Portuguese diacritics; feature flags for cut/QR/status.
- [ ] Agent telemetry, bounded redacted logs, local diagnostics, spool accepted != printed.
- [ ] Host restart/agent crash/resume safe attempt recovery; never blind-resend uncertain ticket.
- [ ] Simulate USB, shared Windows queue, network printer and duplicate network visibility in two agents.
- [ ] Background update with signature validation, idle/roll-back semantics and version compatibility.

## Web/landing/release
- [ ] Expand /manage/printing with Add computer, pairing approval, agent list/revoke, discovered printers and routes.
- [ ] Configure BAR, KITCHEN and receipt destination from logical endpoint; no raw credentials to browser.
- [ ] Add test print flow, normalized errors and visible uncertain result + reprint authorization.
- [ ] Add /downloads page to apps/landing, same stable artifact used by Manage, SHA/version/help.
- [ ] Windows GitHub Actions pipeline, lock dependencies, test install/uninstall, build immutable artifacts.
- [ ] Authenticode release signing and updater manifest; public stable download only after signing/hardware gate.
- [ ] Ops runbook onboarding, printer model compatibility matrix, support/recovery and rollback.

## Pilot acceptance
- [ ] Inventory Aderlan PC OS, printer models, connection/ports and installed drivers (real hardware).
- [ ] Print physical Bematech test page under actual service account on Windows.
- [ ] Run kitchen/bar correct station routing, original vs REIMPRESSÃO, receipt and PDF fallback.
- [ ] Simulate second Windows agent and network printer accessible by both; prove only one send.
- [ ] Test queue offline, USB unplugged, spool restart, LAN down, VPN/rebinding, revoked token, expired lease.
- [ ] Observe and record the outcome *on physical paper*; no CI-only go-live claim.
- [ ] Decide venue trigger mode OPTIONAL_MIRROR separately, after Spec 015 health/fallback gates.
- [ ] Record release SHA, installer checksum, profile/driver/OS and approved go/no-go sign-off.
