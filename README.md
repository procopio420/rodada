# Rodada

**Rodada é um PDV operacional para bares cheios — com dispatch, comandas flexíveis, identidade opcional e pagamentos no núcleo.**

O primeiro piloto é o Bar do Aderlan: operação de alto fluxo, ambiente físico flexível, muitos clientes recorrentes e atendimento que não cabe bem no modelo tradicional de “mesa fixa + pedido + conta no fim”.

A tese não é construir só um CRM ou uma camada em cima de outro PDV. Vamos **reinventar o PDV para esse tipo de operação** e usar o piloto para testar novas primitivas de hospitality:

- **comanda é a unidade financeira; mesa é contexto físico**;
- identidade do cliente é opcional, mas todo pedido pertence a uma comanda;
- uma comanda pode ser encontrada por nome/apelido, perfil, código, sessão do dispositivo, QR dinâmico ou NFC;
- uma mesa pode ter várias comandas simultâneas;
- uma comanda pode existir sem mesa e pode mudar de localização durante a noite;
- pedido é uma unidade operacional que precisa ser produzido e entregue, não só registrado;
- disponibilidade é uma regra operacional do catálogo, não um estado do pedido: se a cozinha esgotou um item, staff e guest enxergam a mesma verdade;
- algumas mesas podem aceitar pedido direto pelo celular, sem exigir app instalado;
- mesas possuem ciclo operacional de ocupação e limpeza, separado do fechamento das comandas;
- atendimento pode ser despachado como trabalho;
- relacionamento (“da casa”) influencia a experiência e a política financeira;
- pagamento pode ocorrer antes, durante ou depois da visita;
- o sistema deve funcionar melhor no pico, não pior.

## Marca e domínios canônicos

A marca do produto é **Rodada** e o domínio canônico é **`rodada.ai`**.

Hosts públicos oficiais:

| Superfície | Host |
| --- | --- |
| Site institucional | `rodada.ai` |
| Gerência | `gerencia.rodada.ai` |
| Cozinha | `cozinha.rodada.ai` |
| Bar | `bar.rodada.ai` |
| Cliente / QR | `cliente.rodada.ai` |
| API | `api.rodada.ai` |
| Atendimento | app Android nativo |

A frase **“Me vê uma rodada aí.”** pode ser usada como assinatura/campanha da marca.

Os subdomínios são superfícies do mesmo produto e não implicam backends separados. Paths como `/owner`, `/kitchen` e `/guest` podem existir internamente, mas não são o contrato público de URL.

Ver [ADR 0010](./docs/adr/0010-brand-and-canonical-domains.md).

## Princípio de domínio

> **Identity optional, Tab mandatory.**

Nome, perfil Rodada, QR, NFC e sessão do celular são formas de encontrar ou acessar a mesma comanda. Nenhuma delas deve virar a própria comanda.

## Roadmap por slices

### 001 — Core POS

O mínimo para operar uma venda de ponta a ponta:

- catálogo, preços e disponibilidade operacional compartilhada;
- cozinha/bar pode indisponibilizar ou reativar itens em tempo real para todos os canais;
- comandas/tabs independentes de mesa;
- pedido e itens;
- status operacional;
- recebimento e fechamento;
- caixa básico e auditoria;
- suporte a localização opcional e múltiplas comandas na mesma ocupação.

### 002 — Conta da Casa

A camada de relacionamento + dinheiro:

- cliente e identidade local;
- `VISITOR`, `KNOWN`, `REGULAR`, `HOUSE`, `RESTRICTED`;
- limite operacional;
- exposição aberta;
- pagamento parcial;
- histórico entre visitas;
- overrides auditáveis.

### 003 — Dispatch

A camada de coordenação em tempo real:

- zonas e pontos de atendimento;
- chamadas de atendimento;
- ownership explícito ou inferido de tarefas;
- pedidos prontos aguardando retirada;
- fila operacional por prioridade;
- happy path de entrega sem exigir taps de “peguei”/“entreguei”;
- telemetria passiva opcional com source/confidence;
- runs de entrega agrupados por zona;
- métricas de tempo entre pedido, preparo, retirada e entrega separando observado/inferido/corrigido.

### 004 — Table Ops + Guest Ordering

A camada física + self-service:

- mesa como recurso físico, não conta;
- ocupação da mesa separada das comandas;
- estados `AVAILABLE → OCCUPIED → DIRTY → CLEANING → AVAILABLE`;
- várias comandas por ocupação;
- QR opaco por mesa;
- PWA guest sem instalação obrigatória;
- cliente cria/assume comanda e pede direto;
- bloqueio imediato de guest ordering pelo staff;
- invalidação das sessões antigas ao liberar/limpar a mesa;
- código curto, perfil e NFC como caminhos adicionais para resolver uma comanda;
- métricas de giro e limpeza.

