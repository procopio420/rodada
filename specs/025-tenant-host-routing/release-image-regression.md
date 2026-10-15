# Spec025 release gate — standalone print contract missing from disposable image

The existing #130 closure contract requires Integrated release demo as a
PostgreSQL/restart/finance gate; this is a packaging regression, not a new feature
or a tenant-isolation exploit. The contract test must run unchanged and pass in
the disposable image; do not skip it or narrow the suite to obtain a green gate.

Baseline `b63b6111d66c640e8d4fde8ab2042743c9083eee`,
[Integrated release38671565495](https://github.com/procopio420/rodada/actions/runs/38671565495):
real HTTP shift/service+PostgreSQL restart PASS, then **853PASS/1FAIL** in438.17s.
`tests/test_print_agents.py::test_standalone_contract_matches_backend` raised
FileNotFoundError at `/app/apps/printer-agent/rodada_printer_agent/contracts.py`.
The full checkout API gate passed this same test: the disposable image copied
API and legacy print-bridge but omitted the standalone agent contract source.

Correction scope: copy only that existing dependency-free contract file into
its repository-relative image location in `demo/api.Dockerfile`. No contract
values, API test, production Railway Dockerfile, startup, database, credentials,
PSP, ports or deployment flags change. Nothing starts or pairs a print agent.

Acceptance: build the disposable demo API image; rerun the existing contract
comparison and complete Integrated release demo, including all PostgreSQL tests
and restart. Record exact SHA/run and actual results; pending until executed.
Independent review is required before integration. This does not authorize the
shared tenant UI flag or satisfy browser/pilot/separate-preview acceptance.


Executed candidate validation: exact `f02d11da39ca28143e1f695f18977b45d49ee8e1`,
[Integrated release38672594038](https://github.com/procopio420/rodada/actions/runs/38672594038)
**SUCCESS**, all854 PostgreSQL tests passed in428.63s including the unchanged
standalone comparison; HTTP shift and PostgreSQL/service restart also PASS.
Independent R3 read of the two-file candidate reported NO_FINDINGS_WITH_GAPS,
no reproducible finding. [PR168](https://github.com/procopio420/rodada/pull/168)
merged `75f637f8e5297b960375df8c1dd83b6478a5d1ec` after candidate gates green.
Final integration/runtime evidence is tracked in the [checkpoint](railway-151-checkpoint.md).

## Registry transport failure — 2026-10-15

Main637b8e6 release38678091658 attempts1/2 failed before tests: public ECR refused
PostgreSQL17 download with `toomanyrequests: Rate exceeded`. No application test
failed or was executed in those attempts. The isolated pilot shift already uses
`mirror.gcr.io/library/postgres:17`; use that same public PostgreSQL17 distribution
for release validation. Keep the same version, disposable DB, full pytest and
restart checks. No production service/image/source configuration is changed.
Acceptance requires the complete existing release gate on the candidate, without
skipping tests or interpreting a download error as PASS. Review independently.
