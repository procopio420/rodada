# Matriz de paridade UX2

Contrato: PR212 `ec26e26b164692b1e22e0fc1b7c7c45d401a7ca0`.
Capturas locais ignoradas: `apps/web/visual-artifacts/033/reference/`.
Referência estática não prova integração. Resultados ficam PENDING até comparação
com jornada real e revisão no mesmo SHA. Capturas desktop excluem o texto lateral
de laboratório da superfície operacional: requer aprovação antes de aceite de diferença.

| Tela/estado | Protótipo | Web | Android | Diferenças atuais | Resultado |
|---|---|---|---|---|---|
| Agora/Atendimentos | now-service | #221: origem canônica e retorno; integração negativa A409→B | #228/#241: leitura exata e contexto nativo | Matriz conjunta de estados e reconexão ainda parcial | PENDING |
| Agora/Entregas | alternância nowMode + viewDelivery | Fila #221; página real #246, fonte cca4e61a e capturas pareadas | Página nativa em validação; recuperação sob correção independente | Aceite de recuperação/reinício, paridade final e isolamento de falha da fila pendentes | PENDING |
| Mesas | tables | #240: grade e página Mesa; quatro jornadas canônicas | #241: shell real, três larguras e 18 capturas | Fontes ampliadas no shell completo e matriz final conjunta | PENDING |
| Mesa multi-Tab | table-multi-tab | #240: linhas, saldos canônicos e abertura contextual | #241: página nativa e IDs de ocupação preservados | Fluxos completos de giro/READY nas duas plataformas | PENDING |
| Comanda | tab | #224/#232: página e ajustes pareados | #229/#234/#241: página, ajustes e shell real | Estados adicionais e comparação final no conjunto integrado | PENDING |
| Cardápio/rascunho | catalog-draft | #224/#232: envio direto e draft; #238: dados reais compartilhados | #229/#234: fluxo e matriz Compose; #241: shell real | Recuperação operacional após processo encerrado ainda precisa aceite completo | PENDING |
| Resumo opcional | review | #224/#232: página, identidade e controles ajustados | #229/#234: resumo nativo e matriz visual | Revisão conjunta de todos os estados e fontes ampliadas | PENDING |
| Pedido confirmado | order-confirmed | #219/#224: ID, estação e estado reais persistentes | #229: snapshot canônico; matrizes #234/#241 | Reinício real e matriz de falhas integrada | PENDING |
| Mais uma rodada | repeat | #224: seleção, quantidades e envio único | #229/#234: editor nativo e apresentação ajustada | Regressão completa e coexistência com rascunhos | PENDING |
| Envio incerto/recovery | cenário lostACK | #224: commit/ACK perdido/reload/payload igual; #245 corrige apenas seletor de navegação | Stores 026/029; #236 prova persistência sintética após force-stop | Force-stop sintético não comprova POST/ledger real | PENDING |
| Conta/parcial/encerrar | jornadas settlement | #225/#230/#232/#235: CASH, Close recuperável, zero direto e contexto de caixa | #233: conta/parcial/Close reais; #234: ajustes visuais | PSP, dispositivo físico e matriz final; diferenças sem aprovação global | PENDING |
| Limite/perfil | creditbar compact | #224/#232: compacto/expandido e projeção | #229/#234/#241: barra e capturas reais | WARN_ONLY depende 031; preservar ENFORCE canônico | PENDING |
| Liberação/limpeza | table release | #240/#243: dois estágios e contrato obrigatório, corrida real A→B | #241/#244: target imutável e teste API real A→B | Guest/limpeza/READY e giro completo no mesmo ensaio conjunto | PENDING |

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

### Diretriz do responsável — produto ainda não lançado

Compatibilidade legada deixou de ser requisito por orientação explícita do
usuário em18/10. Não preservar fallback de liberação sem identidade. PR242
a4164856 (contratoebd22333) exigeexpected_occupancy_id+expected_generation
noPOST/serviço. Omissão/parincompleto400; ocupação substituída409STALE_OCCUPANCY
soblocksTable→Occupancyanteswrites;54/54PostgreSQLPASS78,28s, R3root.
ClientWeb914095f7+aba5733bprova2/2DjangoPGPASS15,5s: happyDIRTY e
raceA→Breal409comBintacta. AdoçãoAndroidemexecução, mergegatednosdois.
Isso não modifica políticas de pagamento/ledger/permissões.

HarnessPR23627f2631e corrigidolayoutlabelNovaComanda(font1,5)enãoapenas
contagens: fullscriptEXIT0[1,1,1,4,3,1,1,1],116JVM/build/lint/compilePASS
e3fitsstandalonePASS. Force-stopprovaapenaspersistênciasintética, nãoPOST
financeiroreal. Falhasanterioresretidas;R2rootreviewsemfindingsbloqueantes.

### Adoção obrigatória concluída nos recortes Web/Android

