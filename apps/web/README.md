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
npm install
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
```

## Superfícies

Continuam conceitualmente separadas por função:

```text
/staff      PDV, Tabs, pedidos, mesas
/bar        produção + disponibilidade
/kitchen    produção + disponibilidade
/guest      QR/PWA do cliente
/owner      gerência e configuração
```

Compartilhar auth, contratos e design primitives não significa transformar todas as funções em um único frontend escondido por role.

## Design

A implementação consome os tokens semânticos de `docs/design/system.md`: fundo/superfícies quentes, alto contraste, acento âmbar, estados semanticamente consistentes e targets de toque de pelo menos 44 px.

O protótipo continua como referência visual, não como fonte de regra de domínio.
