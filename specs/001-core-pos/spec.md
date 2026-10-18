# Spec 001 â€” Core POS

**Status:** Draft for implementation

## Objetivo

Entregar o nÃºcleo de PDV prÃ³prio do Rodada: catÃ¡logo, Tab/comanda, pedido, cobranÃ§a, pagamento manual e fechamento, sem depender de mesa fixa e sem codificar localizaÃ§Ã£o como identidade financeira.

## UsuÃ¡rios

- Staff: cria/encontra Tabs, lanÃ§a pedidos e recebe pagamentos.
- Cashier: fecha Tabs e opera caixa.
- Manager: cancela/ajusta com auditoria e gerencia disponibilidade global.
- Bar/Cozinha: acompanha produÃ§Ã£o e pode marcar itens da prÃ³pria estaÃ§Ã£o como disponÃ­veis/indisponÃ­veis quando autorizado.

## Invariantes

- todo Order pertence a uma Tab;
- Tab pode existir sem Customer, Table ou ServicePoint;
- Tab pode ter `display_label` humano sem que isso seja identidade forte;
- Table nunca Ã© dona do ledger;
- vÃ¡rias Tabs podem compartilhar a mesma TableOccupancy;
- fechar Tab nÃ£o libera mesa automaticamente;
- o domÃ­nio deve aceitar identificadores adicionais de Tab sem migrar ledger/pedidos;
- disponibilidade operacional de produto Ã© separada de `Product.active`;
- todos os canais revalidam a mesma disponibilidade na confirmaÃ§Ã£o do pedido;
- mudanÃ§a de disponibilidade nunca reescreve pedido jÃ¡ confirmado.

## HistÃ³rias

### POS-001 â€” Abrir Tab

Staff abre Tab anÃ´nima, com label/apelido ou ligada a Customer/Relationship. LocalizaÃ§Ã£o Ã© opcional.

### POS-002 â€” CatÃ¡logo

Produtos tÃªm nome, preÃ§o, ativaÃ§Ã£o administrativa e `fulfillment_station`. `active` controla configuraÃ§Ã£o/publicaÃ§Ã£o; nÃ£o deve ser usado como indisponibilidade operacional de curto prazo.

### POS-003 â€” Criar pedido

Staff adiciona produtos a uma Tab e confirma Order.

### POS-004 â€” Snapshot de preÃ§o

OrderItem captura preÃ§o no momento da confirmaÃ§Ã£o; alteraÃ§Ã£o posterior no catÃ¡logo nÃ£o altera pedido existente.

### POS-005 â€” Gerar charges

Itens confirmados geram charges idempotentes no ledger da Tab.

### POS-006 â€” Estados operacionais

OrderItem suporta estados mÃ­nimos `NEW`, `ACCEPTED`, `PREPARING`, `READY`, `PICKED_UP`, `DELIVERED`, `CANCELLED`.

Confirmar pedido no Atendimento/caixa/guest cria item em `NEW`, sem marcar inÃ­cio de preparo. Na Cozinha/Bar, o operador inicia explicitamente o preparo com uma aÃ§Ã£o `NEW â†’ PREPARING` (ou `ACCEPTED â†’ PREPARING` para compatibilidade com fluxos existentes). `ACCEPTED` segue disponÃ­vel quando houver aceite separado, mas nÃ£o Ã© clique obrigatÃ³rio para cozinhar. Somente a transiÃ§Ã£o para `PREPARING` preenche `preparing_at`. Itens `NEW`/`ACCEPTED` aparecem como aguardando, nunca como em preparo; agrupamentos de demanda podem somÃ¡-los desde que informem o status real.

Fechamento financeiro da Tab nÃ£o abandona produÃ§Ã£o jÃ¡ confirmada. TransiÃ§Ãµes
legais de preparo/entrega continuam autorizadas para esses OrderItems, sem reabrir
a Tab ou alterar ledger. Novos pedidos/pagamentos e correÃ§Ãµes financeiras mantÃªm
as restriÃ§Ãµes de Tab fechada.

