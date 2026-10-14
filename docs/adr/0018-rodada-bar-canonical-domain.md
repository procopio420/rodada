# ADR 0018 — `rodada.bar` como domínio público canônico

**Status:** Accepted (decisão de marca e arquitetura; rollout sujeito a aceite)  
**Data:** 2026-10-13  
**Supersedes:** o domínio raiz `rodada.ai` da [ADR 0010](0010-brand-and-canonical-domains.md) e as referências a esse domínio na [ADR 0016](0016-tenant-hostname-module-paths.md). Não altera a decisão **Venue no hostname, módulo no path**.

## Contexto

O produto evoluiu da proposta `rodada.ai` para o domínio `rodada.bar`, já adotado pelo site estático, páginas de política e links da marca. O piloto utiliza o alias público desejado `bardoaderlan.rodada.bar`; ele **não** renomeia `Venue.slug=bar-do-aderlan`.

Documentos anteriores podem mencionar `rodada.ai` por motivos históricos e compatibilidade. Isso não os torna instrução de novo provisionamento.

## Decisão

- Institucional: `https://rodada.bar/`; `www.rodada.bar` é um redirect configurável.
- Host do estabelecimento: `https://<alias-verificado>.rodada.bar/`; módulo no path (`/atendimento`, `/bar`, `/cozinha`, `/caixa`, `/gerencia`, `/relatorios`, `/m/:token`).
- Exemplo de piloto: `https://bardoaderlan.rodada.bar/`.
- API técnica planejada: `https://api.rodada.bar/`. O host técnico **não** é um Venue.
- `admin.rodada.bar` fica reservado para plataforma futura, sem prometer a rota.
- A marca permanece **Rodada**; identidade visual não é redecidida por esta ADR (ver design system e guia de branding).

## Restrições inegociáveis

- Uma única infraestrutura compartilhada pode servir vários Venues; hostname é contexto adicional, não autenticação.
- `VenueDomain` mapeia hostname normalizado/validado para `Venue.id`; nunca inferir UUID ou slug de string do Host.
- Autorização, staff/guest session, pagamentos, filas/SSE, idempotência e eventos permanecem particionados por Venue.
- Cookies host-only; proibir propagação de tokens entre domínios em redirects/QR. Headers forwarded devem ser sanitizados no edge.
- Não habilitar public wildcard, criar redirects automáticos de QR, editar DNS ou prometer HTTPS até evidência de TLS, isolamento E2E, rollback e aceite no deploy real.
- Referências a `rodada.ai` podem permanecer apenas como **histórico** e aliases explicitamente documentados após verificação; não as anunciar como URLs novas canônicas.

## Migração documental e operacional

Atualizar README, guia Web, contrato de rotas e docs de deploy para `rodada.bar`. Manter ADRs 0010 e 0016 com banner de supersessão em vez de apagá-las ou trocar datas históricas. Para hosts legados verificar necessidade, controle do domínio, cookies e planos de redirecionamento; nada migra automaticamente.

**Aceite de roteamento/deploy:** [Spec 025](../../specs/025-tenant-host-routing/spec.md), [matriz](../../specs/025-tenant-host-routing/acceptance.md), [runbook de preview](../ops/spec025-preview-rollout.md). Escolher `rodada.bar` **não** declara wildcard ou Certificado TLS em funcionamento.