### 005 — Quick Catalog + AI Icons

A camada de criação rápida de cardápio:

- Bar/Cozinha pode usar **+ Item** na própria estação;
- nome possui autocomplete do catálogo e reutiliza Product existente quando encontrado;
- se não existir correspondência exata, **Criar "{nome}"** faz resolve-or-create automaticamente;
- estação vem preenchida pelo contexto e preço completa o item novo;
- Product e ProductIcon ficam vinculados 1:1 por todo o lifecycle;
- o ícone é gerado automaticamente por IA a partir do nome/descrição, sem botão extra;
- geração segue um style contract versionado do Rodada;
- falha da IA nunca bloqueia criar ou vender o produto;
- regeneração excepcional, upload manual e placeholder são suportados;
- autocomplete, staff e guest exibem o mesmo asset publicado.

### 006 — Payments + Tap on Phone

A camada de pagamento integrada à comanda:

- Payment pertence à Tab, nunca à mesa;
- pagamento parcial é nativo e saldo é derivado do ledger;
- **Rodada Atendimento é Android nativo (Kotlin + Jetpack Compose)**;
- Staff paga direto da Tab sem redigitar valor e sem sair do Rodada;
- Tap on Phone transforma o próprio aparelho compatível do garçom em terminal de aproximação;
- **Paytime Tap on Phone é o primeiro adapter do MVP**, atrás de uma abstração própria;
- provider não vaza para o domínio e novos adapters podem coexistir por Venue;
- Pix e pagamento pelo Guest atualizam a mesma Tab;
- dinheiro e maquininha externa existem como fallbacks auditáveis;
- idempotência, webhooks e reconciliação evitam dupla cobrança;
- estado ambíguo vira `CONFIRMATION_PENDING`, nunca retry cego;
- estornos preservam o Payment original e geram efeito reverso rastreável.

### 007 — Management Cockpit + Analytics

A camada de gerência mobile-first:

- **celular é o baseline**; tablet/desktop expandem a análise;
- durante o serviço, a home é um cockpit de exceções em tempo real;
- alertas acionáveis sobem antes de gráficos e relatórios;
- operação detalhada cobre cozinha, bar, atendimento, mesas e pagamentos;
- timeline pesquisável ajuda a investigar o que aconteceu;
- vendas cruzam receita, ticket, origem do pedido, mix e ocupação;
- fechamento diário é gerado a partir de ledger/eventos e revisado pelo gerente;
- fechamento mensal começa por resumo executivo e comparações úteis;
- insights distinguem fato, estimativa e hipótese;
- métricas de equipe servem para diagnóstico, **não leaderboard simplista**;
- read models/projeções são idempotentes, reconstruíveis e alimentados por fatos canônicos;
- business date respeita o turno do bar e não precisa virar à meia-noite.

### 008 — Staff Auth, Roles & Devices

Fundação de identidade operacional: membership por Venue, roles/capabilities server-side, PIN/sessão, troca rápida de operador, devices confiáveis/revogáveis e autoria auditável.

### 009 — Tab Operations

Move localização, split/merge e transferência de responsabilidade aberta sem reescrever Order, Charge, Payment ou Refund confirmado. Pagamento confirmado bloqueia transferências financeiras no P0.

### 010 — Product Modifiers & Variants

Variants definem a forma-base vendável; modifiers estruturam sabores, adicionais, remoções e escolhas obrigatórias. Tudo é revalidado e snapshotado na confirmação do OrderItem.

### 011 — Pricing, Discounts, Courtesy & Service Charge

Descontos, cortesias e taxa de serviço são Adjustments append-only, em centavos, com alocação determinística, thresholds de autorização e interação explícita com pagamentos/refunds.

### 012 — Cash Management

CashPoint + CashShift + CashMovement: fundo inicial, dinheiro/troco, suprimento, sangria, conferência, divergência, review e correções tardias sem reescrever o fechamento original.

### 013 — Venue Configuration

Gerência configura o estabelecimento por contratos tipados, sem acesso ao banco e sem um settings JSON genérico. Mudanças ao vivo são validadas como seguras, versionadas para novo contexto ou bloqueadas até estado seguro.

### 014 — Connectivity & Degraded Operation

Distingue API de realtime e define ONLINE / RECONNECTING / STALE / OFFLINE. Rede ruim nunca autoriza dupla cobrança nem transforma cache/evidência local em verdade canônica.

### 015 — Receipts, Printing & Production Fallbacks

