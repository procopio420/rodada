# Documents / Printing agent foundation

Spec 015 owns immutable ReceiptDocument, PrintJob, PrintAttempt, leases, fencing
and conservative delivery outcomes. Spec 028 extends fleet metadata, not the queue.

S1 adds PrintAgent, PrintPairingRequest, DiscoveredPrinter and AgentPrinterRoute;
Access owns AgentCredential. Venue.print_agents_enabled defaults false. Agents
have no staff session or staff capability grant. Device registration and paired
agent identity must share one Venue. PostgreSQL triggers reject tenant reparenting,
credential resurrection and inconsistent routes, including bulk/raw SQL writes.

Machine read: `GET /printing/agents/v1/me/contract/`, opaque `rpa_` bearer. It exposes
only its own identity/scope and advertises `delivery_enabled=false`. A resolved
signed tenant Host must match the agent Venue. Staff tokens are rejected here;
agent tokens are rejected by all existing staff and legacy bridge endpoints.

Internal Access lifecycle services (`issue_credential`, `revoke_agent`) require a
valid print.manage session in the same Venue. Issuance requires a paired/trusted
agent and enabled Venue flag. The raw secret is returned once, never persisted;
rotation invalidates the previous token, credentials expire after 30 days, and
revocation preserves audit/routes/history. No public issuance or staff conversion
endpoint exists. S2 adds proof-of-possession bootstrap and manager approval;
only the requesting installation can recover its credential before activation.
The Windows service stores machine credentials with DPAPI and a service-SID ACL.
Heartbeat reports agent connectivity only; no printer outcome is inferred.
See specs/028-windows-printer-agent/s2-pairing.md for protocol and operations.

`configure_route` is management-only CAS metadata with audit. Route execution is
not enabled in S1; enabling a flag does not start any printing or KDS fallback.
TCP v1 validation allows literal RFC1918/ULA destinations on 9100 only. Shared
queue destination resolution/safety must be implemented before S3 transport calls.

Regression/evidence: specs/028-windows-printer-agent/s1-foundation.md and PR #149.
Use disposable PostgreSQL for test_print_agents.py; migrate/reverse/reapply and
credential/CAS races are real DB tests. No test may use a shared production Venue.
