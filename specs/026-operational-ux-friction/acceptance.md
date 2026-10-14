# Acceptance — Spec 026

Os critérios abaixo são gates amplos; PASS de uma slice local não conclui a Spec 026.
Evidência de T01/T02 em [revalidation.md](revalidation.md).

- [ ] Cada slice identifica achados, spec proprietária e contrato antes/depois.
- [ ] Contagens medidas têm início/fim, campos, confirmações e contexto explícitos.
- [ ] Tempos e scrolls são medidos em navegação, sem inferir de screenshots.
- [ ] Estado vazio, normal e pico têm dados identificados e evidência separada.
- [ ] Android real e mobile Web 360/390/430 têm evidência própria de teclado/alcance.
- [ ] Trocar comanda preserva draft por destino ou oferece descarte explícito.
- [ ] Reselecionar resultado abre área utilizável; recolher é controle explícito.
- [ ] Repetir consumo revalida configuração/preço/disponibilidade e gera nova intenção.
- [ ] Guest ajusta quantidade mantendo separadas configurações diferentes.
- [ ] Alertas abrem registro correto com autorização e retorno contextual.
- [ ] Retry ambíguo usa o mesmo payload/chave, inclusive após retomada suportada.
- [ ] Duplo toque e perda de resposta após commit não criam segundo efeito financeiro.
- [ ] Correção após parcial oferece disposição financeira coerente e executável.
- [x] Produção da main pós-#98 revalidada localmente: início manual e Pronto; deploy/pico continuam abertos.
- [ ] Lotes, se aprovados, preservam configuração, escopo, autoria e conflitos por linha.
- [ ] Disponibilidade, passe e pedido continuam acessíveis no volume de pico.
- [ ] Contagem física não recebe esperado automaticamente; revisão preserva snapshot.
- [ ] Melhorias visuais executam gates existentes sem relaxar tolerâncias/baselines.
- [ ] Comparação antes/depois demonstra ganho sem aumento de erros ou perda de proteção.

## Aceite do recorte T02 — zero a devolver

- [x] Cenário 3800/1000/800 termina com payable 3000 e exposição 2000, sem Refund/CashMovement e sem alterar Payment/Charge originais.
- [x] Gerente ativo, capability e PIN recente são exigidos; corpo financeiro editável é rejeitado.
- [x] Revisão e reversal são transacionais; saldo que exigiria devolução e item avançado são rejeitados sem efeito.
- [x] Replay e aprovação concorrente geram um único ajuste e audit de aprovação.
- [x] Legado REFUND_REQUIRED zero pode ser revisado; estorno positivo mantém o fluxo existente.
- [x] UI em 360/390/430 oferece aprovação sem estorno e retry por mesmo ID após resposta perdida.
- [x] Jornada real Web/API/PostgreSQL confirma aprovação, Payment intacto, replay e preparo manual do outro item.

Remoção de quantidade parcial paga, produção avançada, deep link do modal,
T03b e medição em campo continuam fora deste recorte.

## T03a — UX-08 (CASH no POS)
- [x] Mesma intenção para double tap, resposta perdida após commit e reload; Payment/movimento/audit únicos.
- [x] Payload divergente de caixa/tender rejeitado, sem alteração financeira.
- [x] Sessão diferente/revogada e storage falho bloqueiam envio/adoção.
- [x] Rejeição inicial é revisável; ambiguidade permanece bloqueada até replay/readback.
- [x] Web/API/PostgreSQL, mobile360/390/430, visual completo, build/tipos e lint conferidos.

Estorno manual UX-22 entregue em T03b abaixo. Provider, persistência após fechar
aba e reconciliação entre sessões permanecem abertos.

## T03b — critérios do recorte manual

Evidências em Spec026/revalidation.md; gates externos permanecem abertos.

- [x] Mesmo Refund após duplo toque, resposta perdida, reload e readback falho.
- [x] Payload congelado; PIN recente, sessão divergente/revogada e storage falho
  não descartam nem adotam intenção ambígua. Rejeição inicial segura permite edição.
- [x] Replay divergente rejeitado; saldo/refundable, Payment/snapshots, ledger e
  auditoria preservados; concorrência produz um único efeito em PostgreSQL.
- [x] Jornada real Web/API e mobile360/390/430; visual completo, build/tipos e lint
  registrados sem declarar provider, piloto, aparelho ou deploy homologados.

## T04 — aceite do recorte local

- [x] A→B→A e nova Tab preservam linhas/configurações isoladas; confirmar limpa
  só a Tab enviada, sem transportar linhas para outra conta.
