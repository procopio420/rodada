# Spec 027 — Início de atendimento, ownership e abertura contextual de comandas

**Status:** Implementação concluída; homologação automatizada por head em `evidence.md`. Piloto observado e medição real no estabelecimento pendentes.
**Data:** 2026-10-12
**Produto:** Rodada / piloto Bar do Aderlan
**Superfícies:** Atendimento Android (canônico), Atendimento Web (companion, sem pagamento), Gerência (visibilidade).
**Relacionado:** Specs 001, 003, 004, 008, 009, 014, 024, 026; ADR 0004 e ADR 0018.

## 1. Problema e resultado esperado

Hoje, "ocupar mesa", "associar comanda", "abrir comanda", "assumir tarefa" e "fazer pedido" aparecem como operações separadas e confusas. No Android, a ação central "Pedir" abre nova comanda sem herdar mesa; em Mesas, as comandas são texto e não navegação direta. No Web, a ocupação e associação ocorrem em controles separados. A auditoria UX-11/12/18/19 na Spec 026 registra o problema.

**Objetivo:** um garçom toca numa mesa disponível e em uma ação explícita inicia atendimento; o Rodada cria a ocupação e atribui responsabilidade inicial automaticamente. Em seguida, "Nova comanda" ou seleção de uma comanda existente leva diretamente ao pedido com destino inequívoco.

**Meta de ações de negócio** (exclui carregamento, espera de rede e digitação opcional):
- Da ficha de mesa AVAILABLE: **1 toque** em "Iniciar atendimento" para ativar ocupação, sem modal.
- Da ocupação ativa sem comanda: **1 toque** em "Nova comanda" + **1 confirmação** ("Abrir e pedir"); nome é opcional.
- Da mesa ocupada com comandas: **1 toque** em uma comanda para entrar no cardápio; não passar pela lista global.
- A abertura da comanda na mesa não exige CPF, Customer cadastrado, covers ou ownership exclusivo.

## 2. Vocabulário canônico e responsabilidade

| Primitiva | Responsabilidade | Proibição |
| --- | --- | --- |
| `Table` | Mesa física, QR permanente, status e localização | Não recebe ledger nem `responsible_staff` permanente |
| `TableOccupancy` | Visita física atual da mesa; sessão de serviço | Não é comanda nem pagamento |
| `OccupancyResponsibility` (projeção) | `StaffMember` responsável **pela ocupação atual**, opcional | Não concede exclusividade para lançar pedidos |
| `Tab` | Unidade financeira de uma pessoa ou grupo | Não é sinônimo de mesa, cliente ou garçom |
| `TabOccupancyAssignment` | Localização atual de uma Tab na ocupação | Não transfere ledger |
| `DispatchTask.claimed_by` | Dono de uma tarefa específica, p.ex. chamar garçom | Não altera responsável da ocupação |

**Claim de mesa na UX = claim da ocupação ativa.** A atribuição inicial ocorre automaticamente quando **staff** inicia a ocupação; ocupação criada pelo **guest/QR** pode ter responsável nulo. Qualquer staff autorizado pode atender/pedir em ocupação assumida por colega. Fazer pedido, entregar, cobrar ou abrir Tab não transfere ownership implicitamente.

## 3. Invariantes de produto e de dados

