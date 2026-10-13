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

Os testes iniciam servidores de produção próprios: execute o build antes. A suíte visual atual tem465 testes de layout, estados, acessibilidade e controles equivalentes; usa respostas controladas somente nos testes. A integração tem87 jornadas com BFF e Django reais, mais três verificações opt-in do cardápio canônico.

Antes da integração, na raiz do repositório: `python -m pip install -e "apps/api[dev]"`. Para a suíte completa, use PostgreSQL17 descartável com banco `rodada_web_e2e`, host `127.0.0.1`, variáveis `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`, `RODADA_E2E_POSTGRES=1` e `RODADA_E2E_RESET=1`. A limpeza entre cenários exige esse nome/host/opt-in; nunca use um banco comercial. [Contrato de isolamento](../../docs/development/web-e2e-isolation.md). SQLite temporário continua disponível sem essas flags, mas não certifica concorrência nem isolamento da suíte completa. Se Python não estiver no PATH, defina `RODADA_TEST_PYTHON` com o caminho completo do executável. Reserve as portas3100 (visual),3110 e8100 (integração).

Execute `npm run test:integration -- --grep-invert "canonical photographed menu"` para as87 jornadas. Depois, com `RODADA_E2E_MENU=1`, execute `npm run test:integration -- tests/integration/venue-menu-acceptance.spec.ts` para as três larguras do cardápio. A aprovação comercial de preços/roteamento permanece independente dos testes.

O [relatório de paridade](../../docs/design/visual-parity-audit.md) registra métricas, cobertura e limitações. A [Spec 020](../../specs/020-web-operational-completion/spec.md) entrega Quick Catalog em Bar/Cozinha, histórico persistido da própria comanda guest com polling de cinco segundos, seleção paginada de turnos antigos em `/cash` e relatórios com filtro de período/CSV em `/reports`. Criação exige `catalog.product.create`; relatórios, `management.reports.read`; configuração do calendário também exige `venue.configure`. A API continua autoritativa.

Antes de iniciar uma instância existente, aplicar as migrações Django (`python manage.py migrate`, em `apps/api`, com o ambiente correto). Elas adicionam ProductIcon e hora de corte do Venue, cujo default 0 preserva meia-noite. Produto novo e existente recebem ícone 1:1 com fallback `GENERATOR_NOT_CONFIGURED`; não há IA/worker configurado nesta entrega, por escolha do usuário. Nenhuma credencial externa é necessária para criar ou vender. O crédito pessoal permanece removido. Consulte [entrega e limites](../../docs/development/web-operational-completion.md).

## Superfícies e hosts — contrato multitenant

O domínio oficial continua `rodada.ai`. A nova arquitetura planeja um subdomínio por estabelecimento e módulos no path, por exemplo:

```text
bardoaderlan.rodada.ai/bar
bardoaderlan.rodada.ai/cozinha
bardoaderlan.rodada.ai/gerencia
bardoaderlan.rodada.ai/caixa
bardoaderlan.rodada.ai/m/<token>
```

**Ainda não está habilitado.** O proxy atual usa hosts separados por superfície (`bar.rodada.ai`, `cozinha.rodada.ai` etc.). O login usa o `Venue.slug` atual `bar-do-aderlan`; não renomear esse slug para criar `bardoaderlan`. Antes de ativar wildcard, implementar registro hostname -> Venue, verificação host/sessão/guest e testes com dois Venues. Ver [ADR 0016](../../docs/adr/0016-tenant-hostname-module-paths.md) e [Spec 025](../../specs/025-tenant-host-routing/spec.md).

Rotas internas para desenvolvimento, testes e demo Railway continuam funcionando: `/staff`, `/attendance`, `/bar`, `/kitchen`, `/guest/:token`, `/manage`, `/reports`, `/cash`. Rodada Atendimento permanece Android nativo.

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
