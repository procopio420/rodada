# Rodada Impressoras

Version 0.5.0 includes the Windows service, persistent installation identity,
manager-approved one-time pairing, machine DPAPI storage with service SID ACL,
heartbeat/revocation, discovery, fenced multiagent delivery and explicit printer
profiles. The optional local diagnostic window reads public status and pairing
code. Protocol v1 enables delivery only for approved routes; S2 clients (0.2.0)
continue with delivery disabled and 0.3.0 clients cannot claim PC860 profiles.

A universal self-contained Windows installer is built and smoke-tested in CI as
**unsigned pilot only**. Install/repair/reinstall/uninstall are implemented; public
signed stable distribution and physical certification remain blocked. There is no
unattended updater. See [mission evidence](../../specs/028-windows-printer-agent/completion-20261020.md)
and [pilot procedure](../../specs/028-windows-printer-agent/s7-pilot.md).

Service configuration and operational instructions: see
`../../specs/028-windows-printer-agent/s2-pairing.md`.

Development checks:

```sh
python -m pip install -e "apps/printer-agent[dev]"
python -m pytest apps/printer-agent/tests -q
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
Packaged installation/upgrade is described below; signed stable distribution and physical checks remain gated by S6/S7.

## S5 compatibility and S6 unsigned packaging

Agent 0.5.0 accepts explicit PC860 profiles, optionally full cut after route-level
physical approval; unrepresentable characters become `?`. WindowsDriver retains
Unicode and is the first candidate for the Bematech MP-4200 TH. Neither model nor
profile name is evidence of physical certification.

`packaging/requirements-build.txt`, `entry.py` and `installer.iss` build a universal
Windows 11 x64 installer in CI, no installed Python required. All generated setup
artifacts are **unsigned pilot only**. Manual reinstall preserves DPAPI identity
and journal; uninstall retains ProgramData for authorized recovery. Do not delete
that journal to resolve an uncertain ticket. No unattended update is enabled.
Signed distribution, distinct-version rollback and physical pilot are external
NO-GO gates; see Spec028 s6-distribution.md and S7 pilot procedure.