### POS-007 â€” Cancelamento

Cancelamento apÃ³s confirmaÃ§Ã£o exige permissÃ£o e trilha de auditoria; ledger recebe reversÃ£o/adjustment em vez de apagar histÃ³rico.

### POS-008 â€” Receber pagamento

Registrar `CASH`, `CARD`, `PIX` ou `OTHER`; P0 aceita confirmaÃ§Ã£o manual.

Valores e troco sÃ£o centavos inteiros positivos dentro do intervalo persistÃ­vel;
payload invÃ¡lido Ã© rejeitado sem efeito financeiro. Retry de intenÃ§Ã£o confirmada
recupera o Payment original mesmo apÃ³s fechamento da Tab; nova intenÃ§Ã£o permanece
bloqueada e uma chave reutilizada com outro valor/mÃ©todo Ã© conflito.

### POS-009 â€” Fechar Tab

Tab fecha normalmente com exposure zero. DivergÃªncia exige manager action.

### POS-010 â€” Caixa

CashShift registra abertura, recebimentos por mÃ©todo, ajustes e fechamento resumido.

### POS-011 â€” LocalizaÃ§Ã£o flexÃ­vel

Tab pode se associar/desassociar de ServicePoint ou TableOccupancy sem alterar pedidos, ledger ou Customer.

### POS-012 â€” MÃºltiplas Tabs no mesmo contexto fÃ­sico

Duas ou mais Tabs podem coexistir no mesmo TableOccupancy sem compartilhar saldo, pagamentos ou fechamento.

### POS-013 â€” Disponibilidade operacional

Bar/Cozinha com permissÃ£o pode marcar Product da sua estaÃ§Ã£o como `AVAILABLE` ou `UNAVAILABLE`. Manager pode alterar qualquer produto.

A mutation registra ator, horÃ¡rio, valor anterior, novo valor e motivo opcional.

### POS-014 â€” Uma fonte de verdade

Menus de staff, caixa e guest usam a mesma disponibilidade operacional. Um Product indisponÃ­vel aparece claramente como indisponÃ­vel e nÃ£o pode gerar novo item confirmado.

### POS-015 â€” RevalidaÃ§Ã£o na confirmaÃ§Ã£o

A API valida disponibilidade ao confirmar o Order. Se o produto ficou indisponÃ­vel depois de entrar no carrinho, a confirmaÃ§Ã£o falha para os itens afetados com resposta explÃ­cita para atualizaÃ§Ã£o do carrinho.

OrderItem jÃ¡ confirmado nÃ£o Ã© cancelado ou alterado por mudanÃ§a posterior de disponibilidade.

## Fora de escopo

- fiscal/NFC-e;
- estoque profundo e baixa automÃ¡tica por insumo;
- delivery/iFood;
- PSP real;
- prÃ©-autorizaÃ§Ã£o;
- dispatch automÃ¡tico;
- guest ordering completo;
- lifecycle/limpeza de mesa;
- NFC/QR de acesso;
- loyalty.

Esses comportamentos de mesa/guest sÃ£o detalhados em `specs/004-table-guest-ordering/`.

## Requisitos nÃ£o funcionais

### T07a â€” acesso ao carrinho Android

Na comanda aberta, um controle persistente alterna catÃ¡logo e carrinho, informa
quantidade e total do rascunho e nÃ£o envia pedidos. A revisÃ£o do carrinho nÃ£o
depende de percorrer o catÃ¡logo. Retornar preserva busca e posiÃ§Ã£o do catÃ¡logo.
Saldo, avisos e aÃ§Ãµes financeiras permanecem disponÃ­veis; o detalhamento contÃ¡bil
Ã© expansÃ­vel por comanda. Recolher nÃ£o altera saldo, autorizaÃ§Ã£o, validaÃ§Ãµes ou a
conferÃªncia completa do diÃ¡logo de pagamento. IntenÃ§Ã£o pendente mantÃ©m os mesmos
bloqueios de ediÃ§Ã£o e o mesmo replay explÃ­cito. Categorias, nova comanda, teclado
e confirmaÃ§Ã£o de liberaÃ§Ã£o de mesa ficam fora deste recorte.