- [x] Reseleção revela o workspace; recolher explícito preserva rascunho e foco.
- [x] Descarte confirmado afeta só a Tab ativa; cancelar preserva conteúdo/foco.
- [x] Leitura falha mantém destino; durante switch/envio/ambiguidade não editar,
  trocar, recolher ou descartar; catálogo atual continua revalidando as linhas.
- [x] Jornada Web/API/PostgreSQL e360/390/430, visual completo/build/tipos/diff.

Memória apenas enquanto workspace montado. Reload e recuperação durável T05 abertas.

## T05a — aceite staff Web

- [x] Resposta perdida/reload retoma mesmo payload/chave e um Order/Charge/audit.
- [x] Readback falho e duplo toque não liberam outra confirmação.
- [x] Sessão diferente/revogada, envelope inválido/alterado e storage falho bloqueiam.
- [x] Rejeição inicial conhecida permite revisão; replay ambíguo mantém bloqueio.
- [x] Web/API/PostgreSQL, mobile360/390/430, visual completo, tipos/build e diff.

Guest, drafts após reload e fechar aba permanecem abertos.

## T05b — aceite do recorte guest

- [x] Resposta perdida/reload retoma payload/chave originais sem duplicar Order/Charge/audit.
- [x] Readback/duplo toque/contexto indisponível mantêm bloqueio até prova canônica.
- [x] Sessão/Tab/ocupação/generation divergentes e revogação/bloqueio não adotam intenção.
- [x] Storage inválido/falho impede POST; rejeição inicial segura permite revisão.
- [x] Jornada real PostgreSQL, Web360/390/430, visual/build/tipos/lint/diff registrados.

Mesma aba com storage íntegro; gates externos e persistência de drafts abertos.

### T06a — Paginação Web
- [x] Setas compactas com nomes acessíveis, foco visível e alvos de 44 px em 360/390/430 px; indicação de página e regras existentes preservadas.
- [x] Próxima/anterior página permite alcançar comandas além das primeiras 200 no PDV e Atendimento; histórico acompanha a página consultada.
- [x] Falha de navegação conserva página, seleção e rascunho; resposta anterior não sobrescreve navegação concluída.
- [x] Filtro local informa seu alcance; seleção não muda automaticamente entre páginas.

Evidência local: 37 testes API/financeiros PostgreSQL PASS; jornada Web/API com 201 Tabs em 360/390/430 PASS; 8 cenários de paginação/rascunho/erro/histórico/resposta obsoleta PASS. Suíte completa: 300 PASS e 3 falhas na fixture nova do PDV, corrigidas e reexecutadas no arquivo afetado (8 PASS). Build/tipos/Ruff/diff PASS.

### T06b
- [x] API encontra apelido além de 200 registros com normalização, paginação e isolamento de Venue; preserva homônimos e sem nome no inventário.
- [x] Busca Web nas duas superfícies reinicia página, mantém destino/rascunho e apresenta UUID de opções indistinguíveis.
- [x] Falha conserva busca aplicada/resultados; resposta antiga não substitui busca nova.
- [x] Migração preenche registros existentes e save de apelido atualiza campo derivado.

Evidência local: 39 testes PostgreSQL PASS, jornada real de 203 Tabs em 360/390/430 PASS, suíte visual completa 310 PASS (6,4 min), build/tipos/migrações/diff PASS. Ruff sem avisos novos; dez RUF012 preexistentes em modelos/views permanecem. Ver revalidation.md e testes tab-search.

### T06c
- [x] Mesa Web permite filtrar nome/número normalizado e escolher individualmente comandas vinculadas, inclusive fora da página de Contas.
- [x] Abertura direta e retorno preservam filtro, foco, destino e rascunhos; falha mantém contexto anterior e bloqueios pendentes.
- [x] GET contextual rejeita vínculo liberado/movido, ocupação liberada, mesa divergente, IDs inválidos e outro Venue; leitura não altera financeiro/histórico.

Evidência local: 70 testes PostgreSQL PASS; jornada real com 203 Tabs, confirmação única e preservação de ocupação/Payments em 360/390/430 PASS; suíte visual final **318 PASS (6,7 min)**. Build/tipos/diff PASS; Ruff sem avisos novos (15 RUF012 preexistentes nas views, teste PASS). Ver revalidation.md.

