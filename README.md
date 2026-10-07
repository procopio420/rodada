# Rodada

**Rodada é um PDV operacional para bares cheios — com dispatch, identidade de cliente e pagamentos no núcleo.**

O primeiro piloto é o Bar do Aderlan: operação de alto fluxo, ambiente físico flexível, muitos clientes recorrentes e atendimento que não cabe bem no modelo tradicional de “mesa fixa + pedido + conta no fim”.

A tese não é construir só um CRM ou uma camada em cima de outro PDV. Vamos **reinventar o PDV para esse tipo de operação** e usar o piloto para testar novas primitivas de hospitality:

- a comanda pertence à pessoa/grupo, não necessariamente à mesa;
- a localização pode mudar durante a noite;
- pedido é uma unidade operacional que precisa ser produzido e entregue, não só registrado;
- atendimento pode ser despachado como trabalho;
- relacionamento (“da casa”) influencia a experiência e a política financeira;
- pagamento pode ocorrer antes, durante ou depois da visita;
- o sistema deve funcionar melhor no pico, não pior.

## MVP em três slices

### 001 — Core POS

O mínimo para operar uma venda de ponta a ponta:

- catálogo e preços;
- comandas/tabs;
- pedido e itens;
- status operacional;
- recebimento e fechamento;
- caixa básico e auditoria;
- suporte a ponto/localização opcional, sem depender de mesa fixa.

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

- zonas e pontos efêmeros;
- chamadas de atendimento;
- ownership/claim de tarefas;
- pedidos prontos aguardando retirada;
- fila operacional por prioridade;
- runs de entrega agrupados por zona;
- métricas de tempo entre pedido, preparo, retirada e entrega.

## O que NÃO queremos copiar

Não queremos um ERP genérico com uma skin de bar. Fiscal, estoque profundo, delivery e contabilidade podem vir depois ou por integração.

O foco inicial é construir o melhor **sistema transacional e operacional do salão/bar** para ambientes de alto fluxo.

## Comece por aqui

1. [`AGENTS.md`](./AGENTS.md) — contrato de desenvolvimento spec-driven.
2. [`docs/product/vision.md`](./docs/product/vision.md) — visão e tese.
3. [`docs/product/principles.md`](./docs/product/principles.md) — princípios de produto.
4. [`docs/domain/model.md`](./docs/domain/model.md) — modelo canônico.
5. [`specs/001-core-pos/spec.md`](./specs/001-core-pos/spec.md) — primeiro slice implementável.
6. [`specs/002-house-account/spec.md`](./specs/002-house-account/spec.md) — relacionamento e exposição.
7. [`specs/003-dispatch/spec.md`](./specs/003-dispatch/spec.md) — coordenação operacional.
8. [`docs/demo/demo-script.md`](./docs/demo/demo-script.md) — roteiro para mostrar ao Aderlan.
9. [`prototype/index.html`](./prototype/index.html) — protótipo estático navegável.
10. [`docs/implementation-status.md`](./docs/implementation-status.md) — mapa do que está implementado e lacunas ainda sem spec.
11. [`docs/demo/local-runbook.md`](./docs/demo/local-runbook.md) — reset, credenciais e verificação local do demo.

## Stack alvo

- **API:** Django + Django REST Framework
- **Web/PWA:** Next.js + React
- **DB:** PostgreSQL
- **Realtime:** Redis + WebSocket quando dispatch entrar
- **Arquitetura:** modular monolith primeiro

## Desenvolvimento local com Docker

O ambiente canônico sobe API, PostgreSQL, Redis/Channels, worker de ícones e web:

```bash
docker compose up --build
```

Abra `http://localhost:3000`. A API é `http://localhost:8000/api/`; o seed cria
o Bar do Aderlan, usuários operacionais com PIN local, caixa, mesas fixas e
temporária, QR codes e catálogo. O fluxo local completo, incluindo credenciais e
smoke test, está em [`docs/demo/local-runbook.md`](./docs/demo/local-runbook.md).

## Rodar sem Docker

API (Django + DRF):

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

Em outro terminal, inicie a interface staff:

```bash
cd apps/web
npm install
npm run dev
```

Abra `http://localhost:3000`. A API local fica em `http://localhost:8000/api/` e o
seed cria o Bar do Aderlan, um caixa aberto, pontos P37/P41/P44 e o catálogo de demo.
Consulte o [runbook do demo](./docs/demo/local-runbook.md) para as credenciais e o
comando verificável do fluxo de ponta a ponta.

Variáveis opcionais: `REDIS_URL` habilita o channel layer compartilhado em produção;
`NEXT_PUBLIC_API_URL` e `NEXT_PUBLIC_WS_URL` apontam a interface para a API e
WebSocket. A sessão do operador vem do login local por PIN; clientes devem enviar o
token retornado como `Authorization: Bearer <session_token>`.

## Norte do produto

> **PDVs registram o que aconteceu. Rodada também coordena o que precisa acontecer agora.**
