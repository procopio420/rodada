# Spec 004 — Table Ops + Guest Ordering

Spec 026 T06d Web: mover uma Tab usa MOVE_LOCATION da Spec 009; não libera
origem, ocupa destino vazio ou migra GuestSession. A escolha aceita somente
outra mesa já ocupada; contexto e versão são revalidados antes de confirmar.
Recuperação da intenção segue o contrato de sessão da Spec 009.

**Status:** MVP operational closeout in progress (2026-10-14); evidence and roadmap in `closeout.md`.

## Objetivo

Permitir que mesas selecionadas tenham ciclo operacional explícito e que clientes possam pedir pelo próprio celular sem instalação obrigatória, mantendo **Tab como unidade financeira**.

## Usuários

- Guest: escaneia QR, cria/assume comanda, acompanha e envia pedidos.
- Staff: associa/move Tabs, libera mesa, inicia/finaliza limpeza e bloqueia guest ordering.
- Manager: configura modos de guest ordering e revisa auditoria/métricas.

## Invariantes

- todo Order pertence a uma Tab;
- Table nunca possui ledger;
- TableOccupancy pode conter várias Tabs;
- Tab pode existir sem TableOccupancy;
- fechar Tab não encerra ocupação automaticamente;
- QR físico resolve Table, não Tab nem posição;
- Table e TablePlacement são entidades distintas;
- Table pode existir sem placement ativo;
- mover/posicionar mesa não muda Tab, Order, ledger ou QR;
- identificadores públicos não são sequenciais/adivinháveis;
- GuestSession é revogável;
- pedidos `GUEST` entram na mesma pipeline de fulfillment dos pedidos do staff;
- guest usa a mesma disponibilidade operacional de Product que staff/caixa e não pode contorná-la.

## Table lifecycle

Estados:

```text
AVAILABLE
OCCUPIED
DIRTY
CLEANING
OUT_OF_SERVICE
```

Transições mínimas:

```text
AVAILABLE -> OCCUPIED
OCCUPIED -> DIRTY          (release table)
DIRTY -> CLEANING
CLEANING -> AVAILABLE      (cleaning complete)
* -> OUT_OF_SERVICE        (manager)
OUT_OF_SERVICE -> AVAILABLE
```

### TABLE-001 — Ocupação automática

Quando permitido pelo modo da mesa, primeiro atendimento/pedido associado a uma Table `AVAILABLE` cria TableOccupancy e move para `OCCUPIED`.

### TABLE-002 — Múltiplas Tabs

Uma ocupação aceita várias Tabs com ledger/pagamentos independentes.

### TABLE-003 — Liberar mesa

Staff marca a mesa como liberada quando o grupo efetivamente sai.

Resultado:

- encerra TableOccupancy;
- status vira `DIRTY`;
- novos guest orders são bloqueados;
- sessões ligadas à ocupação deixam de autorizar novos pedidos.

### TABLE-004 — Limpeza

Staff pode iniciar limpeza e concluir limpeza.

Concluir:

- status `AVAILABLE`;
- registra ator/timestamps;
- incrementa `access_generation`;
- invalida definitivamente autorizações da geração anterior.

### TABLE-005 — Métricas

Registrar dados suficientes para calcular:

- tempo total de ocupação;
- saída → início da limpeza;
- duração da limpeza;
- saída → mesa disponível;
- throughput/giro por mesa;
- histórico de movimentações/placements por atendimento quando útil.

### TABLE-006 — Mesa física sem posição

Uma Table pode existir e estar `AVAILABLE` sem `TablePlacement` ativo. O QR permanente continua resolvendo a mesma Table.

#### Contexto textual P0

Enquanto o `FloorPlan` não é implementado, uma Table pode apontar
opcionalmente para uma `Zone` textual do mesmo Venue (como `Salão`, `Rua` ou
`Varanda`). Staff autorizado pode trocar ou remover essa associação. É uma
mudança de contexto físico auditada e não altera `TableOccupancy`, Tabs,
Orders, ledger, Payments, GuestSession ou QR.

