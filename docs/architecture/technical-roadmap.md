# Roadmap Técnico — Rodada

**Status:** plano de execução  
**Fonte de verdade de produto:** specs em `specs/`  
**Objetivo:** sair de documentação/protótipo e chegar a um piloto operacional real no Bar do Aderlan sem construir módulos fora de ordem.

> O roadmap por specs descreve **o que** o produto precisa fazer. Este documento descreve **em que ordem técnica devemos construir**, quais dependências precisam existir antes de cada etapa e qual evidência prova que uma fase realmente terminou.

## Regra principal

Não considerar uma feature “implementada” porque existe tela, mock, rota ou componente visual.

Uma capability só conta como pronta quando o fluxo relevante possui:

1. regra de domínio no backend;
2. persistência/migration quando aplicável;
3. API/contrato estável;
4. UI da superfície correta;
5. autorização server-side;
6. auditoria quando a mutation for relevante;
7. testes alinhados aos critérios de aceite;
8. comportamento de erro/retry definido;
9. observabilidade mínima;
10. evidência end-to-end em ambiente executável.

## Estado de partida

Hoje o repositório contém specs, ADRs, design system e protótipo navegável. Os diretórios `apps/api` e `apps/web` ainda descrevem a arquitetura alvo; o aplicativo Android de Atendimento ainda precisa ser criado.

Portanto, o primeiro trabalho não é “adicionar mais telas”. É criar um walking skeleton real e provar uma venda ponta a ponta.

---

# Milestone 0 — Engineering foundation

## Objetivo

Criar uma base executável na qual todas as specs seguintes possam ser implementadas sem retrabalho estrutural.

## Entregas

### Backend

- Django + Django REST Framework em `apps/api`;
- PostgreSQL como banco principal;
- estrutura modular inicial:
  - `venue`;
  - `catalog`;
  - `ordering`;
  - `fulfillment`;
  - `billing`;
  - `cash`;
  - `audit`;
- settings por ambiente;
- migrations;
- health/readiness endpoint;
- OpenAPI gerado a partir da API;
- IDs públicos não sequenciais onde exposição externa exigir;
- dinheiro representado em centavos, nunca `float`.

### Web/PWA

Criar implementação Next.js real para as superfícies web:

- Rodada Cozinha;
- Rodada Bar;
- Rodada Cliente;
- Rodada Gerência.

Compartilhar tokens, contratos e primitives; não transformar tudo em uma única aplicação com telas escondidas por role.

### Android

Criar `apps/attendance-android`:

- Kotlin;
- Jetpack Compose;
- client HTTP tipado;
- armazenamento seguro de sessão;
- design tokens equivalentes ao design system;
- arquitetura preparada para SDK de Tap on Phone.

### Dev environment

- Docker Compose para Postgres e dependências locais;
- seed mínimo de Venue, staff e catálogo;
- comandos únicos para bootstrap;
- lint + formatter;
- testes backend;
- testes frontend;
- testes Android;
- CI em pull request.

## Gate de saída

Um desenvolvedor novo deve conseguir clonar o repo, subir a stack, autenticar em ambiente local e enxergar um Venue seeded sem configuração manual fora do README.

---

# Milestone 1 — Walking skeleton: uma venda real ponta a ponta

**Specs principais:** 001 Core POS, partes mínimas da 006 Payments.

## Objetivo

Provar primeiro o fluxo que define se o Rodada é um PDV de verdade:

```text
staff entra
  -> abre Tab
  -> lança pedido
  -> Bar/Cozinha recebe
  -> item fica pronto
  -> saldo da Tab existe no ledger
  -> pagamento é registrado
  -> Tab fecha
```

## Backend P0

Implementar primeiro:

- Venue;
- StaffMember + autorização mínima;
- FulfillmentStation;
- Product;
- ProductAvailability;
- Tab;
- Order;
- OrderItem;
- Charge;
- Payment;
- CashShift mínimo;
- AuditEvent;
- snapshot de preço no OrderItem;
- confirmação transacional de pedido;
- criação idempotente de Charge;
- cálculo canônico de saldo/exposure;
- fechamento de Tab apenas com saldo compatível com a política.

Não implementar mesa como requisito do pedido. A primeira Tab precisa funcionar sem Table.

## Atendimento Android P0

Fluxo mínimo:

- login;
- lista/busca de Tabs abertas;
- abrir Tab anônima ou com apelido;
- adicionar produtos;
- confirmar pedido;
- visualizar consumo e saldo;
- receber dinheiro;
- registrar maquininha externa;
- fechar Tab.

Tap on Phone entra depois que o ledger e os estados de pagamento estiverem provados.

## Bar/Cozinha P0

- fila por estação;
- novo pedido em tempo útil;
- aceitar/preparar/pronto;
- indisponibilizar e reativar Product;
- mesma disponibilidade refletida no Atendimento;
- nenhuma obrigação de marcar “peguei”/“entreguei”.

## Definition of Done

O milestone só termina quando um teste E2E provar:

1. uma Tab sem mesa é aberta;
2. pedido com itens de Bar e Cozinha é confirmado;
3. cada estação recebe apenas seus itens;
4. um Product indisponível é bloqueado server-side;
5. Charges são gerados uma única vez;
6. pagamento parcial altera o saldo corretamente;
7. pagamento final permite fechar a Tab;
8. AuditEvents permitem reconstruir quem executou mutations relevantes.

---

# Milestone 2 — Realtime operacional

**Specs principais:** 001 + 003.

## Objetivo

Retirar polling/manual refresh do fluxo operacional e começar a coordenar trabalho em tempo real.

## Entregas

- Redis;
- canal WebSocket/realtime;
- outbox/event publication idempotente para fatos operacionais;
- atualização em tempo real de:
  - novos pedidos;
  - status de fulfillment;
  - ProductAvailability;
  - saldo/pagamento da Tab;
- reconnect com revalidation pela API;
- indicador explícito de estado stale/offline.

## Dispatch P0

Implementar primeiro a parte útil sem hardware:

- Zone;
- ServicePoint;
- DispatchTask;
- SERVICE_REQUEST;
- BILL_REQUEST;
- DELIVERY criado idempotentemente a partir de item pronto quando aplicável;
- prioridade/SLA;
- fila operacional;
- DeliveryRun básico.

Telemetria BLE/presença e inferência avançada vêm depois do fluxo básico funcionar.

## Gate de saída

Durante uma execução com Atendimento + Bar/Cozinha abertos, nenhuma mutation normal exige refresh manual para aparecer na outra superfície.

---

# Milestone 3 — Floor, Table Ops e Guest Ordering

**Spec principal:** 004.

## Objetivo

Adicionar contexto físico sem destruir a independência financeira de Tab.

## Ordem

### Floor/Table

- FloorPlan;
- Zone/ServicePoint integrados ao mapa;
- Table;
- TablePlacement;
- optimistic locking de posição;
- TableOccupancy;
- estados AVAILABLE / OCCUPIED / DIRTY / CLEANING / OUT_OF_SERVICE;
- associação opcional Tab ↔ TableOccupancy;
- múltiplas Tabs na mesma ocupação.

### Guest Access

- QR opaco por Table;
- GuestSession;
- access generation;
- short code;
- TabIdentifier;
- bloqueio imediato de guest ordering;
- revogação de sessão antiga após liberação/limpeza.

### Guest PWA

```text
scan QR
  -> resolve mesa/ocupação
  -> cria ou entra em Tab
  -> vê catálogo disponível
  -> pede
  -> acompanha
  -> vê conta
```

## Gate de saída

Provar E2E que duas Tabs independentes conseguem consumir na mesma mesa, uma delas pode pagar/fechar e isso não libera a mesa nem interfere na outra.

---

# Milestone 4 — Pagamentos integrados

**Spec principal:** 006.

## Objetivo

Substituir registros manuais pelo fluxo financeiro integrado sem permitir dupla cobrança.

## Ordem obrigatória

### 1. Payment state machine

Antes de SDK:

- PaymentAttempt;
- idempotency key;
- ProviderEvent inbox;
- states completos;
- `CONFIRMATION_PENDING`;
- Refund;
- reconciliation;
- eventos financeiros em realtime.

### 2. Pix

- create charge;
- QR/copia-e-cola;
- webhook;
- confirmação;
- expiração;
- reconciliação;
- atualização simultânea de Atendimento/Guest/Gerência.

### 3. Tap on Phone

No Android:

- `TapToPayProvider`;
- capability detection;
- `PaytimeTapProvider`;
- Paytime SDK;
- lifecycle/cancel;
- sem abrir aplicativo externo no happy path;
- fallback claro para terminal externo.

