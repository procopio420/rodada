# Spec 026 — Redução de fricção operacional

Estado: execução incremental com recortes locais documentados até T10b; próxima implementação T10c. Critérios amplos e gates globais permanecem abertos.
Data: 2026-10-12. Base documental: main em 0a2038d.

## Revalidação integrada — recebimento em comanda encerrada

Uma comanda encerrada selecionada no histórico não deve exibir formulário para
novo recebimento em dinheiro. A intenção ambígua já preservada continua visível
para conferência na comanda original, inclusive encerrada; ocultar o formulário
nunca remove ou troca seu envelope. Regressão: jornada real de impressão com
fechamento da comanda e recuperação de recebimento com resposta perdida.

## Objetivo

Reduzir esforço, tempo e carga cognitiva nas operações frequentes do Rodada,
priorizando funcionários sob pressão e preservando segurança financeira.
Esta spec organiza o diagnóstico; propostas não equivalem a contratos
implementados ou homologação de piloto.

## Fonte e evidência

Leia o [relatório completo](../../docs/design/ux-friction-audit-2026-10-12.md),
incluindo a seção H de navegação real. São 35 achados UX-01–UX-35.
Código e demo auditados: c198c9bd239a5ee0a0884a76ccb9b623245ae162.
M distingue ações executadas; E distingue estimativas; NM significa não medido.
Navegação realizada em Chrome desktop 1363×936 no ambiente Railway demo.
Android, pico controlado e falha deliberada de rede não foram executados.

**Atualização obrigatória:** PR #98, main 0a2038d, já substitui
Aceitar → Preparar → Pronto por Iniciar preparo → Pronto em Cozinha/Bar.
Os nove cliques de UX-03/H2 são evidência histórica do deploy c198c9b.
Na nova main, o código sugere seis ações para três linhas; não declarar essa
contagem medida sem repetir a jornada no novo deploy. Revalidar UX-03 antes
de implementar; não restaurar aceite redundante nem auto-iniciar preparo.

## Relação com specs existentes

- Spec 023 governa paridade visual; fidelidade não comprova boa usabilidade.
- Spec 021 operacional e Spec 025 de coesão continuam proprietárias de seus
  contratos existentes; esta orientação não os substitui silenciosamente.
- Specs 001/003/004/006/008–018 permanecem responsáveis por estados, dinheiro,
  autoria, autorização, disponibilidade, conectividade e recuperação.
- Cada slice futura deve declarar spec proprietária, comportamento antes/depois,
  fora de escopo e critérios verificáveis antes de alterar código.

## Guidance para comportamento futuro

1. Seleção de comanda deve manter destino claro e não perder draft silenciosamente.
2. Pedido e carrinho devem permanecer acessíveis sem percorrer catálogo completo.
3. Nome, código e mesa devem resolver comandas sem associação financeira ambígua.
4. Repetir rodada cria novo draft com configuração revalidada; não repete chave antiga.
5. Produção deve registrar atos reais; agrupamento visual não autoriza mutation em lote.
6. Guest precisa encontrar produtos e ajustar quantidades sem reconstruir o pedido.
7. Exceção deve abrir registro correto, com próxima ação e retorno contextual.
8. Resultado ambíguo conserva chave e payload imutável até consulta/reconciliação.
9. Fricção proporcional ao risco: desfazer edição local difere de revogar QR ou estornar.
10. Redução de cliques só é aceita sem piorar erro, visibilidade e recuperação.

## Prioridades

| Frente | Achados | Orientação |
| --- | --- | --- |
| Segurança/contexto | UX-06/07/08/10/22/24/29/34/35 | Preservar draft/intento; tornar correção financeira executável |
| Garçom/cliente | UX-01/02/11/12/13/14/15/16/17/18/19 | Busca, repetição, contexto de mesa, quantidade e acesso ao pedido |
| Produção | UX-03/04/05/23/27/28 | Revalidar #98; lote compatível, passe/disponibilidade e ações independentes |
| Gerência | UX-09/20/21/25/26/30/31/32/33 | Acesso direto ao registro, autorização contextual e recuperação guiada |

UX-34 foi observado como correção encaminhada a “Estornar R$ 0,00” após
parcial fictício. Diagnosticar causa/alocação no servidor antes de propor regra;
não presumir prejuízo nem remover autorização para contornar a pendência.

## Fora de escopo desta entrega

### Recorte local T02 em 12/10/2026