PR243af223739 (Web914095f7/testsaba5733b/3f94a059):
3/3visualPASS10,5s;2/2DjangoPGPASS15,5s(happyrelease e corridaA→B
comPOSToriginalA409eBintacta);5/5PASS38,8sincluiGuestrevogado,
chamadosQRecontadorcanônicodegiro. R3independente semfindingsnoescopo.
PR244db62c7f9 (produto90b0290c,testb313edc2):119JVM/build/lintPASS,
5/5instrumentados11,588s(4Compose+1APIreal18134/PG55501), targetA
409preservaB, confirmaçãoexplícitaBhappyDIRTY. R3rootsemnovosfindings;
manifest/logs/priorfalhasversionados. Dependências241/242deintegração.

Nãoreintroduziromissãodecamposporcompatibilidade. Backend242+clientes
243/244devemintegrarjuntos, semmerge/deployautorizados. SUITEWeb143
emexecuçãoparaHEADcomposto, nãorepresentadapelosrecortesacima.
ParidadeentregasWeb/Androidépróximoslicereal, ACglobaisaindaabertos.


### Continuação de validação — 18/10, rodada de entregas

A matriz inicial acima foi atualizada para remover descrições de implementação
que já estavam superadas; todos os resultados globais continuam PENDING.
PR245 `36f3444f` (teste `71eb83bf`) seleciona a Tab por UUID da fixture em
vez da ordem textual antiga da linha. Seis cenários reais PostgreSQL passam,
sem alterar assertions de pedido, exposição, pagamento ou payload de recuperação;
revisão independente root: NO_FINDINGS_WITH_GAPS. Base PR243.

A regressão ampla de 143 testes no HEAD imutável `0f37fb03` permanece em
execução. As quatro falhas de navegação identificadas usam o seletor corrigido
pela PR245; a execução original deve terminar e sua evidência deve ser preservada.
O recorte dirigido verde não substitui a futura execução ampla no HEAD corrigido.

Web entrega: PR246 `ffa959b6`, fonte `cca4e61a`, nove testes browser PASS;
quatro jornadas PostgreSQL reais confirmam Tab CLOSED com entrega READY,
abertura/Back sem mutação e perda de ACK reconciliada em DONE/DELIVERED
com um POST e pagamentos inalterados. Não é aceite global ou aprovação de
alterações intencionais do texto de simulação. Android: página nativa em
validação; auditoria independente identificou lacunas preexistentes no motor
completeDelivery (resposta tardia após troca de sessão e ausência de terminal
readback na recuperação). Correções em slice separada, ainda sem aceite.
Falha da fila de entregas também não deve bloquear pedidos disponíveis:
separação de freshness Web registrada como próximo delta E03-07.


### Estado posterior verificável — 18/10, composição de entregas

Esta atualização substitui os estados “em execução” anteriores apenas nos recortes abaixo;
os registros anteriores permanecem históricos. Nenhum épico ou AC global foi encerrado.

| Tela/estado | Protótipo | Web | Android | Diferenças e resultado |
|---|---|---|---|---|
| Detalhe de entrega | PR212, página completa | PR246 `ffa959b6`: nove browser + quatro jornadas PostgreSQL PASS | PR250 `3a77d0a5`: 36 Compose/font1 e2, 120 JVM | Página completa e comparação versionadas; aceite global pendente |
| Fila indisponível | Fluxos operacionais separados | PR248 `5b9e7f97`: 18 browser + quatro jornadas PostgreSQL PASS | Slice própria em execução | Pedir continua disponível quando apenas Dispatch falha; liberação bloqueada enquanto fila desconhecida |
| ACK perdido e reinício em entrega | Recuperação segura | Readback real sem repetir POST coberto na PR246; processo Web ainda pendente | PR251 `24096637`: readback DONE/DELIVERED e force-stop real PASS | Mesmo task/item/intent, um POST; sessão revogada e A→B→A real pendentes |
| Navegação em regressão ampla | Contexto e retorno aprovados | PR249 `87306a67`: cenários migrados para navegação atual | Não aplicável a esse teste Web | Regressores de seleção usam UUID; sem relaxar assertions de domínio |

PR250 executou **120 JVM**, 36 verificações
Compose e uma jornada MainActivity/API real somente leitura. Os **128 JVM**
pertencem à composição de recuperação PR251, não à página isolada. A prova real
de página usa fixture própria e não comprova recebimento/pagamento.

A execução ampla Web em `05666768` terminou com **146 PASS, duas falhas e três
skips**, em 21,9 minutos. Traces das duas falhas em rascunhos demonstram expiração
do orçamento total de 30s, interrompendo a expectativa final após 175/258ms;
não demonstram falha no prazo local de 5s. Revisão independente recomendou
90s apenas para a jornada de três Tabs, mantendo expectativas locais e zero
retries. Nova execução de 151 testes em `87306a67` está em andamento; ainda
não é evidência verde. Os três skips são o menu CSV opt-in, cuja migração e
execução real acontecem em worktree/PG próprios, sem dispensar esse gate.

PR251 inclui revisão independente R3: reconciliação sem achados reproduzíveis;
P2 do harness (aceitar assumption skip/config reservado) corrigido em `b8267334`,
reavaliado e repetido no emulador com códigos reais de sucesso. Dez regressões
Python PASS. Aprovação GitHub qualificada e gates de integração continuam abertos.
Spec031 não integrada: preservar enforcement canônico; WARN_ONLY não simulado.
Sem merge/deploy e sem aceite de diferenças intencionais por inferência.
