# Matriz de paridade UX2

Contrato: PR212 `ec26e26b164692b1e22e0fc1b7c7c45d401a7ca0`.
Capturas locais ignoradas: `apps/web/visual-artifacts/033/reference/`.
Referência estática não prova integração. Resultados ficam PENDING até comparação
com jornada real e revisão no mesmo SHA. Capturas desktop excluem o texto lateral
de laboratório da superfície operacional: requer aprovação antes de aceite de diferença.

| Tela/estado | Protótipo | Web | Android | Diferenças atuais | Resultado |
|---|---|---|---|---|---|
| Agora/Atendimentos | now-service | Shell #221; conexão de ações contextuais em correção | Shell e readback exato; matriz nativa em execução | Integração/retorno e revisão de pixels completos | PENDING |
| Agora/Entregas | alternância nowMode | Fila separada #221; projeções #218/#222/#226 | Fila tipada; ownership depende #226 | Jornada READY/entrega e pares mesmos estados | PENDING |
| Mesas | tables | Página/tiles em #224 | Grade legada; novo recorte em implementação | Paridade Compose e regressões antigas | PENDING |
| Mesa multi-Tab | table-multi-tab | Contexto de página #224 | Diálogo legado; alvo canônico implementado | Layout Compose e Back | PENDING |
| Comanda | tab | Página/CTA/barra em #224 | Página fiel em implementação | Mesma jornada Web/Compose e fonte ampliada | PENDING |
| Cardápio/rascunho | catalog-draft | Lista/quantidade/envio direto #224 | Recorte nativo em implementação, motor reutilizado | Pixels/rascunho/foco/fontes por plataforma | PENDING |
| Resumo opcional | review | Página opcional #224; testes reais quatro larguras | Página nativa implementada; validação de paridade em execução | Paridade e regressão completa | PENDING |
| Pedido confirmado | order-confirmed | #219/#224: ID/estação/estado reais persistentes | Nova apresentação usa snapshot histórico; prova nativa real em execução | Evidência nativa pareada e reinício | PENDING |
| Mais uma rodada | repeat | Página #224 com zero para excluir e envio único | Editor existente; adaptação visual em curso | Paridade nativa e rascunho prévio | PENDING |
| Envio incerto/recovery | cenário lostACK | #224: POST commit/ACK perdido/reload/payload igual em PG | Stores026/029 reutilizados; piloto de recuperação pendente | Restart/forçar parada e matriz de falhas conjunta | PENDING |
| Conta/parcial/encerrar | jornadas settlement | #225: página manual CASH, recovery Payment/Close e readback | Pagamentos existentes; página fiel ainda pendente | Caixa canônico, métodos não homologados indisponíveis; diferenças sem aprovação | PENDING |
| Limite/perfil | creditbar compact | #224: compacto/expandido e projeção; nove testes em página real | Parser corrigido e barra nativa implementada; runtime/paridade pendentes | ENFORCE atual até031; paridade Compose | PENDING |
| Liberação/limpeza | table release | #225: DIRTY→CLEANING→AVAILABLE; PG com atores/horários | Operações existentes; jornada visual conjunta pendente | Release/Guest e limpeza nativa no mesmo ensaio | PENDING |