Proprietária: Spec 017, seção UX-34. Antes: recebimento parcial com exposição
suficiente cria REFUND_REQUIRED de zero, sem ação executável. Depois: revisão
gerencial explícita pode aplicar a reversão sem devolver dinheiro, com
revalidação financeira transacional e nenhuma alteração de Payment.
Escopo: cancelamento integral NEW/ACCEPTED e recuperação de pendências legadas
de zero. Não inclui remoção de parte da quantidade paga, produção avançada,
T03, redesenho geral de Estornos, provider, demo compartilhada ou deploy.
O restante do texto de fora de escopo abaixo descreve a entrega documental original.

Implementação, deploy, alteração de banco, provider real, publicação de app,
mudança dos exports/baselines e alegação de UX validada em campo.
Relatório descreve eventos de teste previamente autorizados na demo, não
instrução para repetir operações em produção.

## Critérios e execução

Ver [acceptance.md](acceptance.md), [plan.md](plan.md) e [tasks.md](tasks.md).

### Recorte local T03a / UX-08

Recebimento CASH no POS tem envelope local por sessão, persistido antes do envio,
replay exato e readback do Payment. Conferência server-side de sessão e fingerprint
caixa/tender preservam histórico; não há confirmação offline ou replay automático.
Contratos nas Specs006/012/014. Estorno positivo UX-22 é a próxima slice T03b.
Retomada na mesma aba/sessão foi testada; fechamento de aba e resolução entre
sessões continuam abertos. Ver revalidation.md para evidência local independente
de publicação/piloto.


## Recorte T03b contratado — UX-22

Executar intenção manual de estorno imutável e recuperável na mesma aba/sessão,
com readback canônico, PIN recente, fingerprint financeiro/caixa e replay sem
substituição. Contratos proprietários:006,012,014,017. Provider/cross-session/piloto
continuam fora deste recorte. Validar antes de marcar tarefas/aceite.


## T04 / UX-06/35 — rascunho por comanda no workspace Web

Atendimento e POS mantêm rascunhos não enviados separados por Tab.id enquanto
o workspace está montado. Trocar A→B→A, abrir outra comanda, navegar pelas seções
montadas do Atendimento, pesquisar ou recolher não apaga nem transporta linhas.
Produto/quantidade/variant/modifiers/instruções ficam ligados ao destino original;
catálogo atual revalida preço, configuração e disponibilidade antes de confirmar.
Seleção da Tab atual sempre revela o workspace; recolher continua explícito no
cabeçalho. Após seleção bem-sucedida, foco vai ao título da comanda.

Descartar rascunho exige diálogo nomeando a comanda e confirmação; Voltar/Escape
preservam linhas e foco. Descarte e confirmação limpam somente o destino ativo.
Com rascunho não vazio, fechamento fica bloqueado com orientação de confirmar ou
descartar. Tab nova começa vazia sem limpar o rascunho anterior. Falha na leitura
da Tab mantém destino/rascunho anteriores. Seleção/abertura em andamento bloqueia
edição/envio e outro switch; respostas não podem deslocar uma intenção enviada.

Pedido em envio/ambíguo, correção pendente e recebimento pendente continuam
bloqueando troca, recolher e descarte; nunca converter payload já enviado em draft
editável. T04 não modifica os endpoints financeiros nem o replay existente.
Limite deste recorte: memória do workspace, sem persistir credenciais ou conteúdo
em storage. Reload, fechar aba, outra sessão/aparelho e recuperação durável de
pedido enviado são contratos de continuação T05; não declarar resolvidos.

## T05a / UX-07 — recuperação de confirmação staff Web

Antes do primeiro envio, Atendimento/POS salva em sessionStorage um envelope
versionado com Venue, ator, sessão, Tab, gateway original, instante e payload/chave imutáveis.
Não guarda tokens, PIN ou dados completos do catálogo. Uma intenção por aba;
ambiguidade bloqueia novos pedidos, troca, edição, descarte e fechamento.
Após reload, a operação fica visível mesmo sem selecionar a Tab original.
Retomada é explícita, revalida auth/me e exige Venue/ator/sessão originais;
sessão revogada/diferente não adota nem descarta a intenção. Não há autoenvio.
Replay envia o mesmo payload/chave e exige Order canônico; leitura da comanda
incluindo o mesmo Order deve passar antes de limpar storage e liberar o fluxo.
Falha de storage antes do envio impede POST. Envelope inválido ou alterado,
resposta perdida, 5xx ou readback falho preservam bloqueio e orientação.
Somente rejeição inicial conhecida sem commit permite voltar à edição; em
retomada, rejeição não prova ausência de commit e mantém a intenção.
Não afirmar sucesso por saldo, catálogo atual ou simples resposta HTTP vazia.
Fora de escopo: guest, fechar aba, outra sessão/aparelho, fila offline,
persistência de draft não enviado e reconciliação gerencial entre sessões.