## Gate de saída

Passar testes de:

- double tap;
- retry frontend;
- retry backend;
- timeout ambíguo;
- webhook duplicado;
- reconciliação posterior;
- partial payment;
- refund parcial/total.

Nenhum desses cenários pode aplicar o efeito financeiro duas vezes.

---

# Milestone 5 — Conta da Casa

**Spec principal:** 002.

## Objetivo

Adicionar relacionamento sem transformar identidade em requisito do PDV.

## Entregas

- Customer;
- Relationship;
- política por Venue;
- VISITOR / KNOWN / REGULAR / HOUSE / RESTRICTED;
- busca por nome/apelido/telefone;
- associação posterior de Customer a uma Tab existente;
- OperatingLimit;
- exposure;
- REQUIRES_ACTION;
- override auditável;
- histórico entre visitas.

## Gate de saída

Uma Tab anônima precisa continuar sendo o happy path. Identificar o cliente depois não pode migrar nem recriar Order, Charge ou Payment.

---

# Milestone 6 — Quick Catalog + AI Icons

**Spec principal:** 005.

## Objetivo

Permitir que Bar/Cozinha alterem catálogo no ritmo real da operação sem criar duplicatas.

## Ordem

- normalized product name;
- autocomplete;
- resolve-or-create transacional;
- ProductIcon 1:1;
- placeholder;
- geração assíncrona;
- storage/CDN;
- publish;
- regenerate/upload apenas em fluxo avançado.

A IA não faz parte da transação de criação do Product.

## Gate de saída

Mesmo com o provider de imagem indisponível:

- Product é criado;
- aparece no catálogo;
- pode ser vendido;
- usa placeholder;
- geração pode ser retomada depois.

---

# Milestone 7 — Management Cockpit

**Spec principal:** 007.

## Objetivo

Construir a Gerência sobre fatos já confiáveis, e não sobre queries ad hoc em tabelas operacionais.

## Pré-requisitos

Não começar analytics sério antes de:

- ledger estável;
- realtime estável;
- AuditEvent/fatos persistidos;
- business date definido;
- fulfillment com timestamps coerentes;
- estados de TableOccupancy reais quando métricas físicas forem exibidas.

## Entregas

- outbox/fatos canônicos;
- ManagementLiveSnapshot;
- DailyOperationsSummary;
- MonthlyManagementSummary;
- rebuild/replay;
- home Agora;
- alertas;
- operação;
- timeline;
- vendas;
- fechamento diário;
- fechamento mensal;
- insights determinísticos;
- push apenas para exceções aprovadas.

## Gate de saída

Todos os números P0 exibidos pela Gerência devem possuir:

- fórmula documentada;
- fonte canônica;
- teste;
- business date;
- capacidade de drill-down ou reconstrução.

---

# Milestone 8 — Pilot hardening

## Objetivo

Transformar uma demo funcional em sistema no qual o bar pode realmente depender.

## Reliability

- migrations seguras;
- backup automático;
- restore testado;
- health/readiness;
- structured logging;
- error reporting;
- métricas técnicas;
- tracing/correlation id quando útil;
- jobs retryable/idempotentes;
- dead-letter/recovery operacional;
- rate limits;
- secrets fora do repo.

## Security

- RBAC server-side;
- sessão expirada/revogada;
- device/session audit;
- proteção de endpoints guest;
- webhook verification;
- redaction de dados sensíveis;
- dependency/security scanning.

## Operação

- seed/configuração de produção;
- runbook;
- rollback;
- modo de manutenção;
- suporte a reconnect;
- UX clara para backend/realtime indisponível;
- procedimento manual de contingência para pagamentos.

## Gate de saída

Executar pelo menos uma simulação de turno com:

- múltiplos aparelhos;
- Bar e Cozinha simultâneos;
- perda/reconexão de rede;
- Product ficando indisponível;
- duas Tabs na mesma mesa;
- guest ordering;
- pagamento parcial;
- Pix;
- Tap on Phone;
- refund;
- fechamento diário;
- backup/restore de teste.

---

# Gaps que exigem spec antes de implementação

As Specs 001–007 cobrem a tese central, mas alguns comportamentos de PDV de produção ainda não possuem contrato suficiente.

Não implementar por improviso. Criar specs dedicadas quando entrarem no milestone correspondente.

