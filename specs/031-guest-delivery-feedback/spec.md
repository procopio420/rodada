# Spec 031 — Feedback opcional de entrega pelo cliente

**Status:** PROPOSTA / não implementado  
**Data:** 2026-10-16  
**Motivação:** medir melhor pedido → mesa sem introduzir taps obrigatórios de entrega para garçons; complementar telemetria passiva da Spec 003 e ADR 0009.

## Decisão de produto proposta

**Inverter o pedido de confirmação:** oferecer ao cliente, na PWA guest, a opção de informar que seu pedido chegou, sem exigir confirmação para continuar pedindo, consumir, pagar ou sair.

> A falta de resposta do cliente significa **desconhecido**, nunca automaticamente "entregue" nem "não entregue".

A confirmação do cliente é uma evidência de entrega útil para calibrar o modelo passivo — mas não substitui todos os sinais de staff/fulfillment e não certifica o horário físico exato da entrega.

## Fluxo principal

1. Order/OrderItem confirmado e vinculado à Tab; permanece no pipeline normal Bar/Cozinha/Dispatch.
2. Após haver itens prontos/chegando e uma janela apropriada configurável, a página **Pedidos** pode mostrar uma mensagem discreta: **"Seu pedido chegou?"**.
3. Escolhas:
   - **"Sim, chegou"** — feedback positivo para os itens/lote explicitamente mostrados.
   - **"Chegou só uma parte"** — seleção de itens/quantidades entregues, sem inferir o restante.
   - **"Ainda não"** — feedback negativo no instante da resposta, não afirma ausência de entrega posteriormente; pode orientar atenção de Dispatch com deduplicação e limiar.
   - **"Veio errado / preciso de ajuda"** — abre exceção/solicitação apropriada, sem reembolso ou cancelamento automático.
   - **Ignorar/fechar** — não gera milestone nem penalidade.
4. O cliente segue navegando por Cardápio, Pedidos e Conta sem pop-up bloqueante e sem novos destinos primários.
5. Não mostrar o prompt se não houver autorização guest válida, pedido cancelado integralmente, conflito de contexto ou ausência de elegibilidade. Não reaparecer repetidamente em cada navegação.

## Semântica dos fatos

- `READY`: estação declarou preparo concluído, **não é entrega**.
- `GUEST_CONFIRMED`: cliente autorizado **declarou** que os itens selecionados chegaram em `reported_at` (horário recebido pelo servidor); não se assume o mesmo horário de entrega real.
- `INFERRED`: entrega estimada por sinais passivos com confiança/proveniência (ADR 0009).
- `MANUAL` / `CORRECTED`: observação/correção operacional auditada existente; as fontes devem coexistir, sem apagar a origem.
- `NOT_YET`: declaração pontual de não recebimento, possível evidência contrária à inferência, não um estado financeiro ou cancelamento.
- `PARTIAL`: confirmação com escopo e quantidades explícitos, sem marcar o pedido inteiro como entregue.

**Compatibilidade:** ADR 0009 atualmente enumera `MANUAL | INFERRED | CORRECTED`. Antes do código, decidir formalmente se `GUEST_CONFIRMED` é uma nova enum `source` ou uma subcategoria de `MANUAL` com `actor_type=GUEST`. Nunca perder origem do cliente nem mascará-la como ação staff. Atualizar contratos/ADR e consumidores em conjunto, mediante revisão.

Não confundir eventos de **feedback** com transições operacionais. Um "Sim" pode registrar evidência sem avançar automaticamente o estado canônico da entrega até existir política explícita segura e reconciliada com produção/dispatch.

## Segurança, integridade e concorrência

- O servidor valida GuestSession, Venue, Table/TableOccupancy/generation, Tab e escopo do Order/OrderItem/quantidade; não confiar em IDs do browser.
- Pedido só elegível para feedback se houver evidência compatível de preparo/dispatch; não permitir declarar entregue antes de haver possibilidade operacional plausível.
- Replays idempotentes por UUID da intenção; deduplicar eventos repetidos, bloquear alteração silenciosa de payload e proteger contra envios concorrentes.
- Após liberação/revogação de sessão, rejeitar novas mutations; não transportar confirmação para ocupação/Tab seguinte.
- Preferir timestamps do servidor, guardar instante de feedback e proveniência; nunca aceitar timestamp do cliente como horário canônico físico.
- Não fazer mutações em Charge, Payment, ledger, fechamento de Tab ou reembolso.
- Feedback não expõe nomes de funcionários nem estados internos de outras Tabs/mesas.
- Correções posteriores são append-only, vinculadas ao evento original; situações conflitantes vão para exceção, nunca sobrescritas silenciosas.
- Rate limit por sessão/pedido, deduplicação de prompts e proteção contra uso indevido.

## UX e operação

- CTA opcional na lista/detalhe do pedido, priorizando a continuidade do cardápio.
- Uma pergunta por pedido/lote elegível, sem push insistente e sem pesquisa obrigatória.
- Quando a entrega ocorrer em lotes, perguntar apenas pelos itens explicitamente identificados; unidades semelhantes podem ter múltiplas quantidades.
- "Ainda não" gera no máximo uma exceção acionável por contexto/janela, sem disparar alarme no primeiro toque prematuro.
- "Veio errado" encaminha a situação para Dispatch como exceção, preservando idempotência e contexto.
- Funcionários não precisam confirmar o happy path nem "validar" cada resposta guest.
- A disponibilidade/falha dessa UI não afeta realização ou pagamento do pedido.

## Métricas, limitações e critérios do piloto

- Exibir `feedback_response_rate` e `positive_confirmation_coverage` por Venue, canal, estação e business date.
- Tempo pedido → feedback positivo **não é** igual ao tempo físico pedido → mesa. Se apresentado, rotular como "até confirmação pelo cliente", separado de medição observada e inferida.
- Mensurar taxa de resposta, entrega parcial, "ainda não", exceções e divergência com inferências anteriores.
- Não comparar diretamente tempos de respondentes com todo o universo de pedidos sem explicitar seleção e amostra.
- Estratificar por canal (guest/staff), item/lote e faixa de movimento.
- O principal valor inicial é ganhar sinal de calibração e identificar exceções; **não prometer precisão universal**.

## Fora de escopo

- Obrigatoriedade de confirmação guest ou staff.
- Alterações automáticas de cobrança/cancelamento/reembolso em resposta ao feedback.
- Novo cadastro/login, hardware BLE obrigatório, push insistente, GPS/câmeras.
- Trocar o sistema inteiro de fulfillment só para representar o feedback.
- Classificação automática de desempenho individual de garçons.

## Dependências

- `docs/adr/0009-passive-fulfillment-telemetry.md`
- `specs/003-dispatch/spec.md`
- `specs/004-table-guest-ordering/spec.md`
- `docs/product/guest-experience.md`
- `docs/product/north-star-operational-metrics.md`
