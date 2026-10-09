# Rodada Web

Next.js / React, mobile-first, para Cozinha, Bar, Cliente e Gerência.

## Estado atual — Spec 008

A primeira implementação executável fecha a sessão de staff no Web/PWA:

- `/staff` com login por Venue + operador + PIN;
- BFF same-origin em `/api/auth/*`;
- browser nunca recebe access/refresh token do Django;
- tokens ficam em cookies `httpOnly`, `SameSite=Lax` e `Secure` em produção;
- refresh rotativo ocorre server-side;
- browser installation id fica em cookie `httpOnly` separado;
- mutations rejeitam origem cross-site;
- lock/logout removem a sessão local;
- revogação/expiração terminal também limpa cookies;
- fast operator switch aparece apenas em device `TRUSTED`;
- privileged reauthentication é inline;
- erros como `CAPABILITY_REQUIRED` e `REAUTH_REQUIRED` mantêm código explícito.

A API Django é acessada apenas no servidor Next através de `RODADA_API_BASE_URL`. Não usar `NEXT_PUBLIC_` para essa URL e não colocar bearer token em `localStorage` ou `sessionStorage`.

## Rodar localmente

Requer Node.js 22+.

```bash
cd apps/web
npm ci
RODADA_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

Acesse:

```text
http://localhost:3000/staff
```

## Checks

```bash
npm run typecheck
npm run build
npx playwright install chromium
npm run test:visual
npm run test:integration
```

Os testes iniciam servidores de produção próprios: execute o build antes. A suíte visual tem 102 testes nas nove telas, cinco larguras e estados de operação, incluindo o formulário do Quick Catalog; usa respostas controladas somente nos testes. A integração tem cinco testes de navegador com BFF e Django reais.

Antes da integração, na raiz do repositório: `python -m pip install -e "apps/api[dev]"`. O banco local é SQLite temporário; CI usa PostgreSQL 17 isolado. Se Python não estiver no PATH, defina `RODADA_TEST_PYTHON` com o caminho completo do executável. No PowerShell: `$env:RODADA_TEST_PYTHON='C:\caminho\python.exe'`. Reserve as portas 3100 (visual), 3110 e 8100 (integração).

O [relatório de paridade](../../docs/design/visual-parity-audit.md) registra métricas, cobertura e limitações. A [Spec 020](../../specs/020-web-operational-completion/spec.md) entrega Quick Catalog em Bar/Cozinha, histórico persistido da própria comanda guest com polling de cinco segundos, seleção paginada de turnos antigos em `/cash` e relatórios com filtro de período/CSV em `/reports`. Criação exige `catalog.product.create`; relatórios, `management.reports.read`; configuração do calendário também exige `venue.configure`. A API continua autoritativa.

Antes de iniciar uma instância existente, aplicar as migrações Django (`python manage.py migrate`, em `apps/api`, com o ambiente correto). Elas adicionam ProductIcon e hora de corte do Venue, cujo default 0 preserva meia-noite. Produto novo e existente recebem ícone 1:1 com fallback `GENERATOR_NOT_CONFIGURED`; não há IA/worker configurado nesta entrega, por escolha do usuário. Nenhuma credencial externa é necessária para criar ou vender. O crédito pessoal permanece removido. Consulte [entrega e limites](../../docs/development/web-operational-completion.md).

## Superfícies e hosts

Em produção, as superfícies Web/PWA usam os hosts canônicos definidos na arquitetura de superfícies:

```text
gerencia.rodada.ai  Gerência
cozinha.rodada.ai   Cozinha
bar.rodada.ai       Bar
cliente.rodada.ai   Cliente / QR
api.rodada.ai       API
```

`rodada.ai` é o site institucional. **Rodada Atendimento** continua Android nativo.

Durante desenvolvimento, rotas locais podem continuar servindo como entrypoints:

```text
/staff      sessão/base de staff
/bar        produção + disponibilidade
/kitchen    produção + disponibilidade
/guest      QR/PWA do cliente
/manage     gerência
/reports    relatórios operacionais + calendário/CSV
/cash       caixa + histórico de turnos
```

Rotas locais são detalhe de implementação e não definem URLs públicas. O runtime/deploy pode resolver a superfície pelo hostname mantendo um único codebase/deploy Next.js.

`app.rodada.ai` e `pedido.rodada.ai` são aliases de compatibilidade durante a migração. Não criar aliases públicos como `kitchen.rodada.ai`, `owner.rodada.ai` ou `guest.rodada.ai` sem decisão arquitetural.

Compartilhar auth, contratos e design primitives não significa transformar todas as funções em um único frontend escondido por role.

## Design

A implementação consome os tokens semânticos de `docs/design/system.md`: fundo/superfícies quentes, alto contraste, acento âmbar, estados semanticamente consistentes e targets de toque de pelo menos 44 px.

O protótipo continua como referência visual, não como fonte de regra de domínio.


## Invalidação de acesso

Enquanto uma sessão staff está ativa, o Web/PWA consulta o invalidation feed em intervalo bounded. Mudança de role/device força nova leitura de `/auth/me` e limpa qualquer janela de reauth recente. Falha do feed não bloqueia operação: a API continua autoritativa em todas as mutations.

## Revisão UX local — Spec 021

Fila/passe vêm antes do catálogo em Bar/Cozinha e expandem para duas colunas em tablet/desktop. Gerência prioriza pulso/produção e mantém Conta da Casa em Gestão. Cliente mantém ícone/nome/preço separados; POS desabilita produto indisponível sem substituir a validação da API.

A suíte visual cobre os seis viewports 360×800, 390×844, 430×932, 768×1024, 1280×800 e 1440×900. Na raiz, `node scripts/ux-review-gallery.mjs` gera o índice estático ignorado; `--before` preserva capturas antes das alterações. O launcher e o runner Django descartável são ferramentas locais, sem nova rota em produção. Consulte [auditoria, reprodução, evidências e limites](../../docs/design/operational-ux-review.md).

## Atendimento Web — test without payments

From this checkout, `npm ci`, `npm run build`, then
`RODADA_API_BASE_URL=http://127.0.0.1:18764 npm run start -- --port 3120 --hostname 0.0.0.0`.
Open `http://localhost:3120/attendance` For phones, use an HTTPS proxy to preserve secure authentication cookies; plain LAN HTTP is not supported by the production build.
The existing demo API must be running; no public Sites deployment is required.
For the seeded local demo: Venue `bar-do-aderlan`, staff `bia`, PIN `1234`
(or manager `ana`, PIN `0420`). These are test-only identities.

Agora lists deliveries; Contas opens/searches comandas and confirms customized
orders; Mesas supports occupancy, association, zones and cleaning. Add the page
to the phone's home screen for standalone browser mode. No payments, refunds or
cash management are exposed by this companion. Unpaid tabs remain open, and
closure requires zero canonical balance. Native NFC/BLE and payment SDKs require
the Android app. API connectivity is required; no offline command queue exists.
Keep the page open while verifying an ambiguous order: retries preserve its payload
and idempotency key in memory. Reload recovery is outside this slice.
