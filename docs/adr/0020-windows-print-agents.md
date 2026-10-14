# ADR 0020 — Windows print agents, scoped pairing and logical printer routing

**Status:** Proposed for Spec 028. Non-fiscal print transport; complements ADR 0013, does not replace it.

## Context

Spec 015 already implements immutable document snapshots, station binding, queued PrintJob, fenced attempts, conservative outcomes and a bridge for LAN/CUPS/file using a human session. Aderlan has an identified Bematech MP-4200 TH but the real host, interface and driver remain unverified. The deployment must work with one Windows PC, multiple PCs with USB peripherals or the same LAN printer reachable from multiple Windows hosts.

Shipping separate per-model applications or accepting human manager refresh tokens as background-service credentials would be fragile. Installing the agent must not grant administrative permissions to anyone using the workstation.

## Decision

1. **One universal Windows service** packaged independently at apps/printer-agent, paired to exactly one Venue. Small status/pair UI is optional; background printing does not require a logged-in desktop user.
2. **Out-of-band manager approval** with short-lived single-use code and proof of possession tied to the installation. Authorized staff with print.manage selects the Venue. Slug only helps discovery; it is not an authorization signal.
3. **Dedicated machine credentials** managed by Access, restricted to agent heartbeat, discovery and eligible print claims/results. DeviceRegistration is reused where useful for lifecycle/revocation, but no StaffSession, manager PIN or permanent managerial token is stored locally. Secrets are hashed at server and protected by DPAPI + service ACL on Windows.
4. **Logical printer endpoint versus physical route:** Documents/Printing retains PrinterEndpoint and StationPrinterBinding. A new AgentPrinterRoute selects the Windows agent, observed printer, driver profile, transport and priority for a given logical endpoint. Agent/discovery are advisory; the job claim enforces Venue, route and lease/fencing centrally.
5. **Separate driver and transport layers:** ESC/POS common driver, tested Bematech specialization if necessary, Windows printer-driver path, and transports WinSpool RAW when verified, Windows spooler rendered/GDI, Windows shared queue, TCP/IP to approved private-LAN targets. Capabilities are opt-in and must be physically tested before enabling paper cut or status commands.
6. **Do not equate 'sent' with 'printed'.** Preserve OUTPUT_READY, SPOOL_ACCEPTED and DELIVERY_UNCERTAIN. Retry only if failure before any possible side effect is established; after ambiguous submission, pause until operator review. Even two viable agents may not replay an uncertain ticket.
7. **Preserve canonical authority:** print command does not create Order, Payment, DispatchTask or receipt financial totals. Spec 015 trigger modes and auto-fallback gates remain authoritative.
8. **Dual entry points, one artifact:** rodada.bar/downloads and Manage obtain identical signed stable installers via a release manifest/checksum. Installation/activation does not require Venue-specific package builds.
9. **Gradual rollout:** legacy print-bridge and BROWSER/FILE/NETWORK/CUPS adapters stay supported until a validated migration; no implicit conversion or forced automatic KDS fallback.

## Alternatives rejected

- **Manager login within installer:** leaves sensitive human credentials or ongoing staff session dependency on unattended PCs.
- **Slug only:** cannot authenticate tenant membership and enables cross-tenant misassociation.
- **Central Railway print server connecting to LAN:** requires exposing local network endpoints and cannot safely address USB.
- **Create per-model microservices:** duplicates immutable documents, queue, retries and operational semantics.
- **Let every agent poll and print every visible printer:** duplicate ticket and cross-route risk.
- **Treat spool success as physical completion:** unprovable on common thermal printers and unsafe for food production.
- **Auto-install arbitrary vendor drivers:** raises privilege, trust and reliability risk; provide an explicit compatibility guide.
- **Always fail over on timeout:** could produce duplicate kitchen instructions after a partial or completed print.

## Consequences

Pros: installs where hardware exists; covers mixed network/USB deployments; no PC inbound exposure; single product experience; predictable multi-Venue isolation; bounded hardware plugin complexity.

Costs: Windows service-context queue permissions can be difficult; code signing and upgrades require release infrastructure; many printer status signals are not dependable; a logical printer may have multiple candidate routes, requiring explicit operator configuration. Hardware compatibility claims are limited to tested profiles.

## Verification and reversibility

Implement incrementally with backend flag and existing bridge intact. Release only after security/race tests plus Aderlan printer and workstation physical certification. Disabling agent routes preserves documents, print attempts and reprint audit; operators can fall back to current Browser/legacy paths. Record supported driver/transport pairs per model rather than claiming universal compatibility.
