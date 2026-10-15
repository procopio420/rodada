# Rodada Impressoras

S2 provides the Windows service, persistent installation identity, manager-approved
pairing, machine DPAPI storage with a service SID ACL, heartbeat and revocation.
The optional local diagnostic window reads only public status and pairing code.
Protocol v1 advertises contract, activate and heartbeat; delivery remains false.
No spooler, print claims, installer or public stable release is implemented yet.

Service configuration and operational instructions: see
`../../specs/028-windows-printer-agent/s2-pairing.md`.

Development checks:

```sh
python -m pytest apps/printer-agent/tests/test_worker.py -q
python -m mypy --strict apps/printer-agent/rodada_printer_agent
python -m ruff check apps/printer-agent
```

The Windows CI also installs and starts the actual service in session 0, exercises
DPAPI and access denial, restarts it and verifies revocation. Physical support for
Bematech or any other printer remains unverified. Spool acceptance never means
physically printed paper.


## S3 development printing (0.3.0)

Service enumerates queues under LocalService/service SID, not an interactive login.
In Manage > Impressoras, create a Computador Rodada Impressoras destination, then
select an observed queue and enable its route. WindowsDriver uses GDI/installed
printer driver; no ESC/POS bytes are sent through that rendering path.

RAW ESC/POS ASCII is opt-in only after an operator actually tests that connection.
The CI attestation fixtures are synthetic, not printer certification. Cut/QR/status
commands stay disabled. Changed queue/driver invalidates the route and attestation.

For a direct LAN printer, an administrator may configure approved literal private
addresses on the local installation (no scan/DNS/public targets):

```powershell
python -m rodada_printer_agent configure --api-origin https://api.rodada.bar --tcp-printer 192.168.1.50
```

Repeat --tcp-printer for several printers; the explicit list replaces earlier TCP
configuration. Reconfiguring without that argument preserves the existing list.
The API still requires manager assignment and attested RAW compatibility; local
configuration alone cannot claim work. Stop/restart the service after configuration.

Only one in-flight result journal persists in DPAPI; no document/queue is stored.
Restart reconciles that result without resubmitting. Expired claims (monotonic
conservative TTL) do not enter the transport. Spool/network acceptance is not paper.
Inspect DELIVERY_UNCERTAIN before an explicit audited reprint. Drivers already
entered can block beyond a lease; fencing cannot retract bytes already submitted.
Installer, updates and signed stable distribution remain S6; physical checks S7.