### T06d — movimento API e Web
- [x] Destino com generation divergente rejeita sem alterar versão/vínculo, ledger ou auditoria da Tab.
- [x] Movimento válido com e sem pagamento preserva snapshots de Orders/Charges/Payments e motivo na auditoria, sem liberar origem.
- [x] Replay concorrente único; disputa com liberação não deixa vínculo ativo na ocupação encerrada; replay posterior não recria vínculo e exige autorização atual.
- [x] Controle de escolha/confirmação A→B no Atendimento Web e sua recuperação/jornada mobile.
- [x] Gateway nega operações/fields financeiros; sessão divergente, storage falho e readback indisponível não substituem a intenção.
- [x] Drafts por Tab, saldo/Payments, origem ocupada e histórico preservados na jornada Web/API descartável.

Evidência atual: 58 testes API PostgreSQL PASS (122.306s), jornada real Web/API
em 360/390/430 PASS (22.4s de teste), suíte visual completa 331 PASS (7.2 min),
incluindo 13 cenários novos, e 12 testes auth/realtime PASS. Build/tipos/Ruff/
check/diff PASS. Android, aparelho e deploy não revalidados; revalidation.md
separa as evidências da correção API inicial e da continuação Web.

### T07a — carrinho Android
- [x] Revisar e voltar ao catálogo sem percorrer 146 produtos; quantidade/total visíveis e navegação sem envio.
- [x] Detalhes expansíveis sem esconder alertas ou alterar as condições Pagar/Fechar.
- [x] Edição e replay preservam bloqueios existentes; checks Android e matriz de emulador registrados separadamente de aparelho/API.

Evidência T07a: 59 unitários Android, assembleDebug/assembleDebugAndroidTest,
lintDebug (zero erros, oito avisos em arquivos não alterados), sete cenários
Compose em 360/390/430 dp × fonte 100%/150% e 35 testes financeiros PostgreSQL
PASS. Journey Android/API, teclado, aparelho, tempo humano e deploy não verificados.

### T07b — confirmação de liberação Android
- [x] Revisão nomeia mesa e revogação guest; cancelar não chama mutation.
- [x] Confirmação explícita uma vez; busy, perda de permissão ou ocupação local divergente bloqueiam.
- [x] Matriz de emulador e regressões mesas/guest/financeiras documentadas com limites.

T07b: três cenários Compose em seis configurações PASS, 59 unitários Android,
build/lint (zero erros) e 48 testes PostgreSQL PASS. Ver revalidation.md;
não comprova aparelho, jornada Android/API nem nova precondição transacional.

### T07c — destino do pedido Android
- [x] Pedir leva à escolha sem criação/envio; Nova comanda é ação separada.
- [x] Homônimos preservam IDs; vazio não cria automaticamente; loading/busy bloqueiam seleção/criação.
- [x] Navegação, matriz de emulador, build/lint/unitários e regressões financeiras documentadas com limites.

T07c: cinco cenários Compose em seis configurações, 59 unitários Android,
build/lint sem erros e 28 testes PostgreSQL PASS. Ver revalidation.md para
limites de inventário local, aparelho e jornada Android/API.

### T07d — teclado e centavos Android
- [x] Teclados decimal/PIN configurados nos campos do recorte, máscara mantida.
- [x] Ponto/vírgula convertem exatamente; negativo, letras, excesso de casas e overflow rejeitados.
- [x] Confirmação inválida bloqueada; métodos, caixa, PIN e replay preservados; checks e limites documentados.

T07d: 61 unitários Android, sete cenários Compose em seis configurações,
48 testes PostgreSQL e build/lint sem erros PASS. InputType real de pagamento
e PIN de estorno verificados no emulador; IME/aparelho físico não homologados.

### T08a — critérios antes da implementação
- [x] T08a Android local: revisão mostra valores/configuração anteriores e atuais, exclusões e bloqueios sem defaults silenciosos.
- [x] T08a Android local: cancelar não muda draft; inclusão preserva draft e bloqueia conteúdo alterado/intent pendente/busy/offline.
- [x] T08a: preço/configuração atuais e nova intenção seguem confirmação existente; unitários/Compose e regressões PostgreSQL documentados. Journey Android/API integral não homologada.

### T08b — critérios antes do código
- [x] T08b local: revisão Web usa IDs/configuração/preços atuais, mostra diferenças/exclusões e bloqueia itens inválidos sem defaults.
- [x] T08b local: cancelar/falha preservam draft; inclusão na mesma Tab preserva outras Tabs; busy/pendência/conteúdo alterado bloqueiam repetição.
- [x] T08b local: nova intenção, resposta perdida/replay e histórico financeiro verificados em Web/API PostgreSQL 360/390/430; 342 testes visuais, tipos/build PASS. Sem baseline/tolerância alterados.

