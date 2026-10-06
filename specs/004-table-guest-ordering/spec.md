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
- QR físico resolve Table, não Tab;
- identificadores públicos não são sequenciais/adivinháveis;
- GuestSession é revogável;
- pedidos `GUEST` entram na mesma pipeline de fulfillment dos pedidos do staff.

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
- throughput/giro por mesa.

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

Após scan válido, UI mostra a mesa/área resolvida e cria ou recupera GuestSession.

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

Guest adiciona itens e confirma Order com `source=GUEST`.

Order entra na mesma fila/estação de Bar/Cozinha usada por pedidos do staff.

### GUEST-008 — Acompanhar

Guest vê apenas informações autorizadas da própria Tab:

- pedidos;
- estados relevantes;
- total/exposure apropriado;
- ações permitidas.

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