Conta, recibo digital/impresso e ticket de produção como saída derivada. PrintJob é idempotente, reprint é explícito e a operação continua sem impressora.

### 016 — Covers / Party Size

Covers pertencem primariamente à TableOccupancy, podem ser UNKNOWN e nunca são inferidos por quantidade de Tabs. Analytics por pessoa expõem cobertura dos dados.

### 017 — Order Corrections & Exception Handling

Cancelamento, item errado, remake, replacement e complaint preservam o OrderItem original. Correções operacionais/financeiras criam história compensatória, não “limpam” o passado.

### 018 — Notifications & Operational Escalation

OperationalAlert é a mesma exceção usada por Gerência, in-app e push: dedupe, cooldown, acknowledgement separado de resolução, auto-resolution, escalation e deep link para o contexto exato.

## O que NÃO queremos copiar

Não queremos um ERP genérico com uma skin de bar. Fiscal, estoque profundo, delivery e contabilidade podem vir depois ou por integração.

Também não queremos transformar QR em “conta da mesa”. **Pedido sempre pertence a uma Tab.**

## Comece por aqui

1. [`AGENTS.md`](./AGENTS.md) — contrato de desenvolvimento spec-driven.
2. [`docs/product/vision.md`](./docs/product/vision.md) — visão e tese.
3. [`docs/product/principles.md`](./docs/product/principles.md) — princípios de produto.
4. [`docs/design/system.md`](./docs/design/system.md) — design system compartilhado por todas as superfícies.
5. [`docs/domain/model.md`](./docs/domain/model.md) — modelo canônico.
6. [`docs/architecture/technical-roadmap.md`](./docs/architecture/technical-roadmap.md) — ordem técnica de implementação, gates e definição de piloto pronto.
7. [`specs/001-core-pos/spec.md`](./specs/001-core-pos/spec.md) — primeiro slice implementável.
8. [`specs/002-house-account/spec.md`](./specs/002-house-account/spec.md) — relacionamento e exposição.
9. [`specs/003-dispatch/spec.md`](./specs/003-dispatch/spec.md) — coordenação operacional.
10. [`specs/004-table-guest-ordering/spec.md`](./specs/004-table-guest-ordering/spec.md) — mesa, ocupação, QR e guest ordering.
11. [`specs/005-catalog-ai-icons/spec.md`](./specs/005-catalog-ai-icons/spec.md) — criação rápida de item e ícones gerados por IA.
12. [`specs/006-payments-tap-on-phone/spec.md`](./specs/006-payments-tap-on-phone/spec.md) — pagamentos, Pix, Tap on Phone, idempotência e reconciliação.
13. [`specs/007-management-cockpit/spec.md`](./specs/007-management-cockpit/spec.md) — cockpit gerencial mobile-first, realtime, fechamentos e analytics.
14. [`specs/008-staff-auth-roles-devices/spec.md`](./specs/008-staff-auth-roles-devices/spec.md) — identidade staff, capabilities, sessões e devices.
15. [`specs/009-tab-operations/spec.md`](./specs/009-tab-operations/spec.md) — move/split/merge de Tab sem reescrever histórico.
16. [`specs/010-product-modifiers-variants/spec.md`](./specs/010-product-modifiers-variants/spec.md) — variants/modifiers e snapshots de customização.
17. [`specs/011-pricing-discounts-service-charge/spec.md`](./specs/011-pricing-discounts-service-charge/spec.md) — discounts, courtesy e service charge.
18. [`specs/012-cash-management/spec.md`](./specs/012-cash-management/spec.md) — caixa físico, conferência e divergência.
19. [`specs/013-venue-configuration/spec.md`](./specs/013-venue-configuration/spec.md) — configuração tipada do Venue.
20. [`specs/014-connectivity-degraded-operation/spec.md`](./specs/014-connectivity-degraded-operation/spec.md) — reconnect, stale/offline e recovery.
21. [`specs/015-receipts-printing-fallbacks/spec.md`](./specs/015-receipts-printing-fallbacks/spec.md) — recibos, impressão e fallback de produção.
22. [`specs/016-covers-party-size/spec.md`](./specs/016-covers-party-size/spec.md) — covers/party size canônicos.
23. [`specs/017-order-corrections-exceptions/spec.md`](./specs/017-order-corrections-exceptions/spec.md) — cancelamentos, remake, replacement e exceções.
24. [`specs/018-notifications-operational-escalation/spec.md`](./specs/018-notifications-operational-escalation/spec.md) — alertas acionáveis, push e escalonamento.
25. [`docs/adr/0008-management-cockpit-projections.md`](./docs/adr/0008-management-cockpit-projections.md) — projeções/read models e business date da Gerência.
26. [`docs/product/icon-style.md`](./docs/product/icon-style.md) — style contract dos ícones de catálogo.
27. [`docs/adr/0004-tab-identity-and-table-occupancy.md`](./docs/adr/0004-tab-identity-and-table-occupancy.md) — Tab, identidade e ocupação.
28. [`docs/adr/0005-domain-boundaries-and-operational-availability.md`](./docs/adr/0005-domain-boundaries-and-operational-availability.md) — fronteiras de domínio e indisponibilidade operacional.
29. [`docs/adr/0009-passive-fulfillment-telemetry.md`](./docs/adr/0009-passive-fulfillment-telemetry.md) — retirada/entrega inferidas sem taps obrigatórios.
30. [`docs/adr/0007-specialized-surfaces-and-paytime-tap.md`](./docs/adr/0007-specialized-surfaces-and-paytime-tap.md) — apps especializados, Atendimento Android nativo e Paytime como primeiro adapter.
31. [`docs/demo/demo-script.md`](./docs/demo/demo-script.md) — roteiro para mostrar ao Aderlan.
32. [`prototype/index.html`](./prototype/index.html) — protótipo estático navegável.