- fluxo mobile-first;
- dinheiro em centavos;
- mutations transacionais;
- auditoria para cancelamento/ajuste;
- pedido comum deve ser lanÃ§Ã¡vel em poucos toques;
- API desenhada para realtime posterior;
- nÃ£o expor IDs sequenciais como credenciais pÃºblicas.


## T04 / UX-06/35 â€” rascunho por comanda no workspace Web

Atendimento e POS mantÃªm rascunhos nÃ£o enviados separados por Tab.id enquanto
o workspace estÃ¡ montado. Trocar Aâ†’Bâ†’A, abrir outra comanda, navegar pelas seÃ§Ãµes
montadas do Atendimento, pesquisar ou recolher nÃ£o apaga nem transporta linhas.
Produto/quantidade/variant/modifiers/instruÃ§Ãµes ficam ligados ao destino original;
catÃ¡logo atual revalida preÃ§o, configuraÃ§Ã£o e disponibilidade antes de confirmar.
SeleÃ§Ã£o da Tab atual sempre revela o workspace; recolher continua explÃ­cito no
cabeÃ§alho. ApÃ³s seleÃ§Ã£o bem-sucedida, foco vai ao tÃ­tulo da comanda.

Descartar rascunho exige diÃ¡logo nomeando a comanda e confirmaÃ§Ã£o; Voltar/Escape
preservam linhas e foco. Descarte e confirmaÃ§Ã£o limpam somente o destino ativo.
Com rascunho nÃ£o vazio, fechamento fica bloqueado com orientaÃ§Ã£o de confirmar ou
descartar. Tab nova comeÃ§a vazia sem limpar o rascunho anterior. Falha na leitura
da Tab mantÃ©m destino/rascunho anteriores. SeleÃ§Ã£o/abertura em andamento bloqueia
ediÃ§Ã£o/envio e outro switch; respostas nÃ£o podem deslocar uma intenÃ§Ã£o enviada.

Pedido em envio/ambÃ­guo, correÃ§Ã£o pendente e recebimento pendente continuam
bloqueando troca, recolher e descarte; nunca converter payload jÃ¡ enviado em draft
editÃ¡vel. T04 nÃ£o modifica os endpoints financeiros nem o replay existente.
Limite deste recorte: memÃ³ria do workspace, sem persistir credenciais ou conteÃºdo
em storage. Reload, fechar aba, outra sessÃ£o/aparelho e recuperaÃ§Ã£o durÃ¡vel de
pedido enviado sÃ£o contratos de continuaÃ§Ã£o T05; nÃ£o declarar resolvidos.

## T05a / UX-07 â€” recuperaÃ§Ã£o de confirmaÃ§Ã£o staff Web

Antes do primeiro envio, Atendimento/POS salva em sessionStorage um envelope
versionado com Venue, ator, sessÃ£o, Tab, gateway original, instante e payload/chave imutÃ¡veis.
NÃ£o guarda tokens, PIN ou dados completos do catÃ¡logo. Uma intenÃ§Ã£o por aba;
ambiguidade bloqueia novos pedidos, troca, ediÃ§Ã£o, descarte e fechamento.
ApÃ³s reload, a operaÃ§Ã£o fica visÃ­vel mesmo sem selecionar a Tab original.
Retomada Ã© explÃ­cita, revalida auth/me e exige Venue/ator/sessÃ£o originais;
sessÃ£o revogada/diferente nÃ£o adota nem descarta a intenÃ§Ã£o. NÃ£o hÃ¡ autoenvio.
Replay envia o mesmo payload/chave e exige Order canÃ´nico; leitura da comanda
incluindo o mesmo Order deve passar antes de limpar storage e liberar o fluxo.
Falha de storage antes do envio impede POST. Envelope invÃ¡lido ou alterado,
resposta perdida, 5xx ou readback falho preservam bloqueio e orientaÃ§Ã£o.
Somente rejeiÃ§Ã£o inicial conhecida sem commit permite voltar Ã  ediÃ§Ã£o; em
retomada, rejeiÃ§Ã£o nÃ£o prova ausÃªncia de commit e mantÃ©m a intenÃ§Ã£o.
NÃ£o afirmar sucesso por saldo, catÃ¡logo atual ou simples resposta HTTP vazia.
Fora de escopo: guest, fechar aba, outra sessÃ£o/aparelho, fila offline,
persistÃªncia de draft nÃ£o enviado e reconciliaÃ§Ã£o gerencial entre sessÃµes.

