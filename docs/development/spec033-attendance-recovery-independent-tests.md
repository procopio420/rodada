# E04 — testes de recuperação independentes

Autor dos testes: agente `review_e04_final`, em contexto separado do autor do
motor financeiro. Base de produto examinada: `3fc2ac55e38b09b1f6b61887f7c05ca20e02b545`.
Branch de autoria: `test/033-attendance-recovery`; worktree própria, sem alterações
em componentes de produto. Contrato: `specs/033-attendance-ux2-productization/web-workspace.md`.

A revisão R3 anterior foi somente leitura. Esta etapa é autoria de testes e não
constitui revisão independente destes próprios testes nem aprovação do GitHub.
Não autoriza merge, deploy, produção ou aceite de paridade visual.

`attendance-settlement-recovery.spec.ts` usa a página `/attendance` real sem
seleção inicial de Tab, BFF real, Django e PostgreSQL. Injeta apenas falhas de
transporte/armazenamento para validar:

- Payment Pending com ACK perdido, payload original no replay após reload,
  Close 503 e Close com ACK perdido após commit, seguido de recuperação sem
  novo Payment/Close quando a Tab canônica já está fechada.
- Payment Confirmed com consumo concorrente, decisão explícita de manter aberta,
  callback canônico 503 após essa decisão e retomada após reload sem mutações.
- Recusa do armazenamento ao gravar Payment Confirmed: envelope Pending original
  preservado, replay idêntico após reload e um único Payment canônico.

Execução em 2026-10-17: `npm ci --ignore-scripts` em node_modules próprio;
`npm run build` PASS; `npm run typecheck` PASS;
`npm run test:integration -- attendance-settlement-recovery.spec.ts`: **3/3 PASS,
24,9 s**, PostgreSQL 17.6 dedicado em `127.0.0.1:55637`, banco `rodada_web_e2e`,
usuário `rodada033`, API 8137, Web 3137. Python em venv própria com dependências
do pyproject. A primeira tentativa de iniciar com Python global foi interrompida
antes dos testes por ausência de cryptography; não é resultado de produto.

Antes e depois: guard estrito de host/porta/nome/usuário e ausência de conexões
client backend concorrentes, seguido de flush do banco descartável. Não acessou
55634. Playwright encerrou seus servidores. Nenhum dado real utilizado.

Limites: suíte completa/CI, paridade visual e tenant negativos adicionais não
executados nesta etapa; testes validam um único Payment no readback, sem nova
asserção própria de movimentos do caixa (a suíte pos-cash-receipt cobre ledger).
