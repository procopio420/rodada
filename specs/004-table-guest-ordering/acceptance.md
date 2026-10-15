# Acceptance — Spec 004

T06d Web movement criteria:
- [x] Explicit occupied destination and independent origin lifecycle verified in 360/390/430.
- [x] Web/API PostgreSQL proves one movement after lost response/reload, with immutable financial snapshots and preserved assignment history.

## Validação integrada da demo — revogação realtime

O teste de chamadas guest preserva em memória o token anterior antes de liberar a mesa. Depois da liberação, exige403/GUEST_SESSION_REVOKED em nova solicitação com esse token e ausência dos controles de chamada após reload. SSE pode remover a superfície imediatamente; não depender de clicar em um botão já removido. Contrato de domínio e status/code exigidos permanecem inalterados.

- [x] Mesa possui QR com token opaco não sequencial.
- [x] QR permanece o mesmo quando a mesa muda de lugar.
- [x] Scan do QR resolve a Table sem expor PK interno.
- [x] Table pode existir AVAILABLE sem placement ativo.
- [x] Staff autorizado pode associar/remover o contexto textual de Zone sem alterar ocupação, Tabs, pedidos, ledger ou QR.
- [x] Guest abre PWA sem instalar app ou criar conta.
- [ ] Ao escanear Table sem placement, guest pode selecionar posição aproximada num floorplan 2D sanitizado.
- [ ] Staff pode posicionar ou arrastar uma Table no floorplan.
- [ ] Staff pode retirar uma Table do mapa encerrando apenas o placement, sem apagar a Table ou trocar o QR.
- [ ] Reposicionar Table preserva TableOccupancy, Tabs, Orders, ledger, GuestSession válida e QR.
- [ ] Update concorrente com versão stale não sobrescreve placement silenciosamente.
- [ ] Floorplan guest não expõe estados operacionais de outras mesas, staff ou filas internas.
- [ ] Staff pode agrupar/desagrupar Tables sem fundir suas identidades ou contas.
- [x] Em `DIRECT`, guest pode iniciar atendimento numa Table `AVAILABLE`.
- [x] Em `JOIN_ACTIVE`, guest não inicia ocupação nova.
- [x] Em `DISABLED`, guest não envia pedido.
- [x] Uma TableOccupancy suporta duas ou mais Tabs independentes.
- [x] Todo pedido guest pertence a uma Tab e possui `source=GUEST`.
- [x] Pedido guest chega à mesma pipeline de fulfillment de um pedido staff.
- [x] Item marcado indisponível por Bar/Cozinha aparece indisponível no menu guest sem criar regra paralela.
- [x] Guest não confirma item que ficou indisponível depois de entrar no carrinho.
- [x] Staff bloqueia guest ordering sem fechar Tab nem impedir pedido interno.
- [x] Fechar a última Tab não libera a Table automaticamente.
- [x] `release table` muda `OCCUPIED → DIRTY` e encerra a ocupação.
- [x] Staff inicia limpeza `DIRTY → CLEANING`.
- [x] Staff conclui limpeza `CLEANING → AVAILABLE`.
- [x] Concluir limpeza incrementa `access_generation`.
- [x] GuestSession de geração anterior não consegue criar novos pedidos.
- [x] Guest mantém Cardápio como home durante a sessão e consegue fazer vários pedidos.
- [x] Guest navega por Cardápio / Pedidos / Conta sem precisar entender estados internos do restaurante.
- [x] Guest vê status simplificado RECEBIDO / PREPARANDO / PRONTO-CHEGANDO derivado do fulfillment.
- [x] Guest consegue pedir novamente um item anterior ainda disponível.
- [x] Guest consegue criar solicitação estruturada de atendimento/conta que entra no Dispatch.
- [ ] Guest pode assumir Tab por código curto.
- [ ] Uma Tab pode receber e revogar associação NFC.
- [ ] NFC pode ser reutilizado em outra Tab após revogação/fechamento.
- [ ] Perfil Customer é opcional e pode ser ligado depois sem migrar a Tab.
- [x] Sistema registra timestamps para ocupação, liberação, início e fim da limpeza.

## T05b — aceite do recorte guest

- [x] Resposta perdida/reload retoma payload/chave originais sem duplicar Order/Charge/audit.
- [x] Readback/duplo toque/contexto indisponível mantêm bloqueio até prova canônica.
- [x] Sessão/Tab/ocupação/generation divergentes e revogação/bloqueio não adotam intenção.
- [x] Storage inválido/falho impede POST; rejeição inicial segura permite revisão.
- [x] Jornada real PostgreSQL, Web360/390/430, visual/build/tipos/lint/diff registrados.

Mesma aba com storage íntegro; gates externos e persistência de drafts abertos.