## Staff identity, auth e devices

Precisamos especificar:

- login/PIN;
- sessão;
- troca rápida de operador;
- device registration;
- revogação;
- roles/permissões;
- autorização offline/degradada, se existir.

## Tab operations

Precisamos decidir comportamento para:

- mover itens entre Tabs;
- split de Tab;
- merge de Tabs duplicadas;
- correção de lançamento;
- cancelamento depois de preparo;
- reabrir Tab fechada;
- transferir ownership/localização.

## Modifiers

Precisamos modelar sem depender de texto livre:

- tamanho;
- sabor;
- adicionais;
- remoções;
- escolhas obrigatórias;
- impacto de preço;
- routing;
- disponibilidade de modifier.

## Discounts, service charge e courtesy

`Adjustment` existe no domínio, mas falta contrato de UX/política para:

- desconto percentual;
- desconto fixo;
- cortesia;
- taxa de serviço;
- remoção da taxa;
- autorização de manager;
- motivo obrigatório em determinados limites;
- efeito em fechamento/analytics.

## Cash operations

O `CashShift` P0 precisa evoluir para:

- fundo inicial;
- suprimento;
- sangria;
- contagem;
- divergência;
- múltiplos caixas;
- fechamento por operador/device quando necessário.

## Receipts and printing

Precisamos decidir:

- recibo digital;
- impressão de conta;
- impressão de produção como fallback;
- Bluetooth/rede;
- política quando impressora estiver offline.

Impressão não deve virar dependência do fulfillment normal se as telas estiverem saudáveis.

## Covers / quantidade de pessoas

Antes de Gerência publicar ticket/consumo “por pessoa”, definir uma fonte canônica para covers/quantidade de pessoas e quando esse dado é opcional.

---

# O que explicitamente não bloqueia o piloto inicial

Não puxar para P0 sem evidência operacional:

- estoque profundo por insumo;
- CMV completo;
- fiscal avançado;
- delivery;
- loyalty;
- payroll/ponto;
- data warehouse;
- chatbot gerencial;
- ML de previsão;
- BLE/presença para provar o fluxo básico;
- IA generativa para analytics.

---

# Ordem resumida de execução

```text
0. foundation
      |
1. Core POS walking skeleton
      |
2. realtime + dispatch básico
      |
3. tables + guest
      |
4. Pix + Tap on Phone
      |
5. Conta da Casa
      |
6. Quick Catalog + AI icons
      |
7. Management Cockpit
      |
8. pilot hardening
```

Alguns trabalhos podem ocorrer em paralelo depois que contratos estejam estáveis, mas **nenhuma trilha deve furar os gates financeiros e de domínio**.

---

# Primeira sequência de PRs recomendada

Para sair do estado atual com risco baixo:

1. **Bootstrap API** — Django/DRF/Postgres, settings, health, CI.
2. **Venue + auth mínimo** — Venue, StaffMember, roles e sessão.
3. **Catalog core** — Product, Availability, stations, seed.
4. **Ordering core** — Tab, Order, OrderItem, confirmação transacional.
5. **Ledger core** — Charge, Payment manual, exposure e audit.
6. **Android shell** — login, Tabs, catálogo e lançamento de pedido.
7. **Bar/Kitchen shell** — filas reais ligadas à API.
8. **Vertical slice E2E** — abrir Tab → pedido → pronto → pagar → fechar.
9. **Realtime foundation** — outbox + Redis/WebSocket + reconnect.
10. A partir daqui, seguir os milestones deste documento.

Cada PR deve apontar para a spec/acceptance correspondente e terminar com comportamento executável, não apenas scaffolding sem uso.

---

# Definition of Pilot Ready

Rodada está pronto para piloto apenas quando um turno real consegue operar sem depender do protótipo e sem editar banco/manual state para completar o fluxo.

No mínimo:

- staff autenticado;
- Tab real;
- pedidos reais;
- Bar/Cozinha reais;
- disponibilidade compartilhada;
- ledger consistente;
- pagamento funcional;
- mesa/ocupação quando usada;
- QR guest quando habilitado;
- realtime com recuperação;
- auditoria;
- caixa/fechamento mínimo;
- backup e restore;
- observabilidade;
- fluxo de contingência documentado.

> A meta técnica não é “implementar 7 specs”. A meta é **fechar loops operacionais completos, observáveis e recuperáveis**.
