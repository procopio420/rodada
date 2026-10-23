# Spec 035 — Contratos, decisões e drift do KDS

**Inventário estático:** main ad45892c54b3d8f7bc0e6ccd53a0c26bfb111d90 em 22/10/2026. **Não é evidência de execução de testes**. Atualizar SHA/status em cada PR.

## 1. Mapa da implementação encontrada

| Domínio | Evidência/arquivo | Preservar | Gap para a UX 2.0 |
| --- | --- | --- | --- |
| UI Bar/Cozinha | apps/web/components/production-board.tsx, componente compartilhado Station BAR/KITCHEN | filtros, readback, sessão staff e autorização | nova hierarquia ticket-first, abas e paridade |
| Transições | mapa NEW/ACCEPTED→PREPARING, PREPARING→READY no ProductionBoard | API decide validade; não fingir sucesso | comando READY direto para produto imediato |
| Pedidos | /api/pos/production/{station}/; snapshot Item com Order/Tab/quantity | Tab canônica, station, customização, IDs estáveis | projection/agrupamento/timer e filtros Passe |
| Batch | useProductionBatchIntent + ADR 0018-idempotent-production-batches | atomicidade, receipt, versão e replay | conectar CTA e compatibilidade do protótipo |
| Item intents | useProductionItemIntents / journal local | mesma key/payload, readback após ACK ambíguo | não capturar IDs obsoletos após SSE |
| SSE/cache | useRealtime, projection-cache | cache não é confirmação; timer e leitura separadas | stale state e aviso global persistente |
| Correções | Spec 017 | manager, motivo, estágio e financeiro | aprovação parcial/remake e notificação real |
| Disponibilidade | useAvailabilityIntents | versão por Venue, autorização | área de Ajustes com visual equivalente |
| Delivery/pickup | Specs 003, 031-guest-delivery-feedback, 032-guest-entry-and-bar-pickup | READY≠PICKED_UP≠DELIVERED; provenance | Passe antigo, código FG84, expedição filtrada |
| Printer | Specs 015 e 028 | status real, incerto≠impresso | ação contextual de impressão/reprint |
| Design | docs/design/system.md, Spec 023 | tokens e UX comum do Rodada | fixture comparável + gate visual rígido |

## 2. Política de produto imediato — decisão de contrato pendente de engenharia

Separar **fulfillment_station** BAR/KITCHEN de **preparation_policy** IMMEDIATE_PICKUP/PREPARED e de **order fulfillment_mode** AT_TABLE/PICKUP. Política é atribuída pelo Venue a Product/variant quando aplicável, versionada e congelada no snapshot; itens confirmados seguem o snapshot. Não inferir estado por string, categoria ou prefixo da URL.

Desejado: comando server-side autoritativo de conclusão rápida para IMMEDIATE_PICKUP com idempotency key, fingerprint, expected_version, atomic commit, audit, Dispatch, receipt terminal e readback. Endpoint/nome exato dependem da revisão de API. Do NOT chain NEW→PREPARING e depois READY no browser sob timeout. PREPARED continua no fluxo tradicional. Diante de política desconhecida/ausente, fallback para etapas explícitas, sem atalho.

**Importante:** Spec 032 define modalidade PICKUP independente de estação. A UI BAR só gerencia itens BAR; KITCHEN só gerencia KITCHEN; o destino de retirada pode existir para ambos conforme setup operacional. Um FG84 não concede acesso nem confirma quitação.

## 3. Decisões a formalizar antes das slices de domínio

- DC-01: local de armazenamento/default da política IMMEDIATE_PICKUP; migração de produtos existentes e compatibilidade de API/clients antigos.
- DC-02: comando idempotente de READY direto, isolamento por Venue, auth/capability, concorrência/readback e interações com ADR 0018.
- DC-03: quantidades parciais (entidade/unidade/split), Dispatch, correções e ledger; sem simular "1 pronto" com contador local.
- DC-04: AllergyHold/auditoria/permissões; tratar impossibilidade de preparar como bloqueio canônico, não toast.
- DC-05: nova observação versus evento de correção, acknowledgment, resiliência e dedupe por ID.
- DC-06: expedição opt-in por Venue e consulta cruzada segura de BAR+KITCHEN; busca e filtro por Order ID, Tab ID e pickup group, nunca só mesa.
- DC-07: limiar de SLA, som, fonte e impressão; propriedades locais vs Venue; replay/retention de prontos antigos.

## 4. Invariantes negativos de segurança

- Jamais eliminar comanda porque a mesa mudou ou outro pedido chegou.
- Jamais aplicar lote a linhas distintas em alergia, modificadores, status, tenant, versão ou correção pendente.
- Jamais transformar READY em prova de retirada física ou entrega.
- Jamais tratar código de ficha público como segredo, permissão ou prova de pagamento.
- Jamais reaplicar mutação com key nova diante de ACK perdido nem mudar key/payload em retry.
- Jamais mostrar produto novo indisponível como aprovado ou remover item previamente confirmado por alteração de catálogo.
- Jamais confundir UI lock com persistência de bloqueio alérgico; controle definitivo vem do servidor.