### T08c — critérios antes do código
- [x] Guest revisa/copía configuração e preço atuais por IDs, sem defaults, preservando draft e intenção nova no envio.
- [x] Token/scope/Tab divergentes, bloqueio/revogação/falha/pendência impedem inclusão; nenhuma resolução de QR ou nova sessão durante repetição.
- [x] Web/API PostgreSQL 360/390/430, resposta perdida/replay sem duplicação e original preservado; 60 testes API/PostgreSQL, 359 visuais, tipos/build/Ruff PASS. Sem alteração de baseline/tolerância.

### T08d — repetição no PDV Web
- [x] Revisão por IDs/preço/configuração atuais, exclusões e bloqueios, sem defaults ou envio automático.
- [x] Cancelamento/falha preservam draft; inclusão única na mesma Tab; personalização, recebimento ambíguo, encerramento e conteúdo alterado bloqueiam repetição.
- [x] Web/API PostgreSQL 360/390/430: preço atual, nova intenção, replay sem duplicação, histórico/snapshot/Payments e draft da outra Tab preservados.
- [x] 371 testes visuais PASS (7,2 min), tipos/build e diff finais PASS; sem alteração de baseline/tolerância.

### T09a — critérios antes do código
- [x] Quantidade +/− e zero remove; toques/edição/repetição agrupam somente configuração idêntica, sem perda de unidades acima de 99.
- [x] Configuração diferente permanece distinta; bloqueios/indisponibilidade/pendência respeitados e replay mantém payload original.
- [x] Web/API PostgreSQL 360/390/430, 60 PostgreSQL, 385 visuais, tipos/build/diff PASS; histórico/ledger preservados, sem baseline/tolerância alterados.

### T09b — critérios antes do código
- [x] Categoria real projetada e busca global por nome sem acento/caixa; limpar, fallback e vazio acessíveis com 146 produtos (143 CSV + três fixtures existentes).
- [x] Filtros preservam draft/configuração/quantidade/intent; Pedido atual acessível, bloqueios/indisponibilidade/revogação preservados.
- [x] Web/API PostgreSQL 360/390/430, 61 PostgreSQL, 393 visuais, Ruff/tipos/build/diff PASS; baseline/tolerância preservados e limites documentados.

### T10a — acesso às regiões mobile
- [x] Passe/disponibilidade alcançados com um atalho em fila de 30 linhas, em ambas estações e 360/390/430.
- [x] Navegação persistente, foco na região e alvos >=44 px; retorno à fila sem alterar estados.
- [x] Contagens do snapshot e loading desconhecido; erro/mutation não liberam comandos.
- [x] Tipos/build e visual completo passam, sem relaxar tolerâncias.

### T10b — resumo por configuração
- [x] Somente snapshots operacionais equivalentes se agrupam; preços/quantidades/ordem JSON não alteram identidade.
- [x] Variação, modificadores e notas visíveis no resumo em ambas estações, 360/390/430.
- [x] Legado incompleto/IDs ausentes/routing divergente independente, com aviso, sem inferir padrão atual.
- [x] Navegação/agrupamento conserva snapshots, Payments e finanças; indisponibilidade posterior não remove preparo.
- [x] Unitários, PostgreSQL, Web/API, visual completo, tipos/build passam; referência/tolerância preservada.


### T10c.1 — API de lote (evidência local)
- [x] Lote compatível, replay imutável e rejeição integral por estado/quantidade/snapshot/configuração/Venue.
- [x] Concorrência, rollback de Dispatch, auditoria por comando e preservação financeira em PostgreSQL.
- [x] T10c.2: revisão e recuperação Web mobile entregue em slice própria; não faz parte de T10c.1.

Evidência T10c.1: 96 testes PostgreSQL PASS (108.595s), incluindo 17 testes novos
de lote, Dispatch, ordering, turno completo, customização, ledger/Payments e
concorrência financeira/correções/pedidos. Django check/migration drift, compilação
Python, tipos Web e diff PASS. Ruff dos arquivos novos PASS; os arquivos existentes
models/views/urls mantêm 12 avisos (10 RUF012/2 I001), reproduzidos em HEAD ad5d64f.
Não houve alteração de UI: visual/build Web e jornada browser/mobile não executados
nesta slice. Log: visual-artifacts/spec026/runtime/t10c-postgres-final.log.

### T10c.2 — evidência local
- [x] Seleção explícita e revisão obsoleta bloqueada; sem auto-preparo.
- [x] Envelope anterior ao envio, replay original, sessão/armazenamento/readback protegidos e resultado por linha.
- [x] Web/API PostgreSQL mobile360/390/430, tipos/build/visual completo sem relaxar baselines.

