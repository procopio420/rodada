# Operational evidence executors

`live-browser-executor.cjs` runs Chromium against the two reserved QA hosts,
with TLS validation enabled. Writes target only those QA hosts; an explicit
unknown-host read probe checks rejection. Use it only in an authorized controlled
window, after verified recovery, current source/deployment checks, authenticated
pilot smoke and activation of the reviewed QA identities/domains and shared flag.
It is evidence tooling, not an administrative endpoint or startup seed.

Provide its JSON contract through a private in-memory stdin pipe:
`sha` (observed runtime commit), `run` (unique audit identifier), `pins` (`a` and
`b`, decrypted only in memory), and `ids` (expected QA Venue UUIDs). Never place
that payload in a file, shell command/history, log, workflow artifact or issue.
The caller must independently read back runtime SHA/deployment/flag **before and
after** execution and reject a report if they change. `sha` supplied by the caller
alone is not evidence that a deployment was tested.

Requires the existing Web Playwright dependency and its installed Chromium.
Optionally select an already installed browser with `SPEC025_CHROMIUM_PATH`.
No screenshot, trace, storage state, cookie, token, QR selector or PIN is retained.
Output contains scenario/status results and QA object UUIDs only. A failed
scenario stops the matrix and still attempts logout; it never authorizes PASS.

Writes are restricted to QA guest policy, table/catalog definitions, physical
groups and empty nonfinancial Tabs/occupancies. No Order, Charge, Payment,
Refund or cash operation is issued. Existing pilot credentials are not accepted
by this executor. Monetary scenarios belong exclusively to disposable PostgreSQL.

Regardless of success, turn the shared flag off, observe that exact deployment
succeed, and run `provision_spec025_ab --operation deactivate --apply` through
private SSH. Verify memberships/sessions/guest issuance/SSE containment, QA421,
pilot authenticated smoke and foreign-history preservation. Do not restore the
operational database to demonstrate rollback. Detailed commands and archive
recovery format are in `docs/ops/spec025-preview-rollout.md`.
