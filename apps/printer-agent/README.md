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