T10c.2:425 visuais completos PASS (8.9m), incluindo17 de lote, mais1 teste
de volume51/limite50 executado separadamente após discovery;6 Web/API PostgreSQL
PASS (50.1s),49 PostgreSQL PASS (66.270s),5 unitários, tipos/build/diff PASS.
Sem baseline/tolerância novos. Capturas fixture/reais360 inspecionadas;390/430
cobertas por testes. Ledger/Payments/snapshots e12 comandos/12 auditorias/24
transições/12 entregas verificados na base exclusiva de teste. Não há script
Web lint/test genérico; executados test:visual/test:integration/test:production
por CLI Node documentada. UX23/T10d, aparelho, piloto e publicação seguem abertos.

### T10d.1 — evidência local
- [x] Itens verificados distintos avançam independentemente; mesmo item/lote/legado protegidos.
- [x] Intenções persistidas sobrevivem mudança de estado/reload; replay original, rejeição e falha isolados.
- [x] Web/API mobile PostgreSQL, regressões financeiras, tipos/build/visual completo.

438 visuais completos PASS (9.4m),29 focados,6 Web/API PostgreSQL (1.0m),
49 PostgreSQL (70.813s),5 unitários,tipos/build/diff PASS. Sem baseline/tolerância
novos. Base exclusiva:18 comandos/18 auditorias/18 transições de comando,
6 transições de setup,12 entregas,6 Payments; replay,ledger e snapshots preservados.
Capturas fixture/reais360 inspecionadas;360/390/430 testados nas duas estações.
Logs:visual-artifacts/spec026/runtime/t10d1-{focused,integration,postgres-tests,
readback,build,visual}.log. Web não possui script test/lint genérico.
UX23/T10d parcial; lote/legado/disponibilidade permanecem protegidos. Próximo
recorte T10d.2. Aparelho,piloto,tempo humano e publicação não verificados.

### T10d.2 — evidência local
- [x] Item fora do lote avança; linhas selecionadas e barreiras conservadas.
- [x] Journals separados e vinculados à sessão; replay/readback preservados.
- [x] Web/API PostgreSQL mobile, regressões financeiras, tipos/build/visual completo.

447 visuais completos PASS (9.2m),38 focados PASS (51.1s),6 Web/API PostgreSQL
PASS (1.1m),49 PostgreSQL PASS (68.929s),5 unitários,tipos/build final/diff PASS.
Sem alteração de baseline/tolerância/export. 360/390/430 nas duas estações;
capturas fixture360 inspecionadas. Base exclusiva:18 comandos/18 auditorias,
30 transições,12 entregas,6 Payments; command_id/ledger/snapshots preservados.
Logs:visual-artifacts/spec026/runtime/t10d2-{focused,integration,postgres-tests,
readback,build-final,visual-final}.log. Sem script Web test/lint genérico.
UX23/T10d parcial; próximo T10d.3: investigar disponibilidade por produto,
versionamento e recuperação antes de liberar esse escopo. Legado/QuickCatalog
e novo lote durante pendência conservam barreiras. Aparelho/piloto/publicação
não verificados; sem commit/push/merge/deploy.

### T10d.3 — evidência local
- [x] API opt-in com recibo/replay e versão esperada; legado preservado.
- [x] Auditoria, autorização, isolamento e rollback; finanças/snapshots preservados.
- [x] Concorrência PostgreSQL e regressões relevantes; migração/checks aplicáveis.

65 Django PostgreSQL PASS (71.667s), incluindo11 novos testes de disponibilidade,
mais16 Quick Catalog pytest PostgreSQL PASS (24.68s), executados sequencialmente.
Check/migration drift/compilação Python/diff PASS; Ruff dos arquivos novos PASS.
Arquivos models/views/serializers conservam19 avisos presentes em HEAD.
Logs:visual-artifacts/spec026/runtime/t10d3-{tests-final,pytest-final,lint-new,
lint-existing,lint-baseline}.log. Nenhuma UI alterada; browser/mobile visual,
tipos/build Web não executados nesta slice. UX23/T10d permanece parcial.
Próxima T10d.4: journal Web por produto com versão/recibo e recuperação antes de
liberar disponibilidade independente. Sem aparelho/piloto/publicação comprovados.

### T10d.4 — disponibilidade Web por produto
- [x] Journal persistido antes de POST; versão/estado/chave e sessão originais
  preservados após reload e retry, sem duplicar alteração.
- [x] Recibo inconsistente, falha de readback, versão obsoleta, no-op,
  sessão diferente e storage inválido/adulterado/falho cobertos.
