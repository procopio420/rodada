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

Os testes iniciam servidores de produção próprios: execute o build antes. A suíte visual tem 87 testes nas oito telas, cinco larguras e estados de operação; usa respostas controladas somente nos testes. A integração tem quatro testes de navegador com BFF e Django reais.

Antes da integração, na raiz do repositório: `python -m pip install -e "apps/api[dev]"`. O banco local é SQLite temporário; CI usa PostgreSQL 17 isolado. Se Python não estiver no PATH, defina `RODADA_TEST_PYTHON` com o caminho completo do executável. No PowerShell: `$env:RODADA_TEST_PYTHON='C:\caminho\python.exe'`. Reserve as portas 3100 (visual), 3110 e 8100 (integração).

O [relatório de paridade](../../docs/design/visual-parity-audit.md) registra métricas, cobertura e limitações. Quick Catalog continua indisponível. O cliente vê os pedidos confirmados nesta sessão; a API atual não fornece histórico completo nem acompanhamento ao vivo após recarregar. O crédito pessoal do desenvolvedor foi removido do rodapé.

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
```

Rotas locais são detalhe de implementação e não definem URLs públicas. O runtime/deploy pode resolver a superfície pelo hostname mantendo um único codebase/deploy Next.js.

`app.rodada.ai` e `pedido.rodada.ai` são aliases de compatibilidade durante a migração. Não criar aliases públicos como `kitchen.rodada.ai`, `owner.rodada.ai` ou `guest.rodada.ai` sem decisão arquitetural.

Compartilhar auth, contratos e design primitives não significa transformar todas as funções em um único frontend escondido por role.

## Design

A implementação consome os tokens semânticos de `docs/design/system.md`: fundo/superfícies quentes, alto contraste, acento âmbar, estados semanticamente consistentes e targets de toque de pelo menos 44 px.

O protótipo continua como referência visual, não como fonte de regra de domínio.


## Invalidação de acesso

Enquanto uma sessão staff está ativa, o Web/PWA consulta o invalidation feed em intervalo bounded. Mudança de role/device força nova leitura de `/auth/me` e limpa qualquer janela de reauth recente. Falha do feed não bloqueia operação: a API continua autoritativa em todas as mutations.