1. Todo `Order` continua ligado a uma única `Tab`; a mesa nunca tem ledger.
2. Uma `Table` tem no máximo uma `TableOccupancy` ativa; ocupação aceita 0..N Tabs.
3. `POST service/start` **não** cria `Tab`, `Order`, `Payment`, `Customer`, `PartySizeObservation` nem sessão guest. O estado inicial tem zero comandas e exposição financeira zero por ausência de Tab, não por saldo agregado inventado.
4. A primeira abertura por staff atribui o ator como responsável inicial **apenas se foi o criador da ocupação**. Guest/QR não escolhe funcionário.
5. A ocupação mantém responsável opcional; transferência/reclaim só ocorre por comando explícito, com versão, autorização e auditoria.
6. Iniciar atendimento em mesa ocupada **nunca cria segunda ocupação nem substitui responsável**. A UI abre contexto atual ou exige claim explícito.
7. Abertura de comanda contextual cria `Tab` e `TabOccupancyAssignment` numa **mesma transação**: nunca sobrar Tab órfã caso o vínculo falhe.
8. A Tab não pode estar associada simultaneamente a duas ocupações ativas. Vínculo de Tab existente em outra mesa exige `move_tab_location` da Spec 009, não `assign_tab` cego.
9. Ações que não completaram no servidor não são apresentadas como sucesso, inclusive após timeout, retorno ao app, reload ou troca de conexão.
10. Fechar/pagar última Tab não encerra `TableOccupancy`; liberar a mesa continua ação explícita que revoga acesso guest e inicia ciclo `DIRTY -> CLEANING -> AVAILABLE`.
11. Pedido feito por outro garçom retém `Order.confirmed_by`; responsável da ocupação permanece inalterado.
12. Autorização sempre por sessão, Venue e capability no servidor; nome/apelido, número da mesa e código visual não são autenticação.
13. A exibição guest nunca revela nome ou identidade operacional do responsável; guest enxerga sua própria autorização da Spec 004.
14. NFC, QR de mesa, `Customer` e `TabIdentifier` não são recriados no start staff.

## 4. Jornada principal no Android e Web

### A. Mesa disponível

**Card/lista:** "Mesa 12 · Varanda · Disponível" + CTA primário **Iniciar atendimento**. Sem pedir quantidade de pessoas, nome, PIN extra, comanda ou escolha do responsável.

1. Garçom toca `Iniciar atendimento`; CTA fica ocupado com estado de envio e intenção durável.
2. API devolve snapshot canônico da ocupação com `responsible_staff = ator`.
3. UI exibe **Mesa 12 · Em uso · Atendimento: você · 0 comandas**; ações: **+ Nova comanda**, **Vincular comanda existente** (secundária). O garçom continua na ficha da mesa.
4. `+ Nova comanda` abre folha curta "Nome ou apelido (opcional)" com botão **Abrir e pedir**. Nunca exige busca por cliente cadastrado. Pode sugerir clientes existentes sem bloquear o fluxo.
5. Após confirmação, o servidor cria Tab + assignment atômicos; o Android/Web navega ao **cardápio da Tab**, com cabeçalho persistente "Mesa 12 · Ana/Comanda sem nome", e só então o primeiro pedido é montado e confirmado.

Com o serviço de mesas habilitado e permissões `table.manage` + `tab.open`, a abertura global de comanda do Atendimento Web exige o **Nome da Comanda** e escolhe uma mesa AVAILABLE. A CTA abre um diálogo com as mesas disponíveis e confirma por um comando próprio atômico `service/open-tab`; ele cria ocupação, responsabilidade inicial, Tab e vínculo juntos. Sem o rollout ou essas permissões, o Atendimento preserva a abertura legada sem mesa; o contrato simples de `service/start` continua sem criar Tab e o cliente nunca faz duas mutations silenciosas em paralelo.

### B. Mesa ocupada

Mover comanda também aceita mesa AVAILABLE por `MOVE_LOCATION` com `table_id`, exigindo `tab.move` e `table.manage`. Uma transação inicia a ocupação, atribui responsabilidade inicial e move a mesma Tab, preservando ledger e ocupação de origem. Replay retorna o resultado anterior mesmo quando o destino já ficou ocupado. Estados DIRTY/CLEANING/OUT_OF_SERVICE são rejeitados. UUID e motivo não são exigidos do operador.

O botão “Mover comanda” abre diretamente o diálogo de movimento; nele, o operador pode selecionar outra mesa já ocupada. Usar as superfícies quentes e destaque âmbar de Contas, preservando foco e alvos de toque.

