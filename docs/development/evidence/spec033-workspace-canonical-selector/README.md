# Spec 033 — seleção canônica na regressão do workspace

Base `0f37fb03`, branch `test/033-workspace-canonical-selector`. Ajuste somente
no teste `apps/web/tests/integration/attendance-ux2-workspace.spec.ts`.
A fixture PostgreSQL agora devolve a UUID da Tab criada; abertura inicial e
após reload usam `button[data-tab-id]`. O seletor anterior dependia da ordem
textual legada `nome · Comanda` na linha visual. Não se altera o produto ou
seus contratos para acomodar o teste. Busca delimitada não identificou outro
seletor com essa expressão legada nos testes de integração.

Spec: `specs/033-attendance-ux2-productization/acceptance.md`, contrato da
branch de especificação. Evidência parcial de AC-04/05/15/20, sem aceite global.

## Validação executada em 18/10/2026

- `npm ci`, `npm run build`, `npm run typecheck` e ESLint do arquivo: PASS.
- PostgreSQL 17.6 novo e exclusivo, loopback 55646, banco `rodada_web_e2e`,
  usuário de teste `rodada`; verificados banco/usuário e zero outras conexões.
- API real 8146 e Web real 3146; sem tocar PG55634/API8134/Web3134 ou o WT do
  integrador que executava a regressão ampla.
- `npm run test:integration -- '/attendance-ux2-workspace.spec.ts$'
  --output=test-results/workspace-selectors`: **6/6 PASS, 59,6 s**, sem retries.
- 360/390/430/1280 preservam OrderID, estações Bar/Cozinha, duas linhas,
  exposição 1500, zero pagamentos e confirmação persistente após reload.
- ACK perdido preserva exatamente UUID/payload no replay e um Order canônico.
- Limpeza exige DIRTY→CLEANING→AVAILABLE, timestamps ordenados e autores reais.

Logs adjacentes registram os comandos e resultados. Não houve alteração de
assertions financeiras ou de recuperação, timeout ou retry. A regressão
completa de 143 cenários e o aceite visual global continuam com o integrador;
este teste isolado não comprova ambos. Revisão independente registrada abaixo. Sem merge/deploy.


## Revisão independente

Em 18/10/2026, contexto integrador `/root` revisou o diff de `71eb83bf`
contra `0f37fb03` e os logs executados. Resultado: **NO_FINDINGS_WITH_GAPS**.
Confirmou UUID canônica da fixture na abertura/reload e preservação de todas
as assertions financeiras e de ACK. Classificação R3 pelo contrato de teste
de recuperação/financeiro; nenhum código novo de produto. A regressão ampla
ainda estava ativa e não foi aceita com base neste resultado. Esta revisão
é técnica e independente do autor, sem representar aprovação de GitHub,
aceite operacional ou autorização para merge/deploy.