### T06a â€” NavegaÃ§Ã£o de comandas na Web
A Web deve consumir `next_offset` do contrato existente, com prÃ³xima/anterior pÃ¡gina no PDV, Atendimento e histÃ³rico do Atendimento. Uma navegaÃ§Ã£o falha conserva a pÃ¡gina anterior; respostas obsoletas nÃ£o substituem a pÃ¡gina vigente. SeleÃ§Ã£o e rascunhos permanecem independentes da pÃ¡gina. O filtro de apelido existente deve informar que filtra somente a pÃ¡gina atual. Busca global por nome/cÃ³digo/mesa e contexto de mesa ficam fora deste recorte. PaginaÃ§Ã£o por offset nÃ£o representa um snapshot: novas comandas podem mudar os limites entre pÃ¡ginas.

### T06b â€” Busca global por apelido
GET /tabs/ aceita q opcional (atÃ© 120 caracteres): substring literal do apelido apÃ³s normalizaÃ§Ã£o Unicode, casefold, remoÃ§Ã£o de acentos e colapso de espaÃ§os. Filtro Ã© aplicado no Venue autenticado antes da paginaÃ§Ã£o existente; q vazio retorna o inventÃ¡rio. Sem nome permanece acessÃ­vel ao limpar a busca. HomÃ´nimos nÃ£o sÃ£o mesclados nem selecionados automaticamente; UUID real distingue opÃ§Ãµes homÃ´nimas/sem nome. Web PDV/Atendimento/histÃ³rico aplicam busca explicitamente e reiniciam na pÃ¡gina 1; falha conserva resultados e busca aplicada anteriores. SeleÃ§Ã£o/rascunhos nÃ£o sÃ£o alterados. Campo derivado de busca Ã© preenchido para dados existentes e mantido em save de apelido, sem mudar valor original ou snapshots financeiros. Escritas em massa de apelidos devem preencher esse campo explicitamente. Fora de escopo: cÃ³digo curto, mesa, Android e otimizaÃ§Ã£o da projeÃ§Ã£o financeira.

### T06c â€” Mesa como entrada para a comanda Web
Atendimento Web filtra pelo nome/nÃºmero normalizado da mesa no inventÃ¡rio completo jÃ¡ entregue por GET hospitality/tables. Mostra todas as comandas da ocupaÃ§Ã£o ativa como escolhas explÃ­citas por ID, sem mesclar ou selecionar homÃ´nimos automaticamente. Apenas associaÃ§Ãµes nÃ£o liberadas aparecem. Abrir uma escolha lÃª GET tabs/{id}/?occupancy_id=...&table_id=...: valida UUIDs, Venue, mesa/ocupaÃ§Ã£o vigentes e vÃ­nculo nÃ£o liberado; conflito responde 409 e mantÃ©m seleÃ§Ã£o/rascunho anteriores. Esse contexto Ã© uma precondiÃ§Ã£o de leitura, nÃ£o nova autorizaÃ§Ã£o nem bloqueio duradouro da mesa; comandos posteriores mantÃªm as regras prÃ³prias da Tab. Busca/abertura nÃ£o fazem mutations. A comanda pode estar fora da pÃ¡gina de Contas. Voltar Ã  mesa preserva filtro e rascunhos, com foco na mesa de origem. Pedidos/correÃ§Ãµes/recebimentos ambÃ­guos e abertura em andamento impedem navegaÃ§Ã£o. Fora de escopo: nova comanda automaticamente associada, movimento Aâ†’B, transferÃªncia financeira, cÃ³digo curto, Android e persistÃªncia do contexto apÃ³s reload.

