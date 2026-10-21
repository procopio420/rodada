# Spec 033 — Atendimento 2.0 no aplicativo real

**Estado: PROPOSED / CONTRACT_ONLY.** Esta spec governa a promoção da UX 2.0 da PR #212 para Atendimento Web e Android nativos, sem substituir contratos financeiros ou operacionais existentes. Base auditada: main em 16/10/2026; a PR #212 ainda é protótipo isolado e não foi homologada em dispositivo real.

## Objetivo

Um garçom deve abrir uma tarefa, chegar à comanda correta, lançar pedidos, acompanhar confirmação/produção, resolver conta e liberar mesa com o mínimo de intervenções, sem perder contexto ou duplicar operações. O resultado esperado é a **convergência de contratos canônicos entre Web/Android**, não copiar HTML literalmente, reescrever módulos ou adicionar novos fluxos.

## Invariantes

- Identity optional, Tab mandatory; Table/Occupancy é destino/contexto, jamais dona do ledger. Múltiplas Tabs por mesa e balcão sem mesa.
- Operação financeira, status de pedidos e movimentação de mesas só mudam após confirmação do servidor e readback. Não inventar pagamento, garantia, aceitação do Bar ou entrega.
- Navegação não executa claim, complete, payment, close, release ou delivery; ações positivas/destrutivas explicitam sua consequência.
- Pedido em resposta incerta mantém a intenção/fingerprint/chave originais; nunca gerar segundo Order silencioso. Erros definitivos mostram correção executável.
- Limite de consumo é política por Venue: somente o modo canônico WARN_ONLY permite aviso sem bloqueio por esse motivo isolado. A Spec 031 foi integrada nas PRs281/284; o modo efetivo e sua versão vêm do servidor. ENFORCE continua padrão seguro; rollout de produção exige autorização.
- Não exigir etapa extra de revisão antes de cada pedido; destaque para Adicionar itens, envio direto com resumo opcional, confirmação de destino e mais uma rodada de um toque após seleção.
- Atendimento, conta e entregas são áreas de trabalho distintas; o mesmo cliente pode aparecer em várias tarefas, sem que uma tarefa concluída feche outra.
- Não transformar ausência de confirmação de entrega ou inferência fraca em DELIVERED; preservar proveniência/correção por exceção. Dispatch falhando não bloqueia venda.
- Uma Tab CLOSED não libera TableOccupancy. Limpeza DIRTY → CLEANING → AVAILABLE segue o domínio e revoga a sessão Guest anterior.

## Evidência de reuso e lacunas observadas

| Superfície atual | Reuso comprovado / risco a validar | Epic owner |
| --- | --- | --- |
| apps/web/components/attendance-web.tsx e order-workspace.tsx | Já oferecem mesas/comandas, rascunho por Tab e operações. Navegação atual não é a UX 2.0; evitar reimplementar T04/T05 da Spec 026. | E01/E02 |
| apps/web/lib/client/order-intent.ts | Já persiste intenção Web e usa chave idempotente/readback. Implementar só deltas de feedback, origem/reconciliação e UX; não criar segundo hook. | E02 |
| apps/attendance-android | Compose nativo com sessão cifrada, intenção durável de pedido, pagamento parcial, entrega e mesa. Fazer port nativo, não WebView, e preservar UX recém contratada na Spec 029. | E01–E05 |
| apps/web/components/service-request-queue.tsx | Projeção SERVICE_REQUEST/BILL_REQUEST expõe label, não Tab/Occupancy navegável; precisa destino staff autorizado. | E01/E03 |
| apps/api/modules/dispatch/views.py | Fila READY tem tarefas canônicas e labels; leitura de destino precisa identificadores/versões revalidados antes do deep link. | E03 |
| Spec 002 / ADR 0011 | Hoje impõe hard limit; Spec 031/PR #215 define WARN_ONLY/ENFORCE ainda não integrado. | E05 |
| Specs 001/004/006/012/014 | Pagamento parcial, Tab CLOSED, liberação e recuperação já existem. Não implementar cobrança fictícia do protótipo. | E04 |
| Issue #106, Specs 026/029 | E2E e fricção com gates existentes: complementar evidências, não substituir suites. | E06 |