Capturas de pagamento pareadas e versionadas em
[PR225 — evidências](https://github.com/procopio420/rodada/tree/impl/033-web-account/docs/development/evidence/spec033-payment).
Protótipo ec26e26b e Web05f5c25a, saldo2400,360/390/430/1280, fonte1x.
Manifest registra hashes e diferenças; são paridade parcial, não aceite visual.
Referências iniciais ignoradas acima são históricas e não substituem esse pacote.

Revisões financeiras independentes: código anterior e correção de fechamento
concorrente receberam NO_FINDINGS_WITH_GAPS, sem aprovação GitHub/piloto. Testes
adicionais reais Attendance cobrem selected=null/reload, storage da faseconfirmed,
Close503/ACK perdido e keepOpen após consumo concorrente/callback indisponível.
Suítes ainda não comprovam todos os aceites, estados e plataformas.

Diferenças exigidas por dados reais em avaliação: referência SIM substituída pelo
Order.id real; estação de OrderItem snapshot, jamais categoria; modo ENFORCE
atual, sem toggle WARN_ONLY antes031; dinheiro/terminal externo apenas após
recebimento observado, nenhum Pix/cartão fictício; sem rota/mapa otimizado fora033.
Nenhum épico concluído e nenhuma diferença intencional aprovada por esta matriz.

## Continuação de integração — 2026-10-17

E01-03/04/05, E02-03/04/05, E03-03/05, E06-02/03/06 continuam parciais.

- Web shell PR221 `c5fe85ab`: origem vinculada à Tab canônica e limpa após falha.
  Revisão independente encontrou P2 e verificou a correção. Teste real negativo
  A409→B manual passou, sem writes e task OPEN. Rodada dirigida 12 PASS cobre
  pedidos perdidos/refresh, rascunhos 360/390/430, reversão e jornada Attendance;
  cinco casos Agora existentes também PASS. CI e composição PR224 em andamento.
- Android contexto `5aa858fc` (produto `b3a5c98c`): 430dp/fonte2 passou com clique
  real, revogação, fallback Conta e Back/manual sem origem. Labels sem overflow
  e ações ≥48dp. Cinco outras combinações passaram em produto anterior
  `9b15ba7c`; não foram repetidas após ajuste de layout. Manifest versionado
  na branch fix/033-android-task-origin. Revisão root sem findings no recorte.
- Páginas nativas `20e86b4f`: revisão independente encontrou recuperação inerte
  de rodada incerta com carrinho vazio e perda de filtros ao visitar Conta.
  Correções relidas: reconciliação original e holder interno, sem novos
  findings estáticos. Execução real de perda de ACK e matriz ainda pendentes.
- PR226 `eb3c634d`: CI API/Web SUCCESS; projeção readonly de claim para entregas.
- PR225 `ba5cadc6`: tipagem das fixtures financeiras corrige findings novos de
  lint do CI. Não altera motor financeiro; novo CI ainda pendente.

Estas evidências não aceitam um épico completo. PRs permanecem abertas; sem
merge/deploy. Aparelho físico, TalkBack, paridade integral, reinício completo e
piloto seguem gates. Findings novos são corrigidos antes de fechar cada slice.

### Evidência adicional — composição real e páginas nativas

- PR224 `e0b15b1b`: três recuperações staff reais360/390/430 PASS, incluindo
  retorno pelo POS em390; mesmo payload/Order/ledger e envelope limpo.
- PR225 `ca7a7817`: composição relida por revisor independente R3 sem novos
  findings; três testes financeiros reais PASS24,1s. Regressão ampla pendente.
- PR229 `16bcd521` / produto `fa1a859f`: novo ensaio real lostACK da rodada
  vazia PASS14,525s. Assertions automáticas conferem Tab/UUID/OrderID/hash em
  eventos e replay; notice Enviando antigo suprimido no pending, R2/R3 relidos.
  102JVM/build/lint PASS. Seis casos Compose em cada combinação360/390/430 e
  fonte1/2 PASS; esta matriz usa fixture e não prova backend nas seis combinações.
- PR227/228/229 são drafts encadeados, sem merge/deploy. E04 nativo agora em
  implementação independente: pagamentos/limpeza existentes reutilizados, nova
  sequência persistida Payment→Close e páginas aprovadas ainda sem aceite real.

Evidência versionada em PR229: docs/development/evidence/spec033-native-repeat/
final-assertions. MainActivity/reinício, dispositivo, TalkBack, comparações
pareadas de todas telas, regressão ampla e piloto continuam gates. Nenhum
checkbox de épico/AC foi fechado por essa evidência parcial.

### Correções após comparação pareada — PR232/233

| Tela/estado | Protótipo | Web | Android | Diferenças / resultado |
|---|---|---|---|---|
| Catálogo/resumo | PR212 ec26e26b, Marina56/limite200/rascunho14 | PR232 produto47592a1d: dimensões, duas colunas, destino fixo, sem aviso redundante; capturas360/390/430/1280 | Correções e recaptura em curso, não aceitas | Web9/9Playwright +4/4recaptura; fixture controlada, não E2E real |
| Recebimento | Marina/Mesa08/saldo24 | PR232 caixa único após CTA, meios reais indisponíveis desabilitados, múltiplos preservam seleção | PR233 produto8991c2ba, HEAD1fed3a5c | Paridade integral e shell nativo ainda não provados |
| Recuperação financeira nativa | Simulação substituída por contratos reais | Evidência financeira PR225 anterior permanece por seu SHA | PR233116JVM/build/lint e3/3instrumentados Django/PostgreSQL reais | R3final NO_FINDINGS_WITH_GAPS: UUID, fenceA→B→A, durabilidade e readback; sem force-stop/UIoperator/PSP/aparelho |

PR232: https://github.com/procopio420/rodada/pull/232
PR233: https://github.com/procopio420/rodada/pull/233
Comparador antes/depois e hashes: PR232
`docs/development/evidence/spec033-parity-comparison/after-web/`.
CI das PRs ainda não encerrado na atualização deste registro. Fonte2 Web,
múltiplos/caixa revogado visuais, shell Android completo, dispositivo físico,
PSP, piloto e aceite integral continuam pendentes. Nenhum AC global foi marcado
concluído por esse recorte. PR233 depende da pilha nativa227/228/229; PR232 da
pilha Web224/225/230/231. Não há merge/deploy autorizado.

Atualização adicional: PR2348f539af1 (fontea7298ee2) corrige páginas
Compose com116JVM/build/lint e24/24instrumentados,18PNGs matched, três
larguras×duasfontes. P2 de edição note-only corrigido e teste incluído.
Fixtures continuam sem shell/API, não aceitam paridade integral. PR233CI
AndroidPASS; forced-stop-recovery SKIPPED, portanto gate não satisfeito.
PR232HEAD75ffdaac (fonted8b7e92a): composição224/225/230 reconciliada,
17/17visuais e8/8financeiros reais PostgreSQL passaram após buildestável;
falhas anteriores preservadas, CIamplo ainda pendente. Comparadores antes/
depois em after-web/index.html e after-android/index.html no pacotePR232.

### Jornada canônica compartilhada e gaps comprovados

PR238 (produto98a641ec, teste7caa33e5): WebcontraDjango18132/PG55501,
mesmo tenant isolado/IDs do ensaio nativo, Marina56/200 eRafael14/Mesa08.
4/4jornadas360/390/430/1280,24capturas, semHTTPmock e zero escritas de
domínio assertadas. Corrigida apresentação MesaMesa08, sem alterarIDs.
Build/typecheck/ESLint/3identityPASS, revisão independente sem findings
bloqueantes após esperarMesa08antescaptura. Evidência não prova liquidação,
envio,Guest ou paridadepixel. CapturaMesa revelou layoutlegadoWeb; nova
slice proprietária deve corrigir, não aceitar paridade com testesnavegação.

PR235 produto2af3b32d: caixa explícito removido exige nova seleção; intenção
pendente recupera mesmo envelope/UUID/caixa original.17adjacentes+2dirigidos
PASS e3financeiros reaisPGPASS25s; R3sem findingscomgapsCashShiftconcorrente.
CIamploWebfalhou/timeout e focused027temseletoreslegados; migração emcurso.

PR236 produto5658d686: harnessforce-stop exigia3testesquandohá4 e chamava
métodoinexistente. Corrigidos parser/targetcomtesteproduçãolabel;4PythonPASS
e revisão root. CIunit/build/lintPASS, mas jobforce-stopéSKIPPEDnasPRs.
Ensaioexplícitoanterior passou fasesforcestop e falhounoharness; gatecorrigido
com emulador ainda pendente, não considerar aceito. Nativefullshell emcurso.

### Páginas Mesa e navegação real — PR239/240/241

PR239633aa3c9 migrafocused027:10/10PASS25,7s, build/typecheck/ESLint;
UUID/payload/unknownnavigationguards preservados e revisão rootsemfindings
bloqueantes. PR240 produto115deffa+14191b08, HEADb8093b81: páginaMesa
flatrows/saldosreadback apenasMesaescolhida/saída/novaTabcontextual.
4/4jornadascanônicasPASS16,1s e24capturas;3dirigidoslimpeza/READYstale/
ClosedreadPASS;2/2followupPASS5,8srevalidaREADYchegandoeocupação
substituída com diálogojáaberto. R3findingREADYcorrigido; releasecontinua
backendcanônico. Menulegadocompatíveladicionalnãoestáimplicitamenteaprovado.

PR24149c175d3 (produtobebcd273): AndroidMesa/Comanda fullpages sobshell,
117JVM/build/lintPASS,12ComposePASS31,462s,3jornadasMainActivityreais
360/390/430PASS(21,228s/23,801s/23,723s)com18capturas. MesmoTenant/
IDsMarina56/200/Rafael14dasjornadasWeb. FindingR3: parserTABdescartava
localizaçãocanônicaqueguardREADYprecisava; preservadocontexto opcional
validadoUUID/ocupação/generation, helpercurrentTable, testesbackendshape.
RevisãorootsemnovoP0/P1apósfix; nãoaceitarREADYmockcomomutaçãoAPIreal.

CIamploaindapendente. Gate236force-stopcorrigidoemexecuçãoseparada;
fonte2shell/TalkBack/aparelho/PSP/piloto/paridadeintegralcontinuamgates.
NenhumépicoouACglobalencerrado, semmerge/deploy.