No Atendimento Web móvel, Mesas apresenta uma lista compacta: nome, estado e contagem de comandas abertas. Tocar na mesa expande suas comandas e ações; os demais detalhes ficam recolhidos. Abrir comanda é a ação principal; movimentação e organização são secundárias. Não exibir UUID completo nem formulário de pessoas/motivo nessa superfície. Contagem de comandas não representa contagem exata de pessoas. Liberação continua confirmada e não encerra comandas.

O diálogo global “Qual mesa o cliente está?” também lista mesas OCCUPIED com ocupação ativa, identificadas como “Em uso”. A seleção abre uma nova Tab pelo comando `occupancies/{id}/tabs/open`, com a geração observada, sem criar outra ocupação nem alterar o responsável. Mesas DIRTY, CLEANING e OUT_OF_SERVICE não aparecem nesse diálogo.

Card "Mesa 12 · Em uso · João · 3 comandas". Tocar na mesa abre lista de comandas *clicáveis* com nome/identificador desambiguador, status e destino; selecionar uma abre pedido diretamente, sem pesquisa global.

- `+ Nova comanda nesta mesa`: cria nova Tab e assignment na ocupação ativa; não cria outra ocupação.
- `Vincular comanda existente`: busca por nome/código e mostra localização atual antes de confirmar. Se já vinculada em outra mesa, oferece **Mover comanda** (Spec 009); não tenta `assign_tab` e não altera ledger ocultamente.
- `Atendimento: João`: ação secundária "Assumir atendimento" com texto "João está responsável; você também pode fazer pedidos sem assumir". Claim não é gate para pedir.

### C. QR iniciou primeiro

Uma ocupação criada por `DIRECT` (Spec 004) pode ficar `OCCUPIED` e `responsible_staff = null`. O primeiro garçom que abre a ficha vê **Atendimento sem responsável → Assumir atendimento**; não ocupa novamente nem cancela sessão guest. O garçom pode abrir a comanda ou registrar pedido autorizado mesmo sem assumir.

### C.1 Destaque operacional de mesa sem responsável (P0 do piloto)

Uma mesa pode estar `OCCUPIED` sem `responsible_staff`, especialmente se o cliente iniciou pela modalidade `DIRECT` no QR. **Isso não deve ficar invisível aos garçons**.

**Critério de visibilidade derivado de fonte canônica, sem criar tarefa financeira ou claim fictício:**

| Situação da ocupação ativa | Exibição staff | Prioridade |
| --- | --- | --- |
| Sem responsável e ainda sem pedidos confirmados | Etiqueta discreta `Sem responsável` na ficha/cartão de Mesa; CTA `Assumir atendimento` | Informativa, não entra em fila de urgência |
| Sem responsável e existe ao menos um pedido `source=GUEST` confirmado nessa ocupação | Destaque persistente **`Pedido via QR · Sem responsável`** no painel `Agora/Atendimento` e cartão da Mesa; apresentar mesa/zona, quantidade de pedidos guest pendentes de acompanhamento e tempo desde primeiro pedido pertinente; CTA `Ver mesa` e `Assumir atendimento` | Atenção operacional visível sem depender de navegar até a mesa |
| Mesmo caso, com item pronto aguardando entrega | Conservar destaque e incluir estado **`Pedido pronto`** derivado da fila canônica de produção/entrega, sem antecipar readiness | Maior prioridade de ordenação; não duplicar despacho |
| Um funcionário assume explicitamente a ocupação | Retirar o aviso **`Sem responsável`** em Android/Web/Agora; manter pedidos e seus estados intactos | Sai da fila de ocupações não atribuídas |
| Ocupação liberada/encerrada ou antiga `generation` | Remover o aviso dessa sessão; jamais associá-lo à próxima ocupação da mesa | Nenhum aviso órfão |