## T05b / UX-07 — recuperação guest na mesma visita

Guest preserva antes do POST envelope versionado de payload/chave, instante e
scope não secreto (Venue/GuestSession/Table/occupancy/generation/Tab), sem copiar
credencial guest. Scope vem do contexto autorizado da API; IDs não autorizam.
Após resposta perdida/reload, mostra Verificar mesmo pedido, sem autoenvio.
Revalida contexto e compara scope integral antes de replay; sessão/visita/Tab
alterada, expirada/revogada, bloqueio QR e contexto indisponível não transferem
pedido nem descartam a intenção. API continua revalidando autorização sob locks.
Replay usa payload/chave congelados, valida Order/tab_id e readback no contexto
original antes de limpar storage/carrinho e anunciar sucesso. Falha/ambiguidade
bloqueiam outro envio/edição/nova Tab. Só rejeição inicial conhecida sem commit
permite revisão; replay rejeitado conserva envelope. Storage inválido/falho
bloqueia confirmação. Não criar nova sessão automaticamente para intenção antiga.
Fora de escopo: fechar aba, outra sessão/aparelho, drafts após reload, fila
fully-offline, reconciliação gerencial e novos pagamentos.

### T06a — Navegação de comandas na Web
A Web deve consumir `next_offset` do contrato existente, com próxima/anterior página no PDV, Atendimento e histórico do Atendimento. Uma navegação falha conserva a página anterior; respostas obsoletas não substituem a página vigente. Seleção e rascunhos permanecem independentes da página. O filtro de apelido existente deve informar que filtra somente a página atual. Busca global por nome/código/mesa e contexto de mesa ficam fora deste recorte. Paginação por offset não representa um snapshot: novas comandas podem mudar os limites entre páginas.

### T06b — Busca global por apelido
GET /tabs/ aceita q opcional (até 120 caracteres): substring literal do apelido após normalização Unicode, casefold, remoção de acentos e colapso de espaços. Filtro é aplicado no Venue autenticado antes da paginação existente; q vazio retorna o inventário. Sem nome permanece acessível ao limpar a busca. Homônimos não são mesclados nem selecionados automaticamente; UUID real distingue opções homônimas/sem nome. Web PDV/Atendimento/histórico aplicam busca explicitamente e reiniciam na página 1; falha conserva resultados e busca aplicada anteriores. Seleção/rascunhos não são alterados. Campo derivado de busca é preenchido para dados existentes e mantido em save de apelido, sem mudar valor original ou snapshots financeiros. Escritas em massa de apelidos devem preencher esse campo explicitamente. Fora de escopo: código curto, mesa, Android e otimização da projeção financeira.

### T06c — Mesa como entrada para a comanda Web
Atendimento Web filtra pelo nome/número normalizado da mesa no inventário completo já entregue por GET hospitality/tables. Mostra todas as comandas da ocupação ativa como escolhas explícitas por ID, sem mesclar ou selecionar homônimos automaticamente. Apenas associações não liberadas aparecem. Abrir uma escolha lê GET tabs/{id}/?occupancy_id=...&table_id=...: valida UUIDs, Venue, mesa/ocupação vigentes e vínculo não liberado; conflito responde 409 e mantém seleção/rascunho anteriores. Esse contexto é uma precondição de leitura, não nova autorização nem bloqueio duradouro da mesa; comandos posteriores mantêm as regras próprias da Tab. Busca/abertura não fazem mutations. A comanda pode estar fora da página de Contas. Voltar à mesa preserva filtro e rascunhos, com foco na mesa de origem. Pedidos/correções/recebimentos ambíguos e abertura em andamento impedem navegação. Fora de escopo: nova comanda automaticamente associada, movimento A→B, transferência financeira, código curto, Android e persistência do contexto após reload.

Retorno T06c reutiliza a última lista autorizada, atualização periódica e Atualizar explícito; não dispara outra varredura de comandas. A abertura revalida o vínculo no backend independentemente dessa lista.

