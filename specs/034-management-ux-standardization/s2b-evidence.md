# S2b — produção e entregas

2026-10-20. Branch codex/management-ux-alerts, HEAD base860b25d93da486d2416c6ddaccfdccd9605f8953, working tree sem commit. Spec034/S2b e Spec007. RiscoR2: apresentação operacional sem mudança de comando, autorização, dinheiro, cache ou carregamento. Revisão do diff pelo autor; sem nova revisão independente desta slice.

## Implementação

Região nomeada, contadores agrupados, lista semântica de entregas expansível por teclado, destino/produto/idade preservados. Atalhos44px para Bar/Cozinha; mensagem de vazio refere último estado consultado. Nenhuma mudança em Salão, endpoints, cálculos, condições ou handlers. Mesmos dados em antes/depois;8entregas de fixture, nomes longos, sem destino, idades30/180s. Nenhuma escrita real.

## Evidência executada

- Baseline4PASS em360/390/430/1280 antes de editar produto.
- BuildwebpackPASS; typecheckPASS; ESLint página e testePASS; diffcheckPASS.
- pnpm run test:visual management-operation-layout.spec.ts management-now-layout.spec.ts management-navigation.spec.ts:26PASS/1FAIL. Falha do teste novo pressupunha ausência de snapshot após reload, mas cache preservado é contrato existente. Teste corrigido para conferir aviso e snapshot, e depois limpar somente sessionStorage da fixture isolada para exercitar primeira leitura.
- Repetição intermediária4PASS/1FAIL por texto incorreto do aviso no teste; ajustado ao texto existente, sem mudança no produto.
- Repetição final management-operation-layout.spec.ts:5PASS10.1s.22regressões de navegação/Agora anteriores passaram no mesmo código de produto; produto não mudou após elas.27casos distintos aprovados, executados em rodadas separadas.
- Axe/overflow, teclado, alvos/destinos, nenhuma escrita, estado vazio,403com cache e403inicial, CSSzoom2 local da região. Capturas390/1280 e360CSSzoom examinadas.12PNG+SHA256SUMS e3fontes+SOURCE-SHA256SUMS em docs/development/evidence/spec034-operation.

## Limites

CSSzoom local não comprova zoom nativo do navegador nem leitor de tela. Aceite humano, dispositivo e integração realNOT_RUN. Gate visual global continuaFAIL conforme rodada compostaS1; não repetido por este recorte. GatesR3 anteriores seguemREVIEW_BLOCKED. GO inspeção local; NO-GO merge/release/piloto. Sem commit/push/merge/deploy. Preservar trabalho anteriorS1 eS2a. Próximo: S2cSalão/itens indisponíveis; ler contrato antes de editar. Preview3001 reiniciado sessão79596; acesso autenticado depende de login staff.