**Regras:**
1. O evento relevante é **pedido guest confirmado** (não apenas QR lido, carrinho montado ou Tab aberta). O aviso de atenção não cria `TableOccupancy`, Tab, Order, `DispatchTask` nem novo evento financeiro.
2. Calcular aviso por `occupancy_id`, `generation`, owner nullable e pedidos canônicos; publicar invalidação realtime após commit de confirmação/claim/liberação e reconstruir por GET para reconexão/reload. Nunca confiar no cliente para inferir `source=GUEST` ou readiness.
3. **Uma ocupação = um destaque agregado**, mesmo com diversos pedidos e replays de confirmação. Mostrar contagem e antiguidade, não spam de banners/toasts nem duplicação de tarefas; ordenar por pronto/antiguidade sem inventar SLA.
4. Claim é **ação do funcionário**, nunca disparado pela simples visualização, pedido, entrega ou toque em `Ver mesa`. A equipe pode cuidar de itens e comandas sem claim; não atrasar produção/expedição por ausência de owner.
5. Prioridade e destaque só são visíveis a funcionários do **mesmo Venue** com acesso operacional; dados internos de staff/filas não aparecem no QR guest. UI não pode usar apenas cor: sempre renderizar texto + ícone/estado acessível.
6. Em concorrência (A assume, B observa antiga versão), refetch remove aviso; claim repetido/conflitante segue CAS do contrato 6.3. Alertas não sobrevivem à liberação nem migram para nova geração.

**Exemplo:** Cliente lê QR da Mesa 12 e confirma cervejas. A equipe vê `Mesa 12 · Pedido via QR · Sem responsável`, pode tocar `Ver mesa` ou `Assumir atendimento`. Depois que Ana assume, `Sem responsável` desaparece imediatamente após confirmação/releitura; os pedidos não são recriados e a cozinha/bar continuam normalmente.

### D. Balcão / consumo em pé

Ação separada `Nova comanda · Sem mesa` continua possível. Não cria `TableOccupancy` artificial, não atribui responsável de mesa e utiliza `Tab.service_point` apenas quando houver contexto legítimo.

### E. Mesa indisponível

| Status canônico | CTA permitido |
| --- | --- |
| `AVAILABLE` | Iniciar atendimento |
| `OCCUPIED` | Ver comandas, Nova comanda, Atendimento, Liberar mesa (ação protegida) |
| `DIRTY` | Iniciar limpeza; **não** permitir start |
| `CLEANING` | Concluir limpeza; **não** permitir start |
| `OUT_OF_SERVICE` | Sem início; ação de recuperação autorizada na gestão |

Não reinterpretar `DIRTY` como mesa disponível; não concluir limpeza automaticamente.

## 5. Projeção da ficha / seleção de comandas

O snapshot da mesa retorna `table_id`, `label`, `status`, `zone`, `active_occupancy` (ID, generation, timestamps, versão de responsabilidade, responsável opcional e Tabs ativas). A projeção staff destinada a Mesas/Agora deve incluir `unassigned_service_attention` derivado (`NONE` | `UNASSIGNED_NO_ORDER` | `UNASSIGNED_GUEST_ORDER` | `UNASSIGNED_READY`), `unassigned_guest_order_count` e `oldest_unassigned_guest_order_at` quando aplicáveis. Essa projeção não entra no payload guest. Atualização é por leitura canônica + SSE de invalidação, sem objeto de alerta independente. Cada comanda listada precisa de `tab_id`, `display_label` ou rótulo humano desambiguador, `state`, localização atual e `opened_at`. Se exibir saldo, obtê-lo da projeção financeira canônica, jamais somar valores de linhas do navegador.

Duas pessoas chamadas "João" na mesma mesa precisam de contexto adicional (rótulo + identificador operacional não secreto + hora de abertura). Não usar UUID truncado como prova de autorização ou código de guest join. Identificador de exibição não concede acesso guest.