Retorno T06c reutiliza a Ãºltima lista autorizada, atualizaÃ§Ã£o periÃ³dica e Atualizar explÃ­cito; nÃ£o dispara outra varredura de comandas. A abertura revalida o vÃ­nculo no backend independentemente dessa lista.

### T07c / UX-11 â€” destino explÃ­cito do pedido Android
Sem comanda selecionada, Pedir leva Ã  lista existente de Contas e orienta escolher
a comanda; nÃ£o abre diÃ¡logo de criaÃ§Ã£o nem chama criaÃ§Ã£o/confirmaÃ§Ã£o de pedido.
A seleÃ§Ã£o usa Tab.id e lÃª o detalhe pelo fluxo autorizado existente. HomÃ´nimos
nÃ£o sÃ£o mesclados nem selecionados automaticamente. Nova comanda Ã© aÃ§Ã£o distinta
na lista e no tÃ­tulo do diÃ¡logo de criaÃ§Ã£o; criaÃ§Ã£o sÃ³ ocorre por confirmaÃ§Ã£o
explÃ­cita. Lista vazia orienta criar sem fazÃª-lo automaticamente. Loading/busy
bloqueiam nova criaÃ§Ã£o e seleÃ§Ã£o. Comanda selecionada mantÃ©m seu workspace,
rascunho e intenÃ§Ãµes existentes: nÃ£o se altera navegaÃ§Ã£o de draft, replay ou saldo.
Escopo de seleÃ§Ã£o: inventÃ¡rio local jÃ¡ carregado; busca/paginaÃ§Ã£o Android, mesa,
persistÃªncia de draft e novos bloqueios entre sessÃµes ficam fora desta slice.

### T08a / UX-13 â€” repetir rodada no Android
A aÃ§Ã£o por pedido confirmado prepara uma revisÃ£o local na mesma Tab aberta.
Copia somente unidades restantes de linhas nÃ£o canceladas; exclusÃµes sÃ£o informadas.
Identidades de Product, variante e opÃ§Ãµes vÃªm do payload/snapshot, nunca dos nomes.
AusÃªncia de snapshot estruturado bloqueia a rodada, inclusive legado vazio.
PreÃ§o, nome e texto da configuraÃ§Ã£o histÃ³ricos sÃ£o comparados com o catÃ¡logo atual
na revisÃ£o. Produto inativo/ausente/indisponÃ­vel, seleÃ§Ã£o invÃ¡lida, quantidade ou
valor fora do contrato bloqueiam toda a inclusÃ£o; nÃ£o substituir por defaults.
Adicionar ao carrinho exige confirmaÃ§Ã£o explÃ­cita e revalidaÃ§Ã£o do mesmo conteÃºdo
revisado; alteraÃ§Ã£o de catÃ¡logo/histÃ³rico exige nova revisÃ£o. Preserva draft existente,
com linhas novas separadas por configuraÃ§Ã£o, e bloqueia busy, leitura em andamento,
catÃ¡logo nÃ£o online e intenÃ§Ã£o de pedido pendente. NÃ£o recebe nem envia automaticamente.
Confirmar pedido usa o fluxo autorizado e a nova chave da intenÃ§Ã£o existente; repetir
nÃ£o reutiliza IDs/chaves histÃ³ricos nem altera snapshots, Payments ou ledger.
A API revalida catÃ¡logo/limite/permissÃ£o na confirmaÃ§Ã£o. Fora de escopo: Web,
repetir entre Tabs, substituir itens bloqueados e afirmar ergonomia em aparelho fÃ­sico.