## Épicos executáveis

| Epic | Contrato detalhado | Resultado | Prioridade |
| --- | --- | --- | --- |
| E01 — Contexto e navegação | [spec](epics/E01-context-and-navigation/spec.md) / [tasks](epics/E01-context-and-navigation/tasks.md) | Agora, Mesas, Tab, busca, retorno e permissões coerentes em Web/Compose | P0 |
| E02 — Pedido confiável | [spec](epics/E02-order-loop-and-recovery/spec.md) / [tasks](epics/E02-order-loop-and-recovery/tasks.md) | Envio direto, repetir, confirmação canônica e recuperação ACK perdido | P0 |
| E03 — Agora, chamadas e entregas | [spec](epics/E03-work-queues-and-dispatch/spec.md) / [tasks](epics/E03-work-queues-and-dispatch/tasks.md) | Filas separadas, deep link ao registro certo e tarefa sem mutação por abrir | P0 |
| E04 — Conta e giro | [spec](epics/E04-settlement-and-table-turnover/spec.md) / [tasks](epics/E04-settlement-and-table-turnover/tasks.md) | Parcial/total, fechamento direto seguro, mesa/limpeza independentes | P0 |
| E05 — Perfis e política | [spec](epics/E05-customer-policy-surface/spec.md) / [tasks](epics/E05-customer-policy-surface/tasks.md) | Barra compacta, preview do draft, estado WARN_ONLY/ENFORCE canônico | P1 / depende da 031 |
| E06 — Homologação e rollout | [spec](epics/E06-integration-and-release/spec.md) / [tasks](epics/E06-integration-and-release/tasks.md) | E2E, screenshots, telemetria, feature gate e piloto com GO/NO-GO | P0 gate |

## Priorização

P0 é o circuito **Agora → contexto → pedido confirmado → conta → saída**, com falha incerta coberta. E05 é P1 de integração, mas nenhuma mudança de policy pode ir a produção sem concluir a Spec 031 e seus gates R3; em primeiro rollout pode manter a policy ENFORCE canônica sem inventar WARN_ONLY no cliente.

**Não pertencem a este fechamento:** editor e algoritmo de rota interna, DeliveryRun otimizado por mapa, pré-autorização/caução real, provider Tap to Pay não homologado, QR híbrido/FG84 (Spec 032 / issue #214), impressão Windows (Spec 028) ou marketplace de freelancers.

## Limites de execução

Esta PR terá **somente arquivos de spec/plan/tasks/acceptance**. Não alterar API, Android/Web, migrations, Railway, publicação nem flags de produção. A execução será composta de PRs menores por epic/slice, com revisão independente quando envolver ledger/auth/isolamento. Nenhum AC pode ser marcado PASS com teste de protótipo estático.

[Plano](plan.md) · [Tasks agregadas](tasks.md) · [Aceite geral](acceptance.md).

## Diretriz de execução aprovada pelo responsável — 16/10/2026

A missão de implementação e seu adendo explícito substituem os limites de PR
somente documental acima **nas branches de implementação**. A PR216 permanece
contrato draft; não pressupor seu merge. O protótipo PR212 em
`ec26e26b164692b1e22e0fc1b7c7c45d401a7ca0` é contrato visual e de interação,
não inspiração. Web React/Next e Android Compose nativo devem reproduzir layout,
cores, tipos, medidas, hierarquia, jornadas e número de intervenções. Adaptação
de componentes existentes deve alcançar a referência; não redesenhar por conveniência.
Diferenças inerentes à plataforma são permitidas. Simulações de pagamentos,
policy, routing e confirmação devem ser substituídas por fatos canônicos sem
simular sucesso. Divergências técnicas devem ser documentadas antes da resolução;
diferenças intencionais exigem aprovação explícita. Nada autoriza merge/deploy.
Cada épico exige jornada executada e capturas comparáveis protótipo/Web/Compose
360/390/430 e desktop aplicável, matriz de paridade e regressões por SHA/dispositivo.
