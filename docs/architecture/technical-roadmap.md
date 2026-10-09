# Roadmap técnico — Rodada

Atualizado em 2026-10-08. O repositório já contém API, Web e Atendimento Android funcionais em várias slices; o próximo trabalho é completar e homologar o produto.

O [plano de implementação do produto completo](full-product-implementation-plan.md) é o documento canônico de execução. Ele substitui a sequência antiga de bootstrap, que não representava mais o código existente. Contrato e backlog: [Spec 022](../../specs/022-full-product-implementation/spec.md).

| Etapa | Resultado |
| --- | --- |
| P0 | Auditoria de critérios, contratos e fixtures |
| P1 | Outbox/SSE, replay, cache e autorização |
| P2 | Jornadas nativas e turno básico; piloto reduzido |
| P3 | Dispatch, pico e inferência com provenance |
| P4 | Financeiro completo, provider real e comprovantes |
| P5 | Guest, configuração, gerência e alertas |
| P6 | Homologação, recuperação e rollout |

P3/P4 dependem do turno básico; P5 integra ambas. Provisionamento do provider pode começar antes, mas conclusão de pagamentos exige homologação real. PostgreSQL é autoridade, HTTP confirma comandos e SSE é o padrão realtime conforme [ADR 0009](../adr/0009-http-commands-sse-realtime-outbox.md); Redis é opcional. Preservar modular monolith e Android nativo.

Não interpretar features previstas como entregues. O plano distingue código presente, lacunas, gates de piloto/produto/produção e dependências externas. Geração IA de ícones continua adiada e sensores não são pré-requisito operacional.