### T08b / UX-13 â€” repetir rodada no Atendimento Web
No histÃ³rico da Tab aberta, Repetir rodada lÃª detalhe autorizado e catÃ¡logo atuais
antes da revisÃ£o. Somente unidades restantes de linhas nÃ£o canceladas sÃ£o copiadas;
exclusÃµes sÃ£o informadas. IDs de Product/variante/opÃ§Ãµes vÃªm do snapshot canÃ´nico,
nunca de nomes. Legado sem snapshot completo, produto ausente/inativo/indisponÃ­vel,
seleÃ§Ã£o removida/invÃ¡lida e quantidade fora de 1â€“99 bloqueiam a inclusÃ£o inteira.
A revisÃ£o mostra preÃ§os e configuraÃ§Ã£o anteriores/atuais e destaca diferenÃ§as.
Adicionar ao carrinho Ã© explÃ­cito, preserva o draft da Tab e nÃ£o envia pedido.
ConteÃºdo alterado durante revisÃ£o exige reabrir a revisÃ£o. Busy, leitura, fechamento,
correÃ§Ã£o, recebimento ou intenÃ§Ã£o pendente bloqueiam repetiÃ§Ã£o/navegaÃ§Ã£o no contexto.
Falha de leitura preserva draft e histÃ³rico. Confirmar pedido usa a recuperaÃ§Ã£o
existente e cria nova chave, sem reutilizar a intenÃ§Ã£o histÃ³rica. A API revalida
catÃ¡logo/limite/autorizaÃ§Ã£o e preserva snapshots/ledger/Payments. Repetir sÃ³ atende
Ã  mesma Tab; Web POS e guest, persistÃªncia de drafts e ganhos humanos ficam fora.

### T08d / UX-13 â€” repetiÃ§Ã£o no PDV Web
O PDV reutiliza a revisÃ£o canÃ´nica de rodada implementada no Atendimento Web.
HistÃ³rico permanece imutÃ¡vel: copiar IDs/configuraÃ§Ã£o/quantidades para um novo
rascunho com preÃ§o e disponibilidade atuais, diferenÃ§as explÃ­citas e bloqueio
integral se houver configuraÃ§Ã£o invÃ¡lida ou legado nÃ£o verificÃ¡vel. Cancelar
preserva o rascunho; incluir Ã© Ãºnico e nÃ£o confirma pedido. Mesma Tab aberta,
dados atuais e ausÃªncia de operaÃ§Ã£o pendente sÃ£o obrigatÃ³rios. PendÃªncias de
pedido, recebimento ou correÃ§Ã£o bloqueiam repetiÃ§Ã£o; revisÃ£o bloqueia recebimento
e troca de Tab. ConfirmaÃ§Ã£o explÃ­cita cria nova intenÃ§Ã£o pelo fluxo existente;
resposta perdida reutiliza payload/chave originais. NÃ£o alterar Payments, ledger
ou snapshots confirmados. Testar mobile, mudanÃ§a de catÃ¡logo, replay e histÃ³rico
em PostgreSQL descartÃ¡vel. NÃ£o ampliar catÃ¡logo, pagamentos ou navegaÃ§Ã£o.

### Spec026 T10 â€” lote de produÃ§Ã£o (contrato pendente de implementaÃ§Ã£o)
T10b muda somente apresentaÃ§Ã£o por configuraÃ§Ã£o confirmada, conforme Spec010.
Lote futuro exige comando prÃ³prio idempotente com capability order.confirm e
isolamento de Venue, seleÃ§Ã£o explÃ­cita de linhas inteiras compatÃ­veis, estado
de origem/snapshot/quantidade restante esperados e destino PREPARING ou READY.
TransaÃ§Ã£o bloqueia linhas em ordem determinÃ­stica, valida todas antes de aplicar
e rejeita integralmente qualquer conflito; resultado identifica cada linha e
se foi aplicada ou nÃ£o. Replay conserva resultado original e fingerprint; mudar
payload com a mesma chave Ã© conflito, nÃ£o novo preparo. READY preserva derivaÃ§Ã£o
de Dispatch por linha, timestamps e auditoria com ator e ID do comando.
Indisponibilidade posterior nÃ£o cancela trabalho confirmado. Falha em uma linha
ou Dispatch reverte todo o comando; ledger/Payments/snapshots permanecem intactos.
Sem fan-out de endpoints individuais, auto-inÃ­cio ou baixa de estoque.


