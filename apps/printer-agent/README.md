# Rodada Impressoras

S1 implements standalone Python 3.12 protocol types and driver/transport boundaries.
No Windows service, local credential storage, spooler integration or installer is
implemented yet. Those are delivered sequentially in Spec 028 S2–S6.

`rodada_printer_agent/contracts.py` has no Django dependencies. Protocol v1's
initial authenticated read is `GET /printing/agents/v1/me/contract/` using a
machine `rpa_` bearer. Only `contract` is currently advertised; delivery is false.
Credentials are issued only through the internal Access service after a paired
identity exists. There is no public bootstrap or staff-token conversion endpoint.

Development checks:

```sh
python -m mypy --strict apps/printer-agent/rodada_printer_agent
python -m ruff check apps/printer-agent/rodada_printer_agent
cd apps/api
pytest --ds=rodada_api.settings tests/test_print_agents.py
```

Use a disposable PostgreSQL database, never a shared bar/demo database. Physical
support for Bematech or any other model is unverified. Spool acceptance never
means physically printed paper.