### T06d — proteção da API de movimento existente
Antes da interface Web, corrigir duas lacunas da Spec 009: rejeitar destino com
generation divergente de Table.access_generation sob os locks existentes e
preservar motivo opcional na auditoria. Movimento e replay mantêm identidade,
histórico financeiro e ocupação de origem; replay autorizado não ressuscita
vínculo liberado. A continuação Web abaixo utiliza esse comando protegido.

Continuação Web T06d: escolha por ID, destino já ocupado, confirmação de
origem→destino e motivo opcional; gateway exclusivamente MOVE_LOCATION.
GET contextual captura versão antes de confirmar. Intenção persistida antes
do POST e retomada explícita na mesma aba/Venue/ator/sessão; sem autoenvio.
Ambiguidade congela payload/chave e bloqueia edição/navegação. Resultado
imutável e readback autorizados confirmam operação, distinguindo local atual
de destino original. Rejeição inicial definitiva libera revisão; replay
rejeitado conserva intenção. Contrato proprietário e limites na Spec 009.

### Recorte T07a / UX-01
Contrato proprietário em Spec 001: acesso persistente à revisão do carrinho Android, com quantidade/total e retorno ao catálogo, mais detalhes financeiros expansíveis. Não muda ledger, pagamentos, autorização, replay ou conferência financeira. As demais ações T07, categorias e ergonomia física continuam fora deste recorte.


### Spec 026 T10a — acesso às regiões de produção
Em 360–430 px, Cozinha/Bar oferecem navegação persistente Fila, Prontos e
Disponibilidade. Uma ação rola e transfere foco à região nomeada; não registra
preparo, retirada ou disponibilidade. Fila mostra contagem de linhas aguardando/
em preparo, Prontos somente READY e Disponibilidade o total de produtos da
estação. Antes do snapshot, contagem é desconhecida (—); cache/erro conserva
a sinalização existente de estado antigo. Atalhos permanecem utilizáveis durante
mutation/erro, mas não liberam ações bloqueadas. Regiões permanecem montadas.
Iniciar preparo → Pronto continua manual. Lote, agrupamento por configuração,
concorrência independente e SLA são fora deste recorte. Desktop preserva layout.


### Spec 026 T10b — resumo por configuração confirmada
O resumo de produção agrupa apenas Product com snapshot operacional equivalente
na mesma estação. Renderiza variação, modificadores e observação do snapshot,
sem reconstruir pelo catálogo atual. Identidade inclui IDs e nomes/semântica
confirmados, observação exata e campos operacionais adicionais. Ordem dos
modificadores e campos JSON não diferencia preparo; preço, quantidade e total
não são configuração operacional. Estados NEW/ACCEPTED/PREPARING podem aparecer
no mesmo resumo com contagens separadas: o resumo não é seleção nem lote.
Ausência/incompletude de snapshot ou identidade/routing divergentes conserva
linha independente e aviso Configuração não registrada; nunca inferir padrão
pelo catálogo. Item sem Product ID permanece independente. Não alterar snapshots,
Payments, ledger, auditoria, estado nem permissões.

Contrato para lote futuro (pendente): seleção explícita de linhas inteiras com
mesmo produto/configuração/estação e estados de origem compatíveis; revisão do escopo/quantidade
e destino PREPARING ou READY, sempre autoria humana. Comando canônico deve
registrar chave e fingerprint imutável, autorizar todas as linhas no Venue,
validar estado/snapshot/quantidade restante sob locks em ordem determinística,
responder resultado por linha e replay do resultado. Conflito em qualquer linha
rejeita integralmente sem efeito parcial. READY deriva Dispatch por linha na
mesma transação. Não usar fan-out de transições individuais: o endpoint atual
não oferece replay idempotente nem precondições suficientes. Indisponibilidade
posterior do catálogo não cancela preparo confirmado. Nenhum botão/lote, comando
novo ou concorrência independente é implementado em T10b.