## Superfícies do produto

Rodada é um único produto com superfícies especializadas por função, todas sobre o mesmo domínio e backend:

- **Rodada Atendimento** — Android nativo em Kotlin + Jetpack Compose para garçom/caixa móvel, incluindo Tap on Phone;
- **Rodada Cozinha** — Web/PWA focada em produção, fila e disponibilidade;
- **Rodada Bar** — Web/PWA focada em bebidas, fila e disponibilidade;
- **Rodada Cliente** — Web/PWA via QR, sem instalação obrigatória;
- **Rodada Gerência** — Web/PWA responsiva **mobile-first** para cockpit ao vivo, exceções, fechamento, pessoas e analytics.

Não criar um único frontend com todas as funções escondidas por permissão. Compartilhar contratos, domínio e design tokens; cada superfície deve continuar extremamente focada no trabalho do seu usuário.

## Dispositivos e implantação do piloto

O Bar do Aderlan pode reaproveitar seus computadores: **caixa e gerência** no PC do caixa; **cozinha e bar** no PC da produção, preservando filas distintas. O **Atendimento Android** usa por padrão celulares pessoais dos garçons (BYOD), com alternativa de aparelho compartilhado/de reserva ou atendimento pelo caixa. O **Cliente** utiliza o próprio celular pelo QR/PWA.

**Autorizamos pessoas, não celulares:** login válido registra automaticamente a instalação e permite as operações do funcionário sem aprovação do gerente nem promoção para `TRUSTED`. Gestão de sessões/dispositivos existe para segurança, e `TRUSTED` atende capacidades específicas de terminais compartilhados. Tap on Phone requer elegibilidade/provisionamento separados pelo provider e não é condição para operar o PDV.

Detalhes: [Spec 008](./specs/008-staff-auth-roles-devices/spec.md), [Spec 006](./specs/006-payments-tap-on-phone/spec.md) e [ADR 0007](./docs/adr/0007-specialized-surfaces-and-paytime-tap.md).

## Design system

PDV, Cozinha/Bar, Dispatch, Conta da Casa, Table Ops, Guest Ordering e Quick Catalog compartilham um único sistema visual definido em [`docs/design/system.md`](./docs/design/system.md).

O Quick Catalog também segue esse contrato: autocomplete-first, reuse de Product/ProductIcon existente e geração automática do ícone apenas para Product novo. O asset segue [`docs/product/icon-style.md`](./docs/product/icon-style.md); estados como `GENERATING`, `FAILED`, selecionado e indisponível pertencem à UI.

O protótipo usa [`prototype/design-system.css`](./prototype/design-system.css) como referência executável. O app Next.js deve portar esses tokens e componentes para primitives reutilizáveis, não copiar cada tela como CSS isolado.

## Stack alvo

- **API:** Django + Django REST Framework
- **Atendimento:** Android nativo — Kotlin + Jetpack Compose
- **Cozinha/Bar/Cliente/Gerência:** Next.js + React / PWA conforme a superfície; Gerência é mobile-first
- **Tap on Phone (MVP):** Paytime SDK, encapsulado por adapter
- **DB:** PostgreSQL
- **Realtime:** Redis + WebSocket quando dispatch entrar
- **Arquitetura:** modular monolith primeiro

## Norte do produto

> **PDVs registram o que aconteceu. Rodada também coordena o que precisa acontecer agora.**
