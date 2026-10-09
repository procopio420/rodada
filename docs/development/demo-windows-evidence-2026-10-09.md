# Demo Windows integrada — 09/10/2026

**GO CONDICIONAL: demo local supervisionada com MANUAL_TEST.** Sem produção, provider real, aparelho físico ou papel certificado.

## Base e preservação

Código validado a partir da main 7227f7d, com os pequenos recortes deste PR. Durante a execução, Lucas publicou 23babc6, exclusivamente docs/development/spec-maturity-matrix-2026-10-09.md; rebase preservou esse documento sem mudanças no código testado. Commit de implementação/reprodução c94ada58199984f1871bb11ebee7d891e47df758; fechamento posterior é documental. Branch codex/demo-functional isolada; original codex/ux-operational-polish 6e2f4ca preservada. Sem merge/force push. Consulta inicial não encontrou PRs abertos.

A demo SQLite antiga nas portas3000/8000 permanece em execução com seu banco/histórico. Nova stack independente: PostgreSQL17.11 portátil Windows, ASGI uvicorn0.54, dispatcher separado, Web produção Next16.3.8; Python3.12.14/Django5.2.18/psycopg3.3.6. Emulador API36, compileSDK37; 43 unitários Android. Docker/WSL ausentes, por isso reprodução nativa documentada em [demo/WINDOWS.md](../../demo/WINDOWS.md). Sem instalação de serviço global.

## Mudanças pequenas

- Preview de pricing fica desabilitado enquanto a leitura canônica não chegou. A falha foi reproduzida no browser real: clique anterior à resposta não fazia nada. Teste de resposta retida comprova disabled → enabled. Sem alterar API/versão/PIN/limites.
- Golden de recibos lê UTF-8 explicitamente: 20 casos falhavam com encoding padrão Windows. Nenhum arquivo golden/referência substituído; texto/HTML/ESC-POS mantêm igualdade literal.
- Teste de revogação conserva o acesso anterior somente em memória antes de liberar mesa. SSE pode limpar sessionStorage antes da requisição; 403/GUEST_SESSION_REVOKED continuam exigidos exatamente. Não se aceita 401 como substituição.
- Launcher e runbook reutilizam serviços, seed e contratos existentes; portas55459/18764/3119, estado persistente fora do Git, recusando portas ocupadas. Senha configurada localmente, não fixa no novo script.

## Evidências por etapa

| Etapa | Resultado atual |
| --- | --- |
| Login, permissões e cross-Venue | PASS; integração browser/API PostgreSQL e turno HTTP; Android login real |
| Abrir comanda / identidade opcional | PASS via browser/Android e roteiro HTTP |
| Pedidos Bar/Cozinha, disponibilidade, variantes/modificadores | PASS suites reais; pedido Android simples nas duas estações; adicional indisponível rejeitado no seletor |
| Aceitar/preparar/pronto | PASS browser sobre pedidos browser e Android |
| Entrega Android | PASS emulador: duas linhas READY → ações existentes → 0 PRONTOS; não dispositivo físico |
| Parcial/restante/fechamento | PASS UI + HTTP manual/test; saldo zero |
| Caixa/Gerência/relatórios | PASS turno com assertions e SQL independente; browser abriu superfícies adjacentes |
| Desconto/serviço/recibo | PASS integração browser9 e cenário da demo: 1800−100+170=1870 recebidos, exposição0; prévia digital não fiscal |
| Exceção/retry/replay | PASS roteiro HTTP e testes; limite/disponibilidade, pagamento/pedido idempotentes, SSE replay |
| Restart | PASS DB/API/dispatcher/Web com mesmos IDs e report após restart; sem apagar história |
| Repetição | PASS dois turnos completos, mantendo histórico; run_ids477d39ed1f/b2fe3baf69 |

O script HTTP registra native_android_ui=NOT_RUN corretamente. A prova Android é separada em [native-result.json](demo-windows-artifacts-2026-10-09/native-result.json) e screenshots. Na tela Android observada o transporte foi ONLINE via consulta/polling; não atribuir ao SSE nativo o resultado. SSE real/replay foi verificado pelo runner HTTP na API ASGI.

## Gates executados

- API PostgreSQL final: **363 passed**, sem skips, 613.56s; banco de teste separado.
- Web typecheck/build: PASS. Realtime: **8 passed**.
- Browser integração PostgreSQL: **9 passed**, incluindo pricing, receipts/PDF e revogação.
- Visual completo final: **173 passed**, incluindo teste novo; referências/thresholds intactos. Superfície adjacente de recibos também verificada.
- Android: **43 unitários**, zero erros/falhas; assembleDebug/lintDebug PASS. Jornada em emulador contra API real adicional.
- System check e migration drift: PASS; grafo aplicado em PostgreSQL vazio.

Tentativas anteriores ficam explícitas: a primeira suíte API foi invalidada porque o executor reiniciou a instância enquanto testes em outro banco ainda a usavam. Não foi contada como aceite. A segunda teve343 PASS/20 FAIL por encoding golden; a final teve363 PASS. Browser falhou inicialmente no preview; após correção apareceu a corrida do harness de revogação; suite final9 PASS. Roteiro UI teve pagamento com versão desatualizada por nova ação antes de terminar atualização; o ensaio final reconsulta a conta entre pagamentos, preservando rejeição. Tentativas/recebimentos antigos não foram apagados ou ajustados por SQL.

## Conciliação e configuração de teste

[SQL read-only final](demo-windows-artifacts-2026-10-09/reconcile-final.txt): Venue release-demo, 7 Tabs fechadas, Charges19600, Adjustments−1130, Payments19670, Refunds1200, Transfers0, Exposure0. 19600−1130−19670+1200=0. Duas CashShifts fechadas, discrepancy0; turno aberto da prova UI tem1870 em movimentos. Nenhuma violação das três verificações de duplicação. Esta fotografia não mistura a Venue bar-do-aderlan usada no ensaio browser simples, cujas tentativas permanecem identificadas.

Catálogo demonstrativo existente seed_demo_catalog foi reutilizado também em release-demo, sem editar histórico de pedidos. Browser endpoint Demo navegador criado pela UI, sem claim de papel. Serviço10% foi habilitado via configuração canônica da Venue de teste e avaliado explicitamente na comanda, sem taxa automática.

## Uso e limites

Abrir http://127.0.0.1:3119/staff; /pos, /bar, /kitchen, /cash, /manage, /reports. Acesso de teste fica na orientação local, fora dos novos documentos publicados. Estado runtime/banco, APK, traces e logs de sessão não são publicados. [Runbook](../../demo/WINDOWS.md) explica iniciar/parar/reproduzir e preservar dados.

Restam fora deste aceite: device físico/LAN/BYOD, private Tap SDK/Pix/liquidação, impressão física/fiscal, rede do bar, restore de backup e paridade visual integral. Não precisam bloquear este roteiro manual supervisionado. Para mostrar algo desses itens é necessário seu gate próprio. Native screenshot regression completa não foi ampliada neste recorte. CI remoto tem estado separado e não é inferido dos passes locais.

Publicação: branch codex/demo-functional enviada e [PR61 em rascunho](https://github.com/procopio420/rodada/pull/61) criado, sem merge. CI remoto é acompanhado separadamente dos checks locais acima.