### TABLE-007 — Posicionamento no mapa 2D

Ao iniciar uso de uma mesa sem placement, guest ou staff pode selecionar aproximadamente sua posição em um `FloorPlan` 2D.

O placement registra Table, FloorPlan, coordenadas normalizadas, origem (`GUEST | STAFF`) e auditoria.

### TABLE-008 — Movimento durante atendimento

Staff pode arrastar/reposicionar a mesa no mapa durante uma ocupação. Guest pode propor/confirmar posição apenas conforme política do Venue.

Mover a mesa:

- encerra o placement anterior;
- cria nova posição ativa;
- não recria TableOccupancy;
- não altera Tabs, Orders, ledger, QR ou GuestSession válida.

Quando uma mesa for fisicamente guardada/retirada do layout, staff pode encerrar o placement sem criar outro. Isso não exclui a Table nem invalida seu QR.

### TABLE-009 — Concorrência de placement

Se guest e staff tentarem posicionar a mesma Table ao mesmo tempo, a API usa versão/optimistic locking. O segundo cliente recebe o placement atual e deve confirmar antes de sobrescrever.

### TABLE-010 — Floorplan guest sanitizado

Guest recebe apenas mapa e referências necessárias para reconhecer onde está. Estados de outras mesas, nomes de funcionários, filas e informações operacionais internas não são expostos.

### TABLE-011 — Agrupamento de mesas

Staff pode representar duas ou mais Tables juntas como `TableGroup` temporário.

Agrupar:

- não funde QR;
- não funde Table;
- não exige fundir TableOccupancy;
- não funde Tabs/ledger;
- pode fornecer label operacional e contexto para dispatch.

## Guest ordering

### GUEST-001 — QR opaco

Cada mesa habilitada possui QR permanente apontando para token aleatório, por exemplo:

```text
/ t / 7Fq2xK9mP4vN
```

Não usar `/mesa/24`, `?table_id=24` ou equivalente público sequencial.

### GUEST-002 — PWA sem instalação

Scan abre experiência web mobile-first. Login e instalação não são obrigatórios.

### GUEST-003 — Resolver contexto físico

Após scan válido, UI resolve a Table e cria ou recupera GuestSession.

Se não houver placement ativo, o fluxo pode pedir **Onde vocês estão?** e abrir o floorplan guest para o cliente posicionar a mesa antes de criar/assumir a Tab. Se staff já tiver posicionado, guest apenas vê/confirma o contexto atual.

### GUEST-004 — Criar comanda

Quando política permitir, Guest cria nova Tab com:

- label opcional;
- Customer opcional;
- TableOccupancy atual.

### GUEST-005 — Assumir comanda existente

Guest pode acessar uma Tab existente por fluxo autorizado, inicialmente código curto.

Depois de validado, dispositivo recebe GuestSession ligada à Tab.

### GUEST-006 — Perfil Rodada

Cliente autenticado pode resolver/assumir Tabs ligadas ao próprio Customer sem transformar Customer em requisito do fluxo anônimo.

### GUEST-007 — Pedido direto

Guest adiciona itens disponíveis e confirma Order com `source=GUEST`.

Order entra na mesma fila/estação de Bar/Cozinha usada por pedidos do staff.

O menu consome `ProductAvailability` compartilhado. Itens `UNAVAILABLE` permanecem identificáveis como indisponíveis e não podem ser confirmados. Se a disponibilidade mudar enquanto o item estiver no carrinho, a API rejeita os itens afetados na confirmação e a UI pede atualização.

### GUEST-008 — Acompanhar

Guest vê apenas informações autorizadas da própria Tab:

- pedidos;
- estados relevantes e simplificados para o cliente;
- total/exposure apropriado;
- ações permitidas.

A UX guest não deve fingir precisão operacional inexistente. O baseline visível é `RECEBIDO → PREPARANDO → PRONTO/CHEGANDO`, derivado dos estados internos existentes.

Depois do primeiro pedido, Cardápio continua sendo a home principal. O cliente pode pedir novamente durante toda a sessão, repetir itens anteriores e acompanhar pedidos sem encerrar a experiência.