### Spec026 T10c.1 â€” comando canÃ´nico de produÃ§Ã£o
POST /production/batches/ exige order.confirm, sessÃ£o ativa e Venue autorizado.
Payload: idempotency_key (atÃ© 120), station BAR/KITCHEN, target_state PREPARING/READY,
e lines (1â€“50 IDs distintos) com item_id, expected_state, quantity restante positiva
e snapshot_fingerprint SHA256 retornado na fila. Linhas inteiras do mesmo produto,
configuraÃ§Ã£o confirmada e estaÃ§Ã£o. NEW/ACCEPTED sÃ£o origens compatÃ­veis para
PREPARING; READY exige PREPARING em todas. O estado esperado de cada linha Ã© exato.
Legado incompleto nÃ£o admite lote; permanece operÃ¡vel individualmente.
Locks: sessÃ£o original, Tabs por ID, OrderItems por ID. Validar tudo antes de
aplicar. Resposta APPLIED ou REJECTED contÃ©m ID do comando e resultado de cada
linha; rejeiÃ§Ã£o persistida nÃ£o aplica nenhuma. Repetir chave/payload na mesma
sessÃ£o devolve recibo original, mesmo apÃ³s mudanÃ§a de estado; payload diferente
retorna IDEMPOTENCY_CONFLICT. Outra sessÃ£o nÃ£o adota comando antigo.
Auditoria associa comando e transiÃ§Ãµes ao ator. READY deriva Dispatch na mesma
transaÃ§Ã£o; falha inesperada reverte comando, transiÃ§Ãµes, auditoria e Dispatch.
PreÃ§o/disponibilidade atuais nÃ£o substituem snapshots; ledger e Payments intactos.
T10c.1 entrega API, nÃ£o seleÃ§Ã£o/revisÃ£o Web nem recuperaÃ§Ã£o de intenÃ§Ã£o no browser.
T10c.2 deve persistir chave/payload vinculados Ã  sessÃ£o antes do envio, revisar
seleÃ§Ã£o explÃ­cita, recuperar resposta perdida e validar mobile 360/390/430.


### T10c.2 — revisão e recuperação Web do lote
Resumo verificável oferece Selecionar preparo / Selecionar prontos por grupo.
Dialog exige seleção humana (inicialmente vazia), linhas inteiras, até 50, e
exibe estação, configuração confirmada, destinos, estados e total de unidades.
Revisão não altera domínio. Confirmar exige snapshot atual compatível; mudança
de estado/quantidade/fingerprint exige nova revisão, sem substituir seleção.
Persistir envelope estrito em sessionStorage antes do POST, com chave/payload
originais e vínculo Venue/staff/session. Nenhuma credencial ou nome de cliente
é persistido. Falha de armazenamento impede envio; resposta perdida/5xx/recibo
inconsistente preserva pendência. Verificar mesmo lote repete payload/chave;
nunca monta lote novo. Sessão diferente bloqueia adoção. Estação diferente
orienta retorno à original. Recibo terminal válido exige leitura atual da fila
antes de remover intenção. Rejeição integral libera nova revisão após leitura.
Resultado discrimina cada linha, sem afirmar sucesso parcial. Durante revisão,
envio ou pendência, bloquear mutations da produção; navegação permanece disponível.
Usar ActionDialog, tokens existentes, foco/44px e estados acessíveis. Legado
sem fingerprint/configuração não oferece lote. UX23 de ações independentes
permanece fora desta slice; não afirmar medição humana, aparelho ou publicação.