- [x] Produtos distintos e itens verificáveis independentes; lote/item pendente
  preservados, mesmo produto bloqueado e configuração/legado protegidos.
- [x] Seis jornadas Web/API PostgreSQL em Cozinha/Bar 360/390/430; pedidos,
  snapshots, ledger e Payments preservados. Tipos/build e regressões PASS.
- [x] Suíte visual completa final e revisão de evidências:465 PASS (9.1m),
  capturas fixture e real360 inspecionadas, diff e isolamento revisados.

18 cenários novos de navegador, mais regressões de produção; 6 jornadas reais
PASS (41.8s), 60 Django PostgreSQL PASS (63.333s), 5 unitários de configuração
PASS. Readback exclusivo: 12 AvailabilityCommands APPLIED, 12 auditorias de
comando, 12 mudanças, 12 produtos em versão2; 6 comandos de produção e6 Payments.
Logs: visual-artifacts/spec026/runtime/t10d4-{focused-final,integration,
postgres-tests,readback,build-final,visual-final}.log. Visual final PASS.
Sem novo baseline/tolerância/export. Aparelho, tempo humano, piloto e publicação
continuam não verificados; UX23/T10d amplo permanece parcial.

Execução visual inicial teve464 PASS e1 corrida de sincronização no teste de
retry de lote. Espera corrigida sem reduzir asserções;5 repetições PASS e suíte
completa final465 PASS. Produto não mudou entre as duas execuções completas.
PostgreSQL descartável encerrado; sem commit/push/merge/deploy. Próxima tarefa T11.

### T11a/T11b — recuperação e filas Android (2026-10-13)
Pendências locais exibem estado, data e resumo do registro original. Abrir contexto
consulta somente a comanda canônica para pedido/pagamento/preço/estrutura, ou a
fila e task exata de entrega; não confirma nem substitui payload, chave ou sessão.
Troca de sessão bloqueia retomada; consulta suspensa revalida a sessão antes de
publicar contexto. Retry de entrega reutiliza a intenção existente da mesma task.
Prontos é o filtro inicial, inclusive no pico; Chamadas e Pendências são filtros
explícitos. Contagem desconhecida usa —. Pendências não ocupam o topo fixo.
Entrega organiza dados e botão verticalmente para fonte ampliada.
Correção/estorno/caixa sem contexto canônico continuam revisão explícita.
UX27: auditoria do backend encontrou conclusão manual; inferência passiva não
foi demonstrada. Preservada confirmação manual até evidência de source/confidence/
provenance e correção por exceção. T11 ampla permanece aberta.

Validação final T11a/T11b: 71 testes unitários Android PASS; 24 verificações
Compose PASS (4 cenários x 360/390/430dp x fontScale 1.0/2.0); 1 jornada
Android/API real PASS após recompilação final; 40 regressões Django PostgreSQL
PASS. Build/APKs/lint PASS (0 erros, 8 warnings, 2 hints); runner Python compila.
Readback do banco exclusivo porta55478: 0 Orders, 0 Payments após navegação.
Captura final360/f200 inspecionada: filtros legíveis em coluna. Primeira matriz
falhou em360/f200 por produto comprimido; corrigidos layout de entrega e filtros,
com nova matriz completa PASS. Não reduzidas asserções de envio/contexto.
Logs em visual-artifacts/spec026/runtime: t11-build-final-accessible.log,
t11-final-{360,390,430}-{1.0,2.0}.log, t11-real-final.log,
t11-postgres-tests.log, t11-readback-final.log; capturas t11-final-evidence/.
Diff do recorte revisado; alterações anteriores preservadas, sem dados pessoais.
API, emulador e PostgreSQL exclusivos desta validação encerrados. Sem commit,
push, merge ou deploy. Não comprova ergonomia física, tempos humanos, inferência
passiva ou piloto. T11a restante e T11/UX26/27 amplos permanecem abertos.

### T11c — conferência do turno original de caixa (2026-10-13)
Pendências CashMovement/CashClose oferecem leitura do shiftId original, inclusive
encerrado. CashShiftViewModel mantém contexto de conferência separado de state
operacional; GET não altera ponto selecionado, turno ativo, payload, chave ou
registro criptografado. Após GET revalida sessão, igualdade do envelope e shift ID.
Falha, turno inexistente, ID divergente e outra sessão não exibem snapshot.
Tela sobreposta mantém fila/filtro/posição anterior; retornar invalida leitura em
andamento. Oferece somente retorno/atualizar consulta, sem comandos financeiros.
Mostra comando original e movimentos canônicos; não infere sucesso/falha por
valor, motivo ou ausência do movimento. Reconciliação gerencial segue necessária.