### GUEST-009 — Bloqueio operacional

Staff pode bloquear guest ordering por Table/ocupação imediatamente.

Bloqueio:

- rejeita novas mutations guest;
- não fecha Tabs;
- não cancela pedidos já confirmados;
- não impede pedidos feitos pelo staff.

### GUEST-010 — Revogação por geração

GuestSession ligada a uma ocupação/generation não pode continuar pedindo depois da liberação/limpeza daquela ocupação.

### GUEST-011 — Modos de mesa

`guest_ordering_mode`:

```text
DISABLED
JOIN_ACTIVE
DIRECT
```

- `DISABLED`: QR não aceita pedido.
- `JOIN_ACTIVE`: guest só entra quando há ocupação ativa.
- `DIRECT`: guest pode iniciar fluxo numa mesa disponível.

### GUEST-012 — Navegação contínua

A navegação base da experiência guest possui no máximo três destinos primários:

- **Cardápio**;
- **Pedidos**;
- **Conta**.

O cardápio prioriza quick-add e uso com uma mão; detalhes/modificadores aparecem somente quando necessários. Pedidos anteriores oferecem **Pedir novamente** quando o item continua disponível.

### GUEST-013 — Solicitações de atendimento

Em vez de uma chamada genérica sempre que possível, guest pode abrir solicitações estruturadas, inicialmente:

- `BILL_REQUEST` — quero pagar;
- `SERVICE_REQUEST` com motivo, como talheres/gelo;
- falar com alguém.

Essas ações criam DispatchTask sem exigir que o garçom marque manualmente cada microestado do pedido.

### GUEST-014 — Conta

Guest pode consultar sua Tab em tempo real. Quando houver identidade de participante suficiente, a UI pode distinguir `minha parte` do total do grupo e preparar futuros fluxos de divisão/pagamento sem transformar Table em conta.

Pagamento online e regras avançadas de split permanecem fora do escopo inicial desta spec.

## Identificadores de Tab

### ID-001 — Código curto

Tab pode receber código curto humano para join. Código não deve ser o PK interno e deve expirar/revogar.

### ID-002 — QR dinâmico da Tab

Staff/Guest pode exibir QR temporário que resolve a Tab sem expor ID interno.

### ID-003 — NFC

Tag/pulseira NFC pode ser associada temporariamente a uma Tab.

Requisitos:

- reutilizável após fechamento/revogação;
- associação auditável;
- UID/token não é prova forte de identidade;
- perda/troca deve permitir revogação imediata.

### ID-004 — Device session

Após join/claim, dispositivo mantém sessão segura para evitar redigitar código a cada pedido.

## Segurança mínima

- tokens públicos aleatórios com entropia suficiente;
- persistir hash quando o token bruto não precisar ser recuperado;
- rate limit em resolução/join/order;
- autorização server-side em toda mutation;
- validar venue, Table, occupancy, generation e Tab;
- revogação imediata;
- auditoria de join, bloqueio, release e mutations relevantes;
- não confiar em label/nome como segredo.

## Fora de escopo inicial

- app nativo obrigatório;
- geofencing;
- pagamento online obrigatório;
- pré-autorização;
- carteira pré-paga;
- NFC seguro de alto nível/secure element;
- loyalty;
- ordering sem internet totalmente offline pelo cliente.

Pagamento pelo celular poderá entrar depois sem alterar o princípio de que pedido pertence à Tab.

A UX canônica está detalhada em `docs/product/guest-experience.md`.

## Entrega executável Web — Spec 020

O contrato implementado nesta entrega e seus critérios verificáveis estão na [Spec 020](../020-web-operational-completion/spec.md). Inclui catálogo com fallback de ícones (IA/worker adiados pelo usuário), histórico da própria comanda guest, seleção/revisão de turnos antigos, relatórios operacionais e calendário auditado. Não marca todo o roadmap desta spec como concluído. Consulte [validação e limites](../../docs/development/web-operational-completion.md).

