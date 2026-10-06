# AGENTS.md — Rodada

Este repositório é desenvolvido de forma **spec-driven**.

## Regra principal

**Não implemente uma feature relevante antes de existir uma especificação que descreva comportamento, regras, fora de escopo e critérios de aceite.**

Código implementa specs. Código não é a fonte primária de intenção de produto.

## Ordem de leitura

Antes de alterar comportamento:

1. `README.md`
2. `docs/product/vision.md`
3. `docs/product/principles.md`
4. `docs/design/system.md`
5. `docs/architecture/overview.md`
6. `docs/domain/model.md`
7. spec relevante em `specs/`
8. ADRs relacionados em `docs/adr/`

## Workflow

1. Identifique a spec existente ou crie uma pasta numerada em `specs/`.
2. Atualize `spec.md` antes do código.
3. Registre decisões arquiteturais duráveis em `docs/adr/`.
4. Mantenha `plan.md` com abordagem de implementação.
5. Quebre execução em `tasks.md`.
6. Defina critérios verificáveis em `acceptance.md`.
7. Implemente a menor vertical slice que satisfaça um critério de aceite.
8. Adicione testes alinhados aos critérios.
9. Atualize a spec se a descoberta durante implementação mudar o contrato.

## Guardrails de produto

- Rodada **é um PDV próprio**, não apenas uma integração com PDV existente.
- Não transformar Rodada num ERP genérico antes de validar o núcleo operacional.
- **Identity optional, Tab mandatory.**
- `Tab`/comanda é a unidade operacional/financeira; não depende de mesa física.
- Pedido pertence a `Tab`, nunca diretamente a `Table`.
- `Product.active` representa configuração/publicação de catálogo; indisponibilidade durante a operação é estado separado e auditável.
- Disponibilidade operacional é uma fonte de verdade compartilhada: staff, caixa e guest não podem confirmar item indisponível.
- A API deve validar disponibilidade novamente na confirmação do pedido; UI desabilitada sozinha não é garantia.
- Tornar item indisponível não altera nem cancela `OrderItem` já confirmado.
- Uma `TableOccupancy` pode conter várias Tabs.
- Fechar a última Tab não deve, sozinho, encerrar `TableOccupancy`.
- Mesa/localização é contexto mutável, não identidade financeira.
- QR físico de mesa identifica a mesa por token opaco; nunca usar IDs sequenciais públicos como `/mesa/24`.
- Uma foto/URL antiga não deve manter uma sessão guest válida depois que a ocupação for liberada; usar geração/epoch e revogação.
- Guest ordering precisa poder ser bloqueado imediatamente pelo staff sem bloquear pedidos internos.
- Cliente não deve precisar instalar app ou criar conta para pedir no fluxo básico.
- Perfil Rodada, NFC, código curto e sessão do dispositivo são identificadores/acessos à mesma Tab, não novos tipos de conta.
- NFC é conveniência operacional; não tratar UID simples como prova forte de identidade.
- Não exigir CPF no fluxo básico.
- Não chamar relacionamento de “score de crédito” na UX.
- Não automatizar promoção/rebaixamento de relacionamento sem spec explícita.
- Dispatch é parte do núcleo operacional, não um add-on cosmético.
- Não acoplar pagamentos a um provider específico no domínio central.
- Pagamentos devem ser idempotentes e auditáveis.
- Override de limite deve registrar ator, horário, valor anterior, novo valor e motivo opcional.
- “Cliente da casa” é uma relação local entre cliente e estabelecimento.
- Fiscal, estoque profundo, delivery e loyalty não entram por reflexo: precisam de spec própria e justificativa.

## Convenções de domínio

- **Venue**: estabelecimento.
- **StaffMember**: usuário operacional.
- **Customer**: pessoa identificada opcionalmente.
- **Relationship**: relação Customer ↔ Venue.
- **Tab**: sessão operacional/financeira de consumo; unidade obrigatória para pedidos.
- **TabIdentifier**: identificador técnico opcional para resolver/acessar uma Tab, como código curto, guest session, QR dinâmico ou NFC.
- **Table**: recurso físico do salão com estado operacional e QR próprio.
- **TableOccupancy**: período em que um grupo usa uma Table; pode conter várias Tabs.
- **ServicePoint**: ponto/localização operacional genérico, opcional, especialmente para dispatch fora de mesa.
- **Zone**: agrupamento operacional de pontos.
- **FulfillmentStation**: destino operacional de preparo, como `BAR` ou `KITCHEN`.
- **Product**: item configurado no catálogo com preço e routing.
- **ProductAvailability**: estado operacional vendável/não vendável de Product, separado de ativação administrativa e auditável.
- **Order**: solicitação operacional de itens sempre ligada a uma Tab.
- **OrderItem**: item individual com rota/estado próprios quando necessário.
- **Task**: unidade de trabalho despachável.
- **Charge**: lançamento financeiro positivo derivado ou manual.
- **Payment**: valor recebido.
- **Adjustment**: cortesia/correção/reversão.
- **Open Exposure**: valor efetivamente aberto.
- **Operating Limit**: exposição máxima sem ação adicional.

## Guardrails de design

- Toda superfície do produto deve seguir `docs/design/system.md`.
- PDV, Cozinha/Bar, Dispatch, Conta da Casa, Table Ops e Guest Ordering são módulos do mesmo produto; não criar identidades visuais independentes.
- Reutilizar tokens e componentes semânticos antes de introduzir novos padrões.
- Estados de domínio devem manter a mesma semântica visual entre superfícies: neutral, info, warning, success e danger.
- Quick Catalog/AI Icons deve usar os mesmos Field, Button, ProductIcon, StatusBadge e feedbacks do restante do Rodada.
- Assets gerados por IA seguem `docs/product/icon-style.md`; estado visual de disponibilidade/seleção fica na UI.
- Não usar hex, spacing, radius ou sombra ad hoc em componentes de produto sem atualizar o design system.
- A experiência base é mobile-first (360–430 px), touch-first e otimizada para operação de pico.
- Não depender de hover; alvo de toque mínimo de 44 px e estado de foco visível.
- Evitar visual de SaaS genérico, glassmorphism, dashboards decorativos e cards sem função operacional.
- Protótipos e implementação real devem compartilhar o mesmo vocabulário de componentes e tokens.
- Antes de aceitar uma nova tela, revisar consistência com pelo menos uma superfície adjacente do fluxo.

## Qualidade financeira

Toda regra financeira precisa de:

- teste unitário;
- idempotência quando houver evento externo;
- trilha de auditoria;
- valores monetários em centavos, nunca `float`;
- transação de banco quando alterar saldo/exposição.

## Qualidade operacional

Mudanças de disponibilidade de produto devem registrar ator, horário, estado anterior, novo estado e motivo opcional.

Mudanças de estado em pedido/task devem registrar timestamps suficientes para medir:

- pedido → aceito;
- aceito → pronto;
- pronto → retirado;
- retirado → entregue;
- chamada → claim → concluída.

Mudanças de mesa/ocupação devem registrar timestamps suficientes para medir:

- ocupação iniciada;
- mesa liberada;
- início de limpeza;
- mesa novamente disponível.

Toda mutation relevante deve responder:

- quem fez;
- o que mudou;
- quando;
- por quê, quando aplicável.

## Commits/PRs

Preferir commits pequenos por slice. PR deve apontar para a spec e indicar quais critérios de aceite passam após a mudança.
