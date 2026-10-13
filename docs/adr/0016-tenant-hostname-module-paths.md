> **Supersessão parcial em 2026-10-13:** a [ADR 0018](0018-rodada-bar-canonical-domain.md) substitui `rodada.ai` por `rodada.bar` nos hosts públicos. A decisão **host por Venue e path por módulo** permanece vigente; o texto abaixo é preservado como registro da decisão original.

# ADR 0016 — Tenant no hostname; superfície no path

**Status:** Accepted (architecture contract; rollout not implemented)
**Date:** 2026-10-12
**Supersedes:** Routing/host portion of ADR 0010 and Spec 019. ADR 0010 still defines Rodada branding and `rodada.ai`.

## Contexto

A versão anterior atribui subdomínios à superfície (`cozinha.rodada.ai`, `gerencia.rodada.ai`). Isso escala mal para SaaS multitenant: um hostname passa a descrever a função, não o estabelecimento, e a separação de sessão/QR entre bares fica implícita.

O backend atual já tem `Venue(id, slug)`, memberships e StaffSession por Venue; `Venue.slug=bar-do-aderlan` é usado no seed e no login. **Não existe ainda um modelo Tenant/Organization nem um registro de domínios públicos por Venue.**

## Decisão

**Hostname identifica o estabelecimento; pathname seleciona a experiência de produto.** O domínio público canônico permanece `rodada.ai` até uma decisão explícita sobre outro domínio.

```text
rodada.ai                              site público
admin.rodada.ai                        control plane da Rodada (futuro)
api.rodada.ai                          API (entrada técnica, não namespace de estabelecimento)
bardoaderlan.rodada.ai                 entrada do Bar do Aderlan
bardoaderlan.rodada.ai/atendimento     Atendimento Web auxiliar; Android continua nativo
bardoaderlan.rodada.ai/bar             Bar
bardoaderlan.rodada.ai/cozinha         Cozinha
bardoaderlan.rodada.ai/gerencia        Gerência
bardoaderlan.rodada.ai/caixa           Caixa
bardoaderlan.rodada.ai/m/<token>       QR / guest
```

`bardoaderlan` é **hostname público desejado**, não substitui o `Venue.slug` interno `bar-do-aderlan`. A resolução autoritativa será `hostname normalizado -> Venue.id` por registro persistente, sem inferir `Venue.slug` da label. Entradas desconhecidas, bloqueadas, inválidas ou suspensas falham fechadas, sem cair em outro Venue ou no demo.

Na primeira migração, `Venue` permanece o escopo operacional e de isolamento já existente; cada Venue pode operar como 1:1 com a conta SaaS. Uma futura `Organization/Tenant` para faturamento, redes e múltiplas unidades será explícita e **não** deve redefinir ownership de Tab, Payment, Order ou memberships sem spec. Desde já reservar a distinção: `Tenant/Organization` = entidade contratante futura; `Venue` = unidade física operacional.

## Roteamento da Web

O gateway resolve `Host` usando uma lista de hosts reservados e um registro validado. Apenas depois de resolver o Venue seleciona o módulo do path. O path não altera o Venue; adicionar `?venue=`, headers enviados pelo browser ou trocar módulos jamais troca de estabelecimento.

| Path público | Entry point interno atual | Nota |
| --- | --- | --- |
| `/` | `/staff` | entrada/login contextual |
| `/atendimento` | `/attendance` | companheiro Web; Android permanece separado |
| `/cozinha/*` | `/kitchen/*` | preservar subpaths e query string |
| `/bar/*` | `/bar/*` | mantém nome |
| `/gerencia/*` | `/manage/*` | preservar subpaths e query string |
| `/caixa/*` | `/cash/*` | fechamento/turnos |
| `/m/:token` | `/guest/:token` | token opaco, nunca ID de mesa |
| `/relatorios/*` | `/reports/*` | relatório gerencial |
| `/configuracoes/*` | ainda não definido | não anunciar tela inexistente |

Paths internos continuam possíveis em localhost/Railway e como aliases temporários. Redirecionamentos canônicos de hosts antigos só devem acontecer depois que a sessão/QR estiver vinculada ao Venue e **nunca** devem copiar cookies, credenciais ou tokens na URL. `atendimento.rodada.ai`, `bar.rodada.ai`, `cozinha.rodada.ai`, `cliente.rodada.ai`, `pedido.rodada.ai`, `gerencia.rodada.ai`, `app.rodada.ai` são hosts reservados de compatibilidade, não slugs de novos bares.

## Isolamento e autenticação

1. O gateway aceita apenas hostnames explícitos e normalizados de uma autoridade de entrada confiável. Não confiar em `X-Forwarded-Host` de cliente externo; configurar proxy/ingress para sobrescrever headers forwarded. Rejeitar aliases homógrafos, host malformado, portas indevidas e domínios sósia.
2. Uma sessão staff tem um único `StaffSession.venue_id`; para **cada** chamada autenticada, `resolved_host_venue_id == session.venue_id` é pré-condição, independentemente de role ou UI. Falha = `VENUE_HOST_MISMATCH` (403), sem dados de outro Venue. Login e refresh devem observar o mesmo vínculo.
3. Backend segue autoritativo: endpoints filtram pelo Venue autenticado, revalidam memberships/capabilities/dispositivo; `tenant_id`, `venue_id`, headers ou token guest enviados pelo cliente não podem escolher escopo.
4. QR/GuestSession/mesa/comanda são validados contra o Venue do hostname. Token válido de outro estabelecimento deve se comportar como não encontrado (404, sem revelar existência).
5. Cookies staff e guest são **host-only**, `Secure`, `HttpOnly` quando aplicável, `SameSite` apropriado. Nunca `Domain=.rodada.ai`. `api.rodada.ai` não deve receber cookie do estabelecimento; Web usa BFF same-origin.
6. SSE, outbox, jobs, imports, PSP credentials, pagamentos, auditoria e relatórios carregam Venue explicitamente. Não permitir troca de tenant por reconnect/replay, idempotency key reaproveitada ou cursor de feed.
7. `Host` serve ao contexto de roteamento e a uma **restrição adicional**, não autentica o usuário. Resolver o host sem sessão é permitido somente para experiência pública do Venue.
8. Provisionamento e mudança de hostname exigem unicidade, nomes reservados, trilha de auditoria, políticas de ativação/desativação e verificação antes de custom domains.

## Provisionamento e deploy

Um deployment Next + Django compartilhado e PostgreSQL compartilhado com scoping por Venue. No futuro, domínio próprio pode apontar para Venue por mapeamento verificado. DNS wildcard e certificado TLS wildcard cobrem `*.rodada.ai`; DNS não prova que uma label pertence a um Venue. `admin.rodada.ai` deve ter autorização de plataforma separada da gerência de um bar.

## Migração sem quebra da demo

1. Adicionar registro persistente de host -> Venue e resolver com testes de fail-closed.
2. Acrescentar binding host/session/guest no BFF + API **antes** de ligar wildcard.
3. Testar em preview/staging com dois Venues, usando `bardoaderlan` como alias de `bar-do-aderlan`, sem alterar slug nem seed.
4. Habilitar public paths/manifest por estabelecimento atrás de rollout controlado; manter os paths locais e URLs Railway ativos.
5. Atualizar QR, links, deep links e documentação depois de validar E2E e segurança; manter aliases legados por período de transição.
6. Só então alterar DNS/HTTPS de produção e migrar hosts antigos com observabilidade/rollback.

**Este ADR não afirma que o wildcard DNS, certificados, lookup de hostname, proteção de sessão ou novos URLs estão implementados ou publicados.** Ver Spec 025.