Validação final T11c: 72 unitários Android PASS; 18 Compose PASS (3 cenários x
360/390/430dp x fontScale1.0/2.0), com retorno/consulta44dp, sem ações financeiras,
loading/falha; 1 jornada Android/API PostgreSQL PASS com turno encerrado original,
outro turno ativo preservado, envelopes intactos, ID divergente/inexistente,
troca de sessão durante GET e rejeição de adoção por novo login. As snapshots
originais/atuais permanecem idênticas após navegação; não marcou intenção concluída.
14 regressões Django caixa/autorização PostgreSQL PASS (8.137s). Build/APKs/lint
final PASS (0 erros,8 warnings,2 hints), diff do recorte PASS. Readback exclusivo:
0 Orders,0 Payments,0 SUPPLY/WITHDRAWAL/CORRECTION enviados pelas pendências;
aberturas/contagens/fechamentos usados apenas para montar fixtures de turnos.
Captura360/f200 final inspecionada; estado guardado claramente distinto da leitura.
Logs visual-artifacts/spec026/runtime/t11c-build-validated.log,
t11c-final-{360,390,430}-{1.0,2.0}.log, t11c-real-validated.log,
t11c-postgres-tests.log, t11c-readback-final.log; capturas t11c-final-evidence/.
Primeira inicialização do cluster usou porta padrão; cluster exclusivo reiniciado
com porta55478 explícita antes dos testes. API/emulador/PostgreSQL exclusivos
encerrados; alterações anteriores preservadas; sem dados pessoais, commit/push/
merge/deploy. Arquivos do recorte: CashRecoveryScreen.kt, CashShiftViewModel.kt,
AttendanceScreen.kt, RecoveryPresentation.kt, RecoveryPresentationTest.kt,
CashRecoveryApiTest.kt, CashRecoveryScreenTest.kt; docs026/012/014, design e README
Android atualizados. Não comprova ergonomia física nem tempos humanos. Próximo
recorte: consulta canônica de correção/estorno; T11/UX26 amplo, UX27 inferência,
aparelho e piloto seguem abertos.

### T11d — conferência de correção e estorno (2026-10-13)
Três GETs canônicos resolvem item/Tab, payment/Tab e correction/item/payment/Tab.
OrderItem requer order.correct; payment/correction requerem refund.create.
Settlement exige payment da mesma Tab/Venue. Foreign/missing retornam404 indistintos;
query inválida400; capability403; sem autenticação401; POST405. Leitura não exige
reauth e não concede mutations; reauth e autorização financeira permanecem.
Android valida IDs conhecidos do envelope, alvo na Tab, sessão e registro após I/O.
Conferência separada não altera cart/seleção nem reenvia operação; alvo cancelado,
payment estornado, correction aplicada e Tab encerrada continuam investigáveis.
Registro/chave/payload preservados; nova sessão não adota e erro não publica contexto.
Retorno conserva fila/filtro; estado guardado e estado consultado são distintos.
Rótulos REFUNDED/PARTIALLY_REFUNDED traduzidos somente na apresentação compartilhada.
Ausência de correction nas pendências não comprova falha; estado do alvo não prova
resultado do envelope. Reconciliação gerencial e critérios de inferência continuam.