### T06c
- [x] Mesa Web permite filtrar nome/número normalizado e escolher individualmente comandas vinculadas, inclusive fora da página de Contas.
- [x] Abertura direta e retorno preservam filtro, foco, destino e rascunhos; falha mantém contexto anterior e bloqueios pendentes.
- [x] GET contextual rejeita vínculo liberado/movido, ocupação liberada, mesa divergente, IDs inválidos e outro Venue; leitura não altera financeiro/histórico.

Evidência local: 70 testes PostgreSQL PASS; jornada real com 203 Tabs, confirmação única e preservação de ocupação/Payments em 360/390/430 PASS; suíte visual final **318 PASS (6,7 min)**. Build/tipos/diff PASS; Ruff sem avisos novos (15 RUF012 preexistentes nas views, teste PASS). Ver revalidation.md.

### T07b — liberação Android
- [x] Revisão identifica mesa e efeito sobre QR/limpeza; cancelar não chama mutation.
- [x] Alvo original preservado; mudança local de ocupação/generation, busy e permissão bloqueiam.
Evidência: três cenários em seis configurações de emulador, 59 unitários, build/lint e 48 testes PostgreSQL PASS (Spec 026 revalidation.md). Aparelho, Android/API e disputa após snapshot não homologados.

### T08c — evidência local guest
- [x] Revisão atual por IDs/preço/configuração, sem defaults; cancelar preserva draft e inclusão não envia.
- [x] Releitura impede visita/Tab/token divergentes e bloqueio/revogação/falha/conteúdo alterado; configuração distinta não se funde.
- [x] PostgreSQL/Web em 360/390/430: nova intenção, resposta perdida/replay sem duplicação, histórico/Payments preservados; bloqueio de mesa após revisão impede inclusão.

Detalhes, checks completos e limites em specs/026-operational-ux-friction/revalidation.md.

### T09a — quantidade guest local
- [x] +/− acessíveis, zero remove, agrupamento por configuração idêntica e edição conserva quantidade; limite 99 rejeita inclusão/edição/repetição inteira sem perder draft.
- [x] Variantes/opções/notas diferentes permanecem distintas, ordem de option IDs não cria configuração nova; controles e payload pendente preservados nos bloqueios.
- [x] Web/API PostgreSQL 360/390/430: quantidade agrupada enviada uma vez, replay idêntico, exposição/charges corretos e Payments preservados; bloqueio real de mesa em 390.
- [x] 385 testes visuais PASS (7,3 min), tipos/build/diff PASS; resultado final e limites em Spec 026/revalidation.md.

### T09b — evidência local guest
- [x] Busca global por nome, acentos/caixa/espaços nas bordas, categorias consistentes, retorno ao limpar, fallback e vazio; fixture de 146 produtos.
- [x] Filtros/atalho preservam configuração, quantidade, draft e intent; indisponibilidade, bloqueio e revogação respeitados; primeira inclusão não desloca catálogo.
- [x] Web/API PostgreSQL 360/390/430: categoria real, seleção cruzando filtros, bloqueio de mesa, foco/draft e replay sem duplicar Order/Charge.
- [x] 393 testes visuais PASS (7,6 min), Ruff/tipos/build/diff PASS; detalhes na Spec 026. Não implica paridade global, aparelho físico ou publicação.

## Fechamento operacional de 14/10/2026

MVP e roadmap separados em [closeout.md](closeout.md), com matriz de cada
critério original, código, teste, evidência e decisão. Itens opcionais continuam
desmarcados nas issues #144–#148. QR opaco estável é reutilizável em nova visita;
a sessão antiga perde autorização ao liberar/limpar. Não é revogação automática
do QR físico. Gate E2E Web+Android integral permanece #106. Gates do SHA final
e revisão independente são necessários antes do fechamento da #3.

## Gestão de mesas
Contrato: [management-tables.md](management-tables.md). Implementar serviço transacional de quantidade/estado, API protegida, tela dedicada e testes PostgreSQL/mobile. Recorte implementado e validado localmente; evidência e limites em [management-tables-evidence.md](management-tables-evidence.md).

## Issue #145 — TableGroup físico

- [ ] Criar e dissolver dois ou mais membros do mesmo Venue, tanto ocupados como vazios; inventário staff e Guest sanitizado refletem agrupamento.
- [ ] Nunca mesclar ocupação, Tab, QR, sessão, Order, pagamentos ou ledger; histórico de grupo/auditoria permanece.
- [ ] Não permitir Table já agrupada, fora de serviço, de outro Venue, repetida ou comando sem capability.
- [ ] Replay com UUID original é sem efeito, reuso com payload diferente falha; corrida PostgreSQL preserva exclusividade.
- [ ] Migration auditada, CI SHA final, revisão R3 independente, acessibilidade/visual 360/390/430/desktop e integração BFF/PostgreSQL passam.
- [ ] PR mergeado após evidência; só então encerrar issue.

Checklists permanecem abertos até execução verificável; código adicionado não é teste executado.
