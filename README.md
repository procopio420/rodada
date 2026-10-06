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
- ownership/claim de tarefas;
- pedidos prontos aguardando retirada;
- fila operacional por prioridade;
- runs de entrega agrupados por zona;
- métricas de tempo entre pedido, preparo, retirada e entrega.

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

## O que NÃO queremos copiar

Não queremos um ERP genérico com uma skin de bar. Fiscal, estoque profundo, delivery e contabilidade podem vir depois ou por integração.

Também não queremos transformar QR em “conta da mesa”. **Pedido sempre pertence a uma Tab.**

## Comece por aqui

1. [`AGENTS.md`](./AGENTS.md) — contrato de desenvolvimento spec-driven.
2. [`docs/product/vision.md`](./docs/product/vision.md) — visão e tese.
3. [`docs/product/principles.md`](./docs/product/principles.md) — princípios de produto.
4. [`docs/design/system.md`](./docs/design/system.md) — design system compartilhado por todas as superfícies.
5. [`docs/domain/model.md`](./docs/domain/model.md) — modelo canônico.
6. [`specs/001-core-pos/spec.md`](./specs/001-core-pos/spec.md) — primeiro slice implementável.
7. [`specs/002-house-account/spec.md`](./specs/002-house-account/spec.md) — relacionamento e exposição.
8. [`specs/003-dispatch/spec.md`](./specs/003-dispatch/spec.md) — coordenação operacional.
9. [`specs/004-table-guest-ordering/spec.md`](./specs/004-table-guest-ordering/spec.md) — mesa, ocupação, QR e guest ordering.
10. [`specs/005-catalog-ai-icons/spec.md`](./specs/005-catalog-ai-icons/spec.md) — criação rápida de item e ícones gerados por IA.
11. [`docs/product/icon-style.md`](./docs/product/icon-style.md) — style contract dos ícones de catálogo.
12. [`docs/adr/0004-tab-identity-and-table-occupancy.md`](./docs/adr/0004-tab-identity-and-table-occupancy.md) — Tab, identidade e ocupação.
13. [`docs/adr/0005-domain-boundaries-and-operational-availability.md`](./docs/adr/0005-domain-boundaries-and-operational-availability.md) — fronteiras de domínio e indisponibilidade operacional.
14. [`docs/demo/demo-script.md`](./docs/demo/demo-script.md) — roteiro para mostrar ao Aderlan.
15. [`prototype/index.html`](./prototype/index.html) — protótipo estático navegável.

## Design system

PDV, Cozinha/Bar, Dispatch, Conta da Casa, Table Ops, Guest Ordering e Quick Catalog compartilham um único sistema visual definido em [`docs/design/system.md`](./docs/design/system.md).

O Quick Catalog também segue esse contrato: autocomplete-first, reuse de Product/ProductIcon existente e geração automática do ícone apenas para Product novo. O asset segue [`docs/product/icon-style.md`](./docs/product/icon-style.md); estados como `GENERATING`, `FAILED`, selecionado e indisponível pertencem à UI.

O protótipo usa [`prototype/design-system.css`](./prototype/design-system.css) como referência executável. O app Next.js deve portar esses tokens e componentes para primitives reutilizáveis, não copiar cada tela como CSS isolado.

## Stack alvo

- **API:** Django + Django REST Framework
- **Web/PWA:** Next.js + React
- **DB:** PostgreSQL
- **Realtime:** Redis + WebSocket quando dispatch entrar
- **Arquitetura:** modular monolith primeiro

## Norte do produto

> **PDVs registram o que aconteceu. Rodada também coordena o que precisa acontecer agora.**