Validação final T11d: 76 unitários Android PASS;12 Compose PASS (2 cenários x
360/390/430dp x fontScale1.0/2.0),7 Compose adjacentes de filas/caixa PASS;
1 jornada Android/API PostgreSQL PASS na versão final (5.692s), repetida durante
validação com3 fixtures independentes. Consulta item cancelado, payment estornado,
correction aplicada e Tab encerrada; store/envelope e snapshots financeiros iguais
antes/depois, alvo inexistente e nova sessão bloqueados, sem marcar confirmação.
71 Django PostgreSQL PASS (124.110s), incluindo6 novos testes de resolução/read-only,
capability/autenticação, foreign/missing, cross-Tab, query inválida e estado histórico.
Build/APKs/lint PASS (0 erros,8 warnings,2 hints). Readback do banco exclusivo:
3 Orders,3 Payments,3 OrderCorrections,3 Refunds, todos fixtures das3 jornadas;
nenhuma nova operação em consulta, verificado pelos snapshots antes/depois.
Captura final360/f200 inspecionada, rótulo Estornado corrigido só na UI. Sem baseline,
tolerância, migration ou regra financeira nova; Web/PWA não recebeu UI neste recorte.
Primeiros testes locais falharam por fixtures sem confirmed_at e Product duplicado;
fixtures corrigidas. Primeira matriz teve falhas em360/390 com fonte ampliada por
asserções sobre nós fora da composição/viewport; rolagem específica adicionada,
mantendo visibilidade/conteúdo e proibição de replay; nova matriz completa PASS.
Logs visual-artifacts/spec026/runtime/t11d-build-final-labels.log,
t11d-final-{360,390,430}-{1.0,2.0}.log, t11d-adjacent-final.log,
t11d-real-validated.log, t11d-postgres-tests.log, t11d-readback.log;
capturas t11d-final-labels-evidence/. Diff do recorte revisado, alterações anteriores
preservadas e sem contexto pessoal. API/emulador/PostgreSQL exclusivos encerrados.
Sem commit/push/merge/deploy. Arquivos finais T11d: API recovery_views.py,
test_recovery_context.py e rodada_api/urls.py; Android ExceptionalRecovery.kt,
ExceptionalRecoveryScreen.kt, ExceptionalRecoveryTest.kt, ExceptionalRecoveryApiTest.kt,
ExceptionalRecoveryScreenTest.kt, OperationsRepository.kt, OperationsViewModel.kt,
RecoveryPresentation.kt, RecoveryPresentationTest.kt e AttendanceScreen.kt;
docs026/006/014/017, design e README Android. Gates UX26/G1 integrado, inferência
UX27 com source/confidence/provenance, aparelho/tempos humanos e piloto continuam.

## T12a — Critérios verificáveis
- Motivos de duas propostas permanecem independentes por ID; decisão envia motivo,
  versão e alvo capturados antes do PIN. Cancelar PIN preserva ambos os rascunhos.
- Enquanto aguarda PIN, motivos/decisões e consulta de outro dia ficam bloqueados;
  sucesso remove só o rascunho da proposta decidida. Solicitação própria não oferece decisão.
- Fechamento, caixa, propostas, pagamentos e histórico de estorno usam rótulos humanos;
  desconhecido é sinalizado sem atribuir sucesso. Contratos/enums/valores não mudam.
- Fixtures mobile 360/390/430 com acessibilidade, tipos/build e visual completo sem
  alteração de baselines. Sem mudança financeira/API, integração real não declarada.

## T12b.1 — Turno original da exceção
- Alerta CASH_SHIFT e bloqueios CASH_SHIFT/OVERDUE_CASH_SHIFT apontam ao ID original,
  com retorno ao alerta/fechamento. Destino focaliza resumo acessível após consulta.
- Turno fechado fora da primeira página é selecionado mesmo com outro turno ativo;
  caixa da resposta deve estar na lista autorizada e coincidir na segunda leitura.
- UUID inválido, 403/404, resposta com outro ID/caixa e caixa não listado não selecionam
  turno alternativo. Origem externa é substituída por /manage. Navegação não faz POST.
- Fixtures mobile 360/390/430, a11y, tipos/build e visual completo; não declarar prova
  real de API/PostgreSQL a partir das fixtures. Outros alvos de T12 continuam abertos.

## T12b.2 — Conferência de Payment por ID
- Alerta PAYMENT abre registro exato com retorno; consulta não depende da lista de
  Tabs e encontra pagamento em Tab encerrada mesmo com outro pagamento na comanda.
- Valor, método/status humanos, histórico original e IDs para auditoria são exibidos;
  pendente não recebe saldo reembolsável confirmado. Consulta não oferece mutations.
- UUID inválido, 403/404, resolver/Tab divergentes, pagamento ausente e troca de sessão
  não publicam contexto. Atualização negada remove leitura anterior; origem externa
  retorna a /manage; intenção de estorno em storage permanece inalterada.
- Fixtures360/390/430+a11y/foco, build/tipos e visual completo; API existente preservada.
  Não declarar integração financeira real a partir das fixtures.

## T12b.3 — Critérios da conferência de item/correção
- Item exato entre vários, cancelado/Tab encerrada; estado original e valor/quantidade
  canônicos. Correção aplicada fora da lista de pendências vem do resolver existente.
- Correção confere pagamento explicitamente vinculado e presente na mesma Tab;
  ausência/ID incompatível/403/404/sessão trocada não publica contexto alternativo.
- Links de alerta/item e estornos/correção conservam origem local; foco acessível;
  consulta não realiza POST nem muda intenção financeira guardada.
- Mobile360/390/430+a11y, regressão de estornos, build/tipos/visual completo.
  Correção sem pagamento e telas de decisão permanecem fora deste recorte.

- [x] Contas do Atendimento limita cada página a 10 comandas e permite próxima/anterior, busca global e preservação de rascunhos; PDV permanece com 200.