UX: o cabeçalho da comanda sempre informa **qual Tab receberá o pedido** e sua mesa/ServicePoint atual; mudar localização é ação própria. Rascunho não pode ser perdido ao trocar de ficha/comanda; resultados ambíguos permanecem em revisão.

## 6. Contratos API propostos (aditivos, não existentes hoje)

**Rotas lógicas abaixo relativas à API canônica, no mesmo padrão das rotas `hospitality/*` existentes; Web usa o gateway restrito `/api/attendance/*` quando autorizado.** As rotas e os novos campos precisam ser implementados; exemplos são contratos desejados, não endpoints já disponíveis.

### 6.1 Iniciar mesa

`POST /hospitality/tables/{table_id}/service/start/`

```json
{ "idempotency_key": "uuid-v4-do-comando" }
```

**201** (novo) / **200** (replay da mesma intenção):
```json
{
  "table_id": "uuid",
  "table_status": "OCCUPIED",
  "active_occupancy": {
    "id": "uuid", "generation": 3, "responsible_staff_id": "uuid",
    "responsibility_version": 1, "tab_count": 0
  },
  "replayed": false
}
```

Permissão `table.manage` do Venue, já presente no papel-base STAFF; autenticação obrigatória. Servidor faz `transaction.atomic`, bloqueia Table (`select_for_update`), verifica estado e unicidade de ocupação, cria ocupação, atribui ator e emite `table.occupied` + `occupancy.responsibility_assigned` em auditoria. Publicação realtime **só após commit** (outbox/transaction.on_commit). Lock order estável: registro da intenção -> Table -> Occupancy -> Tab. A intenção antecede locks de domínio para serializar a mesma chave inclusive quando ela é enviada a dois destinos distintos.

Se mesa já ocupada por outro comando: **409 `OCCUPANCY_ALREADY_ACTIVE`**, com `occupancy_id`, `responsible_staff_id` e `responsibility_version` (sem transferir responsabilidade); cliente lê snapshot atual e abre a mesa. Reenvio com mesma chave+payload da intenção previamente confirmada responde 200 com o mesmo resultado, sem efeitos novos. Chave repetida com payload diferente: 409 `IDEMPOTENCY_CONFLICT`. `DIRTY/CLEANING/OUT_OF_SERVICE`: 409 `TABLE_NOT_AVAILABLE` com estado canônico.

### 6.2 Abrir a primeira comanda numa mesa disponível

`POST /hospitality/tables/{table_id}/service/open-tab/`

```json
{ "idempotency_key": "uuid-v4-do-comando", "display_label": "Nome da Comanda" }
```

Exige `table.manage` e `tab.open`. `display_label` não pode ser vazio. Em uma transação, bloqueia a mesa AVAILABLE, inicia a ocupação com o staff responsável, cria a Tab e registra o vínculo. A repetição da mesma intenção devolve os mesmos IDs; mesa já ocupada ou indisponível retorna conflito sem criar efeito parcial.

### 6.3 Abrir uma comanda na ocupação

`POST /hospitality/occupancies/{occupancy_id}/tabs/open/`

```json
{
  "display_label": "Ana",
  "customer_id": null,
  "expected_generation": 3,
  "idempotency_key": "uuid-v4-distinto-do-start"
}
```

`display_label` opcional; validação por Venue e capability `tab.open`. Criação de `Tab` e `TabOccupancyAssignment` na mesma transação; verificar ocupação ativa, generation da Table, versão/estado atual e inexistência de release concorrente. Retornar **201** com `tab_id`, `occupancy_id`, `table_id`, `display_label`, `state` e contexto de destino (ou **200** em replay). Rejeitar `OCCUPANCY_RELEASED`, `STALE_TABLE_GENERATION`, `CUSTOMER_NOT_FOUND_OR_OTHER_VENUE` conforme validações. Reutilizar `open_tab` e associação existentes apenas dentro de serviço orquestrador atômico, sem chamada HTTP de API para API.

### 6.3 Assumir ou transferir responsabilidade

