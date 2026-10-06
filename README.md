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

## O que NÃO queremos copiar

Não queremos um ERP genérico com uma skin de bar. Fiscal, estoque profundo, delivery e contabilidade podem vir depois ou por integração.

Também não queremos transformar QR em “conta da mesa”. **Pedido sempre pertence a uma Tab.**

## Comece por aqui

1. [`AGENTS.md`](./AGENTS.md) — contrato de desenvolvimento spec-driven.
2. [`docs/product/vision.md`](./docs/product/vision.md) — visão e tese.
3. [`docs/product/principles.md`](./docs/product/principles.md) — princípios de produto.
4. [`docs/design/system.md`](./docs/design/system.md) — design system compartilhado por todas as superfícies.
5. [`docs/domain/model.md`](./docs/domain/model.md) — modelo canônico.
7. [`docs/architecture/technical-roadmap.md`](./docs/architecture/technical-roadmap.md) — ordem técnica de implementação, gates e definição de piloto pronto.
6. [`specs/001-core-pos/spec.md`](./specs/001-core-pos/spec.md) — primeiro slice implementável.
8. [`specs/002-house-account/spec.md`](./specs/002-house-account/spec.md) — relacionamento e exposição.
9. [`specs/003-dispatch/spec.md`](./specs/003-dispatch/spec.md) — coordenação operacional.
10. [`specs/004-table-guest-ordering/spec.md`](./specs/004-table-guest-ordering/spec.md) — mesa, ocupação, QR e guest ordering.
11. [`specs/005-catalog-ai-icons/spec.md`](./specs/005-catalog-ai-icons/spec.md) — criação rápida de item e ícones gerados por IA.
12. [`specs/006-payments-tap-on-phone/spec.md`](./specs/006-payments-tap-on-phone/spec.md) — pagamentos, Pix, Tap on Phone, idempotência e reconciliação.
13. [`specs/007-management-cockpit/spec.md`](./specs/007-management-cockpit/spec.md) — cockpit gerencial mobile-first, realtime, fechamentos e analytics.
14. [`docs/adr/0008-management-cockpit-projections.md`](./docs/adr/0008-management-cockpit-projections.md) — projeções/read models e business date da Gerência.
15. [`docs/product/icon-style.md`](./docs/product/icon-style.md) — style contract dos ícones de catálogo.
16. [`docs/adr/0004-tab-identity-and-table-occupancy.md`](./docs/adr/0004-tab-identity-and-table-occupancy.md) — Tab, identidade e ocupação.
17. [`docs/adr/0005-domain-boundaries-and-operational-availability.md`](./docs/adr/0005-domain-boundaries-and-operational-availability.md) — fronteiras de domínio e indisponibilidade operacional.
18. [`docs/adr/0006-passive-fulfillment-telemetry.md`](./docs/adr/0006-passive-fulfillment-telemetry.md) — retirada/entrega inferidas sem taps obrigatórios.
19. [`docs/adr/0007-specialized-surfaces-and-paytime-tap.md`](./docs/adr/0007-specialized-surfaces-and-paytime-tap.md) — apps especializados, Atendimento Android nativo e Paytime como primeiro adapter.
20. [`docs/demo/demo-script.md`](./docs/demo/demo-script.md) — roteiro para mostrar ao Aderlan.
21. [`prototype/index.html`](./prototype/index.html) — protótipo estático navegável.

## Superfícies do produto

Rodada é um único produto com superfícies especializadas por função, todas sobre o mesmo domínio e backend:

- **Rodada Atendimento** — Android nativo em Kotlin + Jetpack Compose para garçom/caixa móvel, incluindo Tap on Phone;
- **Rodada Cozinha** — Web/PWA focada em produção, fila e disponibilidade;
- **Rodada Bar** — Web/PWA focada em bebidas, fila e disponibilidade;
- **Rodada Cliente** — Web/PWA via QR, sem instalação obrigatória;
- **Rodada Gerência** — Web/PWA responsiva **mobile-first** para cockpit ao vivo, exceções, fechamento, pessoas e analytics.

Não criar um único frontend com todas as funções escondidas por permissão. Compartilhar contratos, domínio e design tokens; cada superfície deve continuar extremamente focada no trabalho do seu usuário.

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
