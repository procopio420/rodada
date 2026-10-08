# Spec 004 — Table Ops + Guest Ordering

**Status:** Draft for implementation after Core POS foundation

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