`POST /hospitality/occupancies/{occupancy_id}/responsibility/claim/`

```json
{
  "idempotency_key": "uuid-v4",
  "expected_responsibility_version": 1,
  "mode": "TAKE_OVER"
}
```

Modo `CLAIM_UNASSIGNED` usado para responsável nulo; `TAKE_OVER` quando existe colega. Versão deve corresponder à atual em lock; 409 `RESPONSIBILITY_CONFLICT` retorna versão e responsável atuais. Se já é o próprio ator: retornar estado canônico sem novo evento e sem incrementar versão. Uma transferência real registra de/para, ator, horário, provenance da sessão/dispositivo e razão opcional conforme política. Permissão `table.manage` em P0; ações de outra equipe continuam permitidas se tiverem `order.confirm`/`tab.open`.

`GET /hospitality/tables/{table_id}/` (ou extensão da listagem atual) precisa projetar os campos para ambos os clientes. A consulta de recuperação de intenção deve ser canônica/segura; retry usa sempre a **mesma** chave e payload. Novas intenções não devem ser fabricadas até resolução do resultado anterior.

## 7. Semântica de concorrência, idempotência e rede

- Idempotência **obrigatória** para start, tab open e claim. Persistir uma intenção keyed por Venue + ação + ator + chave com fingerprint do payload e destino, status e IDs/resultado suficientes para replay; a implementação retém registros sem expiração automática; mesma chave em outro payload => conflito. Definir janela durável de retenção que cubra recuperação do turno (mínimo 48h), sem reexecução silenciosa após expiração.
- Staff A e B enviam start ao mesmo tempo: apenas uma ocupação; o vencedor torna-se responsável inicial. O outro recebe conflito/atualiza ficha, sem assumir automaticamente. Índice de ocupação ativa e lock garantem isso em PostgreSQL.
- Staff A inicia e fica offline após commit: retomar consulta/reenvio **da mesma intenção**; nunca criar mesa/comanda duplicada. Se estado é desconhecido, exibir "Verificando atendimento" e preservar intent.
- Staff A libera mesa enquanto B abre Tab: serializar; ou Tab+assignment são ambos confirmados antes do release, ou nenhum é criado e B recebe conflito. Nunca deixar comanda financeira nova sem vínculo por corrida.
- Dois claims concorrentes usam `responsibility_version` e CAS; segundo vê 409, não derruba ownership silenciosamente.
- Realtime/SSE é invalidação/projeção e **não** confirmação da mutation; ler API como fonte de verdade. Erro de rede e snapshot antigo bloqueiam comandos arriscados, mas não apagam rascunhos.
- Requer teste real de concorrência PostgreSQL; SQLite/fixtures e testes visuais não bastam.

## 8. Auditoria e segurança

Eventos mínimos: `table.occupied`, `occupancy.responsibility_assigned`, `occupancy.responsibility_transferred`, `tab.opened`, `table_occupancy.tab_assigned`. Guardar `actor_id`, Venue, Table, Occupancy, Tab quando houver, event/intent ID, horário, anterior/novo e origem staff/guest. Não colocar nome do garçom ou código de acesso guest em eventos públicos/SSE.

Nenhum comando de claim concede capability financeira ou autoriza tab de outro Venue. Fechamento, split/merge, pagamento parcial, guest policy e gestão de limites continuam com suas specs, permissões e trilhas.

## 9. Contratos de compatibilidade e rollout

- Manter `occupy/` e `occupancies/{id}/tabs/` legados enquanto todos os clientes forem migrados; a nova operação não pode introduzir semântica contraditória. Testar convivência (Android, Web, QR e chamadas legadas).
- Migração de `TableOccupancy` adiciona campos nullable de responsável/tempo e versão com default seguro; ocupações antigas/guest ficam sem responsável **sem backfill especulativo**. Um garçom pode assumi-las explicitamente.
- Atendimento Web precisa de rota nova expressamente permitida na allowlist, sem expandir pagamento/cash/refund.
- Android nativo e Web devem mostrar a mesma ocupação/Tab; Web não promete capacidade financeira que não possui.
- O painel Agora e as fichas de mesa usam a mesma projeção staff de `unassigned_service_attention`; uma notificação visual não altera `DispatchTask` e não deve exigir um polling especial por cartão.
- Preferir rollout com flag por Venue, fixture isolada, validação do piloto e rollback de UI/rota. Reverter feature não apaga histórico de ocupações nem vínculos.

