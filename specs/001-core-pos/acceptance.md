# Acceptance — Spec 001

- [x] Staff abre uma Tab sem selecionar mesa ou Customer.
- [x] Staff pode abrir uma Tab com nome/apelido simples.
- [ ] Staff pode opcionalmente associar/mover a Tab entre contextos físicos.
- [ ] Duas Tabs podem compartilhar a mesma TableOccupancy mantendo ledgers independentes.
- [ ] Fechar uma Tab não encerra automaticamente a TableOccupancy.
- [x] Pedido com produtos ativos e operacionalmente disponíveis é confirmado com snapshot de preço.
- [x] Cozinha/Bar autorizado marca produto da estação como indisponível e a alteração é auditada.
- [x] Produto indisponível deixa de ser confirmável por `STAFF`, `CASHIER` e `GUEST` na regra/API de Order; a UI guest completa fica na Spec 004.
- [x] Carrinho stale é rejeitado na confirmação se algum item ficou indisponível, com indicação dos itens afetados.
- [x] Tornar produto indisponível não altera OrderItem já confirmado.
- [x] Todo Order possui `tab_id`.
- [x] Cada item confirmado gera efeito financeiro exatamente uma vez.
- [x] Estados operacionais registram timestamps.
- [ ] Confirmar pedido mantém item `NEW` e `preparing_at=null`; Cozinha/Bar mostra como aguardando; uma única ação “Iniciar preparo” faz `NEW → PREPARING` e registra timestamp, sem aceite adicional.
- Item confirmado continua preparo/entrega após pagamento e fechamento financeiro;
  `test_financial_close_does_not_strand_confirmed_production` verifica API/ledger.
- [ ] Cancelamento pós-confirmação não apaga histórico e exige auditoria.
- [x] Pagamento manual reduz exposure.
- Retry de Payment manual já confirmado após fechamento recupera o mesmo ID;
  payload diferente mantém conflito e nova intenção continua bloqueada.
  Prova: `test_committed_payment_replay_after_close_recovers_original_receipt`.
- Payload monetário fracionário, booleano, fora de intervalo ou malformado é
  rejeitado sem Payment; `test_invalid_manual_payment_payload_cannot_truncate_cents_or_crash`.
- [x] Tab com exposure zero pode ser fechada.
- [ ] Caixa resume recebimentos por método.

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

### T06a — Paginação Web
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

### T07a — acesso ao carrinho Android
- [x] Controle persistente com quantidade/total; revisão e retorno à posição do catálogo sem envio por navegação.
- [x] Detalhes financeiros expansíveis; guards de taxa, offline, busy e fechamento preservados.
- [x] Edição bloqueada e replay explícito de intenção pendente mantidos.
Evidência: Spec 026 revalidation.md, sete cenários Compose em seis configurações, 59 unitários Android e 35 testes PostgreSQL. Aparelho, jornada Android/API e teclado permanecem abertos.

### T07c — Pedir e Nova comanda Android
- [x] Pedir navega para escolha de conta aberta sem abrir criação; Nova comanda é explícita.
- [x] Homônimos preservam IDs e vazio não cria automaticamente; loading/busy bloqueiam seleção/criação.
Evidência local: cinco cenários em seis configurações, 59 unitários Android, build/lint e 28 testes PostgreSQL PASS; Spec 026 revalidation.md separa limitações de inventário/aparelho/Android-API.

### T08a — evidência local Android
- [x] Histórico abre revisão; cancelar preserva draft e adicionar inclui quantidade/configuração com preço atual sem envio. Unitários/Compose e regressão API/PostgreSQL PASS; ver revalidation da Spec 026.
- [ ] Repetição Web/guest, jornada Android/API completa e aparelho físico.

### T08b — Atendimento Web local
- [x] Revisão de rodada e inclusão preservam drafts/configurações por Tab; falha/cancelamento não enviam pedido. Três jornadas Web/API PostgreSQL em 360/390/430 comprovam nova intenção e replay após resposta perdida sem duplicação; ver Spec 026 revalidation.
- [ ] Repetição guest/Web POS, publicação e observação humana.

### T08d — repetição no PDV Web
- [x] Revisão por IDs/preço/configuração atuais, exclusões e bloqueios, sem defaults ou envio automático.
- [x] Cancelamento/falha preservam draft; inclusão única na mesma Tab; personalização, recebimento ambíguo, encerramento e conteúdo alterado bloqueiam repetição.
- [x] Web/API PostgreSQL 360/390/430: preço atual, nova intenção, replay sem duplicação, histórico/snapshot/Payments e draft da outra Tab preservados.
- [x] 371 testes visuais PASS (7,2 min), tipos/build e diff finais PASS; sem alteração de baseline/tolerância.


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
### T10d.4 — evidência local de disponibilidade Web
- [x] Intenção por produto/sessão, versão capturada e replay/readback sem duplicação.
- [x] Produtos e itens verificáveis independentes; configuração/legado protegidos.
- [x] Mobile360/390/430 em Cozinha/Bar, regressões financeiras e visual completo.

465 visuais completos PASS (9.1m),6 Web/API PostgreSQL PASS,60 Django PostgreSQL
PASS,5 unitários,tipos/build/diff PASS. Corrida no teste de retry de lote corrigida
sem relaxar asserções;5 repetições e execução completa final PASS. Evidências em
specs/026-operational-ux-friction/revalidation.md. PostgreSQL descartável encerrado.
UX23/T10d amplo e gates aparelho/tempo humano/piloto/publicação permanecem abertos.