### T10d.1 — ações individuais verificáveis independentes
Item com configuração confirmada e fingerprint usa o comando canônico de produção
com uma linha, conservando seleção humana por Iniciar preparo/Pronto. Intenção
individual persistida antes do POST, por item e sessão; múltiplos itens distintos
podem aguardar resposta sem bloquear uns aos outros. Mesmo item não aceita outro
comando enquanto houver envio/pendência. Repetição usa payload/chave originais.
Ler/validar todas as intenções ao montar a tela, inclusive itens ausentes da fila
ou já READY; recuperação não depende de o botão original continuar renderizado.
Não adotar sessão/Venue/ator diferentes; dados inválidos/storage falho bloqueiam
novos envios. Recibo por linha e leitura atual exigidos antes de remover intenção.
Rejeição afeta somente aquela linha; nunca inferir sucesso parcial. Leitura
pós-comando é serializada; eventos recebidos durante ela são relidos depois.
Enquanto houver intenção individual, lote/legado/disponibilidade/QuickCatalog
seguem bloqueados. Revisão ou pendência de lote bloqueia todos os itens. Fila
indisponível/sessão revogada bloqueia globalmente. Não alterar finanças, snapshots,
autorização, inferir preparo ou tornar disponibilidade concorrente nesta slice.
UX23 permanece parcial até investigar os demais escopos em T10d.2.

### T10d.2 — item independente de lote pendente
Após persistir lote, somente seus IDs ficam bloqueados para ações individuais
verificáveis. Outro item pode usar seu comando canônico independente, conservando
journal próprio e readback serializado. Antes de persistir lote e durante revisão,
bloqueio global permanece. Lote inválido/adulterado ou pertencente a outra sessão
impede novo envio individual. Não liberar novo lote enquanto houver pendência,
nem legado/disponibilidade/QuickCatalog; não mudar snapshots, autorização ou finanças.
Replay original do lote convive com intenção individual disjunta. Testar resposta
perdida, sessão/storage, conflitos e mobile Web/API PostgreSQL.

### T10d.3 — comando canônico de disponibilidade (API)
POST de disponibilidade aceita idempotency_key + expected_version juntos,
com state e reason opcional até600 caracteres. Chave por Venue/sessão, vinculada
à autoria, produto e payload; replay devolve recibo terminal original sem efeitos,
payload diferente retorna IDEMPOTENCY_CONFLICT. Revalidar sessão/capability.
Versão obsoleta persiste REJECTED/VERSION_CONFLICT sem mudar disponibilidade.
APPLIED muda estado/versão/changed_at apenas quando há mudança; no-op auditado
como comando sem inventar mudança. Auditoria conserva antes/depois, versões,
ator, sessão, motivo e comando; transação reverte tudo em falha inesperada.
Catálogo expõe availability_version. POST legado sem ambos preservado para clientes
existentes; campos parciais/inválidos rejeitados. Produto de outro Venue não aceito.
Não alterar Product.active, itens confirmados,snapshots,ledger ou Payments.
Recorte API: UI e seus bloqueios permanecem; T10d.4 implementará recuperação Web.

### T10d.4 — disponibilidade Web recuperável por produto
O Web captura availability_version e persiste intenção vinculada a Venue/staff/
session antes do comando canônico. Retry/reload conservam endpoint, chave e
payload; recibo validado e leitura canônica precedem remoção da pendência.
Outro produto versionado ou item verificável pode operar durante pendência de
disponibilidade/item/lote persistido. Mesmo produto, revisão, legado, novo lote,
modificadores e QuickCatalog mantêm proteção. Storage inválido/adulterado/falho e
sessão divergente impedem adoção/envio. Sem versão, conservar caminho legado.
Não alterar pedidos confirmados, snapshots, ledger, Payments ou autorização.

## Nome operacional staff — 2026-10-15

Abertura pela API staff exige nome/apelido nao vazio de ate120 caracteres. Isso
nao exige Customer nem identificacao civil e nao muda abertura interna/guest.
Comandas existentes sem nome e recibos antigos permanecem preservados.

## Quitação conclui comanda — 2026-10-17

Pagamento confirmado que reduz exposição a zero conclui a Tab na mesma transação, com closed_at e auditoria vinculada ao Payment. Pagamento parcial ou pendente não conclui. Nenhuma TableOccupancy é liberada e produção confirmada continua. Retry recupera o Payment original sem novo fechamento; não concluir retroativamente Tabs antigas em leituras. Clientes exibem CLOSED apenas no histórico. Não alterar regras de estorno, transferências ou reabertura explícita.