## 10. Fora de escopo desta primeira implementação

- Claim exclusivo que bloqueie pedidos de outros garçons; distribuição automática por desempenho, zona ou proximidade; escalas/turnos inteligentes.
- Transformar ocupação em conta compartilhada ou criar Customer obrigatório.
- Floorplan 2D, NFC novo, reconhecimento facial, geofencing.
- Autofechar mesa quando Tab zera ou bloquear mesa até todas as comandas serem pagas (política nova requer spec).
- "Cancelar início acidental" com `OCCUPIED -> AVAILABLE` sem limpeza: **requer regra separada**, com verificação rigorosa de ausência de Tabs/sessões guest/interações; P0 usa release/cleaning existentes. Não introduzir bypass de revogação por conveniência.
- Pagamento Web, providers e processo fiscal.

## 11. Decisões adotadas e pontos de validação em campo

**Padrões propostos para o piloto:** responsável inicial automático por staff que inicia; opcional em ocupações guest; claim transferível, não exclusivo; nome de comanda opcional; Tab contextual atômica; botão de start sem modal.

Validar com garçons reais: rótulos "Atendimento: João" vs "Responsável: João", distinção "Nova comanda" vs "Novo pedido", número de comandas por mesa, necessidade de ação explícita de takeover, mesas móveis e como corrigem abertura equivocada. Se a observação contradizer este contrato, alterar a spec antes da implementação adicional.

**Evidência, tarefas e testes:** `acceptance.md`, `plan.md`, `tasks.md`. Implementação e limites de validação registrados em `evidence.md`; sem homologação do piloto.

## Refinamento de recuperação Web

O Atendimento Web persiste, por Venue/staff/sessão, o destino da Tab, linhas e personalizações do rascunho e, antes do POST, a chave e o payload congelado da confirmação. Reload restaura o destino original e oferece `Verificar mesmo pedido`; nunca gera nova chave para uma resposta desconhecida. Falha de storage bloqueia envio. Registros de outra sessão são preservados e bloqueiam novos pedidos até reconciliação autorizada. Apenas sucesso ou rejeição terminal 400/404/409/422 liberam a intenção; 401/403/5xx não provam ausência de commit. O catálogo atual revalida rascunhos ainda não enviados; replay usa exatamente o payload original.

A ação global Android passa a `Nova comanda`, em duas linhas, mantendo geometria e alvos da Spec 023; o nome explicita que a abertura global não herda mesa.

## Rollout por estabelecimento

`Venue.table_service_enabled` inicia falso, sem backfill de responsáveis. Gerência com `venue.configure` ativa/desativa por comando auditado, versionado e idempotente em `/management/table-service-rollout/`. O rollback bloqueia apenas novas intenções start/open/claim; replays já confirmados continuam disponíveis e nenhuma ocupação, Tab, saldo ou QR é alterado. Comandos já admitidos podem terminar durante desativação. Mesas staff expõem a flag; clientes desativados conservam ocupar/vincular/liberar/limpar legados. Piloto real depende de ativação explícita e observação no estabelecimento; testes isolados ativam apenas seus próprios Venues.

Mover comanda entre mesas exige `tab.move`, confirmação origem/destino e `MOVE_LOCATION` versionado da Spec 009. A intenção durável congela ocupação destino, versão da Tab e chave. Atendimento Web permite somente esse kind no endpoint de operações, rejeitando campos e kinds financeiros.