### Round 2 — Chamada estruturada de atendimento

Em ocupação ativa, guest pode chamar atendimento ou pedir conta à equipe.
A sessão determina mesa/ocupação; payload aceita apenas tipo e UUID da intenção.
A interface guarda o UUID antes de enviar, conserva-o em resultado desconhecido
para retry e anuncia sucesso somente após resposta canônica. Criar solicitação
não paga nem fecha a comanda e não expõe identidade/ownership do staff ao guest.

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

### T06c — Mesa como entrada para a comanda Web
Atendimento Web filtra pelo nome/número normalizado da mesa no inventário completo já entregue por GET hospitality/tables. Mostra todas as comandas da ocupação ativa como escolhas explícitas por ID, sem mesclar ou selecionar homônimos automaticamente. Apenas associações não liberadas aparecem. Abrir uma escolha lê GET tabs/{id}/?occupancy_id=...&table_id=...: valida UUIDs, Venue, mesa/ocupação vigentes e vínculo não liberado; conflito responde 409 e mantém seleção/rascunho anteriores. Esse contexto é uma precondição de leitura, não nova autorização nem bloqueio duradouro da mesa; comandos posteriores mantêm as regras próprias da Tab. Busca/abertura não fazem mutations. A comanda pode estar fora da página de Contas. Voltar à mesa preserva filtro e rascunhos, com foco na mesa de origem. Pedidos/correções/recebimentos ambíguos e abertura em andamento impedem navegação. Fora de escopo: nova comanda automaticamente associada, movimento A→B, transferência financeira, código curto, Android e persistência do contexto após reload.

Retorno T06c reutiliza a última lista autorizada, atualização periódica e Atualizar explícito; não dispara outra varredura de comandas. A abertura revalida o vínculo no backend independentemente dessa lista.

### T07b / UX-10 — confirmação local da liberação Android
Liberar mesa abre revisão com nome da mesa, encerramento da ocupação, revogação
do acesso guest atual e encaminhamento para limpeza. Não fecha nem paga comandas.
Cancelar, voltar ou tocar fora não chamam a mutation. Confirmar exige permissão,
nenhuma submissão em curso e a mesma ocupação ativa do inventário local; mudança
local de ocupação/status invalida a revisão, sem substituir seu alvo. O servidor
mantém autorização e regras existentes. Este recorte não acrescenta precondição
transacional ao endpoint: disputa após a última atualização local e recuperação
durável de resposta ambígua continuam gates separados, sem alegar proteção nova.

### T08c / UX-13 — repetir rodada guest
Repetir rodada por pedido histórico lê contexto e catálogo autorizados com o token
já ativo. Não resolve QR, cria sessão/comanda ou troca destino para repetir.
Venue/session/table/occupancy/generation e Tab devem coincidir com o contexto e
token originais; exigir ocupação ativa, Tab aberta, leitura saudável, ausência de
limite/bloqueio emergencial e de envio/recuperação/configuração em andamento.
Reutilizar revisão de T08b com IDs, configuração e centavos anteriores/atuais,
exclusões explícitas e inclusão inteira bloqueada por item inválido/legado.
Catálogo guest fornece só Products ativos: ausência bloqueia; available é a fonte
operacional. Não inferir produto por nome nem substituir seleção por defaults.
Adicionar ao carrinho relê contexto/catálogo da mesma visita; mudança de conteúdo
exige nova revisão, bloqueio/revogação/falha preservam draft e não enviam pedido.
Inclusão única preserva draft/configurações distintos; Enviar é ação separada com
nova intenção e recuperação T05b. API revalida política/disponibilidade/limite.
Nenhum snapshot, Payment ou ledger histórico é alterado. Sem reserva entre GETs
e envio, persistência de drafts, novo pagamento, Web POS ou ganho humano medido.

T08c acrescenta guest_policy.table_ordering_enabled no payload autorizado de contexto/QR: true somente se a mesa não estiver bloqueada e guest_ordering_mode não for DISABLED, a partir da mesa travada pela leitura existente. É projeção de leitura; não substitui política emergencial, validade da ocupação/sessão ou validação transacional de mutations. Repetição exige true explícito; campo ausente bloqueia. Contexto/cardápio continuam consultáveis quando pedidos estão pausados.

