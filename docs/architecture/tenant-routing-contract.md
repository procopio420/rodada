# Public routing contract — Rodada multiestabelecimento

**Atualizado:** 2026-10-13. **Decisão canônica:** `rodada.bar` ([ADR 0018](../adr/0018-rodada-bar-canonical-domain.md)). **Importante:** contrato de domínio e código mergeado **não são** certificado de DNS/TLS público nem homologação de piloto.

O hostname identifica o estabelecimento (Venue); o path identifica o módulo. `bardoaderlan` é um alias externo para o `Venue.slug` interno `bar-do-aderlan`, sem alterar seu ID.

| Uso | URL canônica desejada | Rota interna compatível |
| --- | --- | --- |
| Site institucional | `https://rodada.bar/` | `apps/landing` |
| Entrada / staff do Aderlan | `https://bardoaderlan.rodada.bar/` | `/staff` |
| Atendimento Web | `https://bardoaderlan.rodada.bar/atendimento` | `/attendance` |
| Bar | `https://bardoaderlan.rodada.bar/bar` | `/bar` |
| Cozinha | `https://bardoaderlan.rodada.bar/cozinha` | `/kitchen` |
| Gerência | `https://bardoaderlan.rodada.bar/gerencia` | `/manage` |
| Caixa | `https://bardoaderlan.rodada.bar/caixa` | `/cash` |
| Relatórios | `https://bardoaderlan.rodada.bar/relatorios` | `/reports` |
| Guest QR | `https://bardoaderlan.rodada.bar/m/<opaque-token>` | `/guest/<opaque-token>` |
| API técnica compartilhada | `https://api.rodada.bar/` | Django API, sujeito a deploy/ingress |
| Admin da plataforma (futuro) | `https://admin.rodada.bar/` | Não implementado |

## Fluxo de confiança

```text
HTTPS / ingress confiável
  → Host normalizado, reservado/verificado e VenueDomain → Venue UUID
  → Next BFF same-origin e prova assinada ao Django
  → sessão staff / guest / tokens / cookies correspondem ao Venue
  → Django autoriza capability e consulta/ação com scoping por Venue
```

A presença de `Host` **não autentica**. Headers controlados pelo navegador (`X-Forwarded-Host`, `X-Rodada-*`, query `venue`) não escolhem Venue. Desconhecido/inativo falha fechado; token guest de outro Venue não revela existência. Não usar labels do domínio como slug de banco.

## Estado de implementação vs rollout

- **Código:** PR [#116](https://github.com/procopio420/rodada/pull/116) mergeado em 13/10, acrescentando sessão/BFF/guest vinculados a host, aliases e testes; `RODADA_ENABLE_TENANT_HOST_UI` controla liberação ampliada. PR [#101](https://github.com/procopio420/rodada/pull/101) ainda aberto na fotografia inicial desta atualização; não presumir que seus commits foram todos incorporados.
- **Ambiente:** wildcard DNS, TLS, forwarded headers e isolamento de dois Venues no deploy real devem ser observados e registrados; ainda não certificados por este documento.
- **Compatibilidade:** preservar Railway e localhost, rotas internas/Android e QR antigo enquanto migração não tiver aceite. Não redirecionar tokens de QR entre domínios nem compartilhar cookies entre subdomínios.

Critérios de aceite: [Spec 025](../../specs/025-tenant-host-routing/spec.md), [acceptance](../../specs/025-tenant-host-routing/acceptance.md), [preview/rollback](../ops/spec025-preview-rollout.md). Decisão arquitetural original de hostname por Venue em [ADR 0016](../adr/0016-tenant-hostname-module-paths.md); troca de raiz em ADR 0018.

## Auditoria P0 de 14/10/2026

#101 está fechado sem merge; #131 (SSE) e #140 (caixa/idempotência) estão
integrados e foram reutilizados. A [matriz #130](../../specs/025-tenant-host-routing/audit-130-evidence.md)
explicita todas as fronteiras, evidências por SHA e controles públicos:
imagens efetivamente publicadas são públicas; recibos por token são capabilities
portáveis read-only com TTL/revogação; gestão continua escopada ao Venue.
O hardening de código valida authorities assinadas e segredos production/pilot,
e converte erro de mismatch no OAuth em403 antes de qualquer troca.
Preview421 mantém #151/#130 bloqueados; CI/review de código não autorizam wildcard.
