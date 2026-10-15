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
groups, empty nonfinancial Tabs/occupancies and fictional opt-in Customer
profiles owned exclusively by QA Relationships. Profile passwords are derived
only in memory from the protected QA seed and unique run; they are never stored
in evidence. The matrix covers profile rotation, logout and cross-visit/Host
replay; final containment also rejects these profiles through revoked GuestSessions.
No Order, Charge, Payment,
Refund or cash operation is issued. Existing pilot credentials are not accepted
by this executor. Monetary scenarios belong exclusively to disposable PostgreSQL.

Regardless of success, turn the shared flag off, observe that exact deployment
succeed, and run `provision_spec025_ab --operation deactivate --apply` through
private SSH. Verify memberships/sessions/guest issuance/SSE containment, QA421,
pilot authenticated smoke and foreign-history preservation. Do not restore the
operational database to demonstrate rollback. Detailed commands and archive
recovery format are in `docs/ops/spec025-preview-rollout.md`.

The fixture reads the per-QA contextual-service rollout policy, enables it through
the existing versioned/idempotent management API when disabled, and restores its
original false value in a separate cleanup block before logout. The shared pilot
policy is never used. Restore failures invalidate the run and require readback
(the core QA deactivate command does not reset this feature policy). QR browser
response observation follows redirects and records the final POST status; a308
is neither a QR success nor an authentication failure. Post-negative reads verify
product names, table flags, active groups and the own profile Tab association.


`railway-ab-20261015-final.json` registra a janela corrigida (173 browser e quatro
streams PASS), backout, pilot smoke e limites por SHA. O arquivo interim permanece
histórico e não prova de fechamento. `live-containment-executor.py` e
`live-stage-executor.py` recebem payload somente em memória; não executar no banco
operacional sem pré-condições/runbook. O stage preserva guardas de escopo e snapshot;
nenhum segredo ou row payload é artefato. Final review/CI e Gate3 estão separados.


Gate3: `gate3-preflight-20261015.json` e `gate3-preflight-mcp-20261015.json` são
evidência de preflight somente. Backup/restore95, leituraCASH, smoke/edge executados;
canary/backout Gate3 NOT_RUN. Não converter NO-GO em homologação pela CI.


Gate3 utiliza `gate3-browser-executor.cjs` e `gate3-containment-executor.py`,
com fixtures QA existentes; não recria Tabs, mesas, perfis, vendas ou grupos.
O browser recebe somente via stdin em memória: `phase` (`qa`/`pilot`), `pins`,
`ids`, `tables`, `tabs`, `products`, `qr`; no smoke piloto, `pilotPin` autorizado
substitui credenciais QA. Nunca salvar esse payload. O wrapper privado confere
SHA/deployment/flag antes e depois e invalida resultados se mudarem. A cópia
versionada do browser difere da executada somente nos caminhos locais de
Playwright/Chromium, agora relativos/configuráveis, sem mudança de cenários.

As escritas novas são disponibilidade QA reversível/versionada/idempotente e
liberação Guest apenas QA; a contenção bloqueia Guest novamente. A prova de quatro
streams usa disponibilidade Product, restaura o estado em finally e então chama
`live-stage-executor.py` injetado no campo `containment_script`, sempre em memória.
Recebe também `sha`, `run` do perfil existente, `products`, `tables`, `ids`, `pins`.
Exige runtime com flagfalse e source esperado. O chamador deve sempre repetir
contenção externamente, inclusive se o executor ou SSH falhar; restore operacional
é proibido. Nenhuma credencial/QR aparece em output. Recibos JSON são comparados
por conteúdo, sem depender da ordem das chaves jsonb.


`gate3-window-20261015.json` substitui o estado NOT_RUN do preflight para a
execução técnica real: canary87PASS, observação15min, rollback/SSE/contenção e
piloto final. Gate3 global segue BLOCKED_SIGNOFF até aceite operacional explícito.
O backup atual95tabelas substitui o arquivo90 para essa intervenção. Os arquivos
preflight preservam o estado histórico de sua captura, sem reclassificar passado.
