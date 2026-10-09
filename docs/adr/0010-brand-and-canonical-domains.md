# ADR 0010 — Marca Rodada e domínios canônicos

**Status:** Accepted  
**Date:** 2026-10-07

## Decisão

A marca canônica é **Rodada** e o domínio canônico é **`rodada.ai`**.

A frase **“Me vê uma rodada aí.”** pode ser usada como assinatura/campanha de marca, mas não substitui Rodada como nome do produto.

## Hosts públicos canônicos

| Superfície | Host |
| --- | --- |
| Institucional | `rodada.ai` |
| Rodada Gerência | `gerencia.rodada.ai` |
| Rodada Cozinha | `cozinha.rodada.ai` |
| Rodada Bar | `bar.rodada.ai` |
| Rodada Cliente / QR | `cliente.rodada.ai` |
| API | `api.rodada.ai` |
| Rodada Atendimento | Android nativo; sem host web canônico |

Os subdomínios representam superfícies especializadas do mesmo produto, não backends, bancos ou domínios independentes. Cozinha, Bar, Cliente e Gerência podem compartilhar `apps/web` e o mesmo deployment; o hostname pode selecionar a superfície correta.

Paths internos como `/owner`, `/kitchen`, `/bar`, `/guest` e `/staff` podem continuar existindo para desenvolvimento, testes ou routing interno, mas não são o contrato público de URL.

`app.rodada.ai` e `pedido.rodada.ai` são aliases de compatibilidade para Gerência
e Cliente, respectivamente, conforme Spec 019 e o contrato já implementado.
Não criar aliases públicos como `kitchen.rodada.ai`, `owner.rodada.ai`,
`guest.rodada.ai`, `management.rodada.ai` ou `staff.rodada.ai` sem nova decisão explícita.

## Guardrail

Implementações futuras devem tratar **Rodada + `rodada.ai` + os hosts desta ADR** como contrato de produto.

Qualquer novo host público, renomeação de superfície ou mudança do domínio raiz exige atualização desta ADR.