### T09a / UX-14 — quantidade no rascunho guest
Toques repetidos e inclusão de rodada agrupam somente Product ID, variant ID,
conjunto de option IDs e observação exatamente iguais. A ordem dos IDs de opções
não muda a configuração; a nota não é normalizada. Edição preserva quantidade e
reagrupa somente a configuração idêntica. Limite por linha agrupada: 1–99;
excedê-lo rejeita toda a inclusão/edição, preserva o draft e informa o problema,
sem truncar, descartar unidades ou confirmar automaticamente.
Controles +/− acessíveis ajustam quantidade; zero remove a linha. Aumento exige
catálogo atual/disponível, configuração válida e visita aberta sem bloqueio de
mesa/Venue/consumo. Diminuição/remoção permitem corrigir item indisponível ou
rascunho obsoleto, mas ficam bloqueadas durante intenção pendente/envio/revisão.
Nenhum controle altera o payload pendente: replay usa a intenção original T05b.
API segue revalidando catálogo, autorização e limite no envio. Histórico,
Payments e ledger não são editados. Fora de escopo: busca/categorias de T09b,
criação automática de comanda, persistência de draft e ganhos humanos medidos.

### T09b / UX-15 — descoberta no catálogo guest
API guest projeta Product.category já persistida, sem inferir categorias pelo
routing nem alterar catálogo/domínio. UI reutiliza a apresentação de categorias
do Atendimento; ausência de categoria pertence a Outros. Todos inicia selecionado,
para preservar descoberta de qualquer produto. Categoria filtra por apresentação;
busca por nome ignora acentos/caixa e espaços nas bordas, pesquisando o catálogo
inteiro. Limpar busca volta à categoria selecionada; selecionar categoria limpa
busca. Categoria removida após atualização retorna a Todos. Resultado vazio tem
feedback e contagem acessível; filtros não mudam Product IDs, configurações,
quantidades, draft, histórico ou intenções pendentes.
Acesso explícito ao Pedido atual no catálogo leva ao draft existente sem enviar,
criando comanda nem resolver QR novamente. Nenhum item se torna vendável pela
busca: indisponibilidade, dados obsoletos, bloqueios de mesa/Venue/consumo, visita
revogada e intenção pendente conservam os guards T05b/T09a. Catálogo vazio tem
mensagem própria. Fora de escopo: recomendação/fuzzy matching, categorias novas
no banco, criação automática da comanda, persistência de draft e medição humana.

Descoberta T09b: Pedido atual permanece visível, desativado com carrinho vazio,
para que a primeira inclusão não desloque os produtos durante toques repetidos.

## Fechamento MVP contratado — 14/10/2026

O MVP usa Table/Zone textual e GuestSession do dispositivo. FloorPlan,
TablePlacement/arrasto/versionamento e TableGroup, assim como join por código
curto, QR dinâmico, NFC e claim por perfil autenticado, permanecem roadmap
explícito: os critérios originais são preservados e vinculados em closeout.md.
Customer opcional no domínio não comprova login/claim guest por perfil.

Navegação contínua usa três atalhos persistentes para regiões montadas
Cardápio/Pedidos/Conta; trocar região rola e focaliza, sem mutation ou perda
de draft/intent. Cardápio continua montado após qualquer pedido. Status por
item projeta NEW/ACCEPTED como Recebido, PREPARING como Preparando e
READY/PICKED_UP como Pronto / chegando. DELIVERED permanece Entregue,
CANCELLED permanece Cancelado, desconhecido é Estado indisponível; nunca
inferir entrega ou tempo. Conta usa a projeção da própria Tab.

Quick-add mantém revisão de variantes e grupos com escolha obrigatória.
Grupos somente opcionais não exigem painel intermediário; defaults válidos
entram no rascunho e podem ser alterados em Editar antes de Enviar.