### Spec026 T10c.1 — comando canônico de produção
POST /production/batches/ exige order.confirm, sessão ativa e Venue autorizado.
Payload: idempotency_key (até 120), station BAR/KITCHEN, target_state PREPARING/READY,
e lines (1–50 IDs distintos) com item_id, expected_state, quantity restante positiva
e snapshot_fingerprint SHA256 retornado na fila. Linhas inteiras do mesmo produto,
configuração confirmada e estação. NEW/ACCEPTED são origens compatíveis para
PREPARING; READY exige PREPARING em todas. O estado esperado de cada linha é exato.
Legado incompleto não admite lote; permanece operável individualmente.
Locks: sessão original, Tabs por ID, OrderItems por ID. Validar tudo antes de
aplicar. Resposta APPLIED ou REJECTED contém ID do comando e resultado de cada
linha; rejeição persistida não aplica nenhuma. Repetir chave/payload na mesma
sessão devolve recibo original, mesmo após mudança de estado; payload diferente
retorna IDEMPOTENCY_CONFLICT. Outra sessão não adota comando antigo.
Auditoria associa comando e transições ao ator. READY deriva Dispatch na mesma
transação; falha inesperada reverte comando, transições, auditoria e Dispatch.
Preço/disponibilidade atuais não substituem snapshots; ledger e Payments intactos.
T10c.1 entrega API, não seleção/revisão Web nem recuperação de intenção no browser.
T10c.2 deve persistir chave/payload vinculados à sessão antes do envio, revisar
seleção explícita, recuperar resposta perdida e validar mobile 360/390/430.


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

### T10d.4 — recuperação Web de disponibilidade por produto
Persistir intenção por produto na mesma aba/sessão antes do POST, capturando
estado solicitado, availability_version, chave e Venue/staff/session. Replay após
reload conserva payload e endpoint originais; recibo validado e readback completo
são obrigatórios antes de remover a pendência. Versão obsoleta não vira sucesso.
Produtos versionados distintos e itens verificáveis podem operar durante pendência
de disponibilidade/item/lote persistido, sem alterar pedidos confirmados. Revisão
de lote e mutation legada mantêm barreira global; QuickCatalog, modificadores,
novo lote e ações legadas seguem bloqueados enquanto houver intenção pendente.
Storage inválido/adulterado/falho e sessão divergente falham fechado sem adotar
intenções. Catálogo sem versão conserva comando legado e bloqueio conservador.
Testar replay, recibo inválido, falha de readback, conflitos, sessão/storage,
ações simultâneas e mobile360/390/430 em fixtures e Web/API PostgreSQL.
### T11a/T11b — contexto recuperável e filas Android
Agora oferece filtros Prontos, Chamadas e Pendências com contagens separadas.
Prontos é o padrão, inclusive ao ativar modo pico; preserva idade canônica e
ordem das chamadas do servidor, sem inventar urgência entre categorias.
Pedidos guardados deixam de ocupar um painel fixo antes das entregas e aparecem
em Pendências, com acesso à conferência existente. Estados desatualizados não
apresentam contagens como leitura atual.
Pendência de pedido/recebimento/ajuste/estrutura com Tab original verificável abre
essa Tab via GET autorizado, inclusive fora da lista local. Entrega pendente abre
Prontos e destaca sua task; retry manual reutiliza registro original, sem novo ID.
Abrir contexto não envia mutation, não descarta evidência, não troca payload/chave
ou sessão e não abandona draft/seleção existente silenciosamente. Intenção ausente,
outra sessão ou storage ilegível não navega para contexto presumido.
Correção/estorno/caixa sem resolução canônica direta conservam orientação de revisão;
o acesso direto desses tipos permanece aberto, sem busca por label ou varredura de
comandas. Fluxo financeiro/reauth e reconciliação de pedidos existentes preservados.
UX27: investigar inferência antes de remover ações de entrega; sem alternativa
comprovada, preservar conclusão manual e auditoria. Aparelho/tempos humanos são gates.

### T11c — conferência do turno original de caixa no Android
Pendência CashMovement/CashClose da sessão original abre somente GET do shiftId
registrado, inclusive encerrado, sem selecionar o turno ativo atual. Tela separada
mostra comando guardado, estado/data operacional do turno e movimentos canônicos;
não oferece suprimento, sangria, contagem, fechamento ou replay. Ausência de um
movimento na consulta não prova falha, e similaridade de valor/motivo não prova
sucesso. O registro permanece intacto para reconciliação autorizada pela gerência.
IDs divergentes, falha de acesso/rede/storage ou troca de sessão durante a leitura
não publicam contexto. Voltar preserva a seleção operacional anterior. Navegação
e atualização repetem apenas a leitura do turno original. Correção/estorno seguem
fora deste recorte até contrato canônico específico, sem varredura de comandas.
