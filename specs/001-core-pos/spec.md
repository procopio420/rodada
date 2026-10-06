# Spec 001 — Core POS

**Status:** Draft for implementation

## Objetivo

Entregar o núcleo de PDV próprio do Rodada: catálogo, Tab/comanda, pedido, cobrança, pagamento manual e fechamento, sem depender de mesa fixa e sem codificar localização como identidade financeira.

## Usuários

- Staff: cria/encontra Tabs, lança pedidos e recebe pagamentos.
- Cashier: fecha Tabs e opera caixa.
- Manager: cancela/ajusta com auditoria e gerencia disponibilidade global.
- Bar/Cozinha: acompanha produção e pode marcar itens da própria estação como disponíveis/indisponíveis quando autorizado.

## Invariantes

- todo Order pertence a uma Tab;
- Tab pode existir sem Customer, Table ou ServicePoint;
- Tab pode ter `display_label` humano sem que isso seja identidade forte;
- Table nunca é dona do ledger;
- várias Tabs podem compartilhar a mesma TableOccupancy;
- fechar Tab não libera mesa automaticamente;
- o domínio deve aceitar identificadores adicionais de Tab sem migrar ledger/pedidos;
- disponibilidade operacional de produto é separada de `Product.active`;
- todos os canais revalidam a mesma disponibilidade na confirmação do pedido;
- mudança de disponibilidade nunca reescreve pedido já confirmado.

## Histórias

### POS-001 — Abrir Tab

Staff abre Tab anônima, com label/apelido ou ligada a Customer/Relationship. Localização é opcional.

### POS-002 — Catálogo

Produtos têm nome, preço, ativação administrativa e `fulfillment_station`. `active` controla configuração/publicação; não deve ser usado como indisponibilidade operacional de curto prazo.

### POS-003 — Criar pedido

Staff adiciona produtos a uma Tab e confirma Order.

### POS-004 — Snapshot de preço

OrderItem captura preço no momento da confirmação; alteração posterior no catálogo não altera pedido existente.

### POS-005 — Gerar charges

Itens confirmados geram charges idempotentes no ledger da Tab.

### POS-006 — Estados operacionais

OrderItem suporta estados mínimos `NEW`, `ACCEPTED`, `PREPARING`, `READY`, `PICKED_UP`, `DELIVERED`, `CANCELLED`.

### POS-007 — Cancelamento

Cancelamento após confirmação exige permissão e trilha de auditoria; ledger recebe reversão/adjustment em vez de apagar histórico.

### POS-008 — Receber pagamento

Registrar `CASH`, `CARD`, `PIX` ou `OTHER`; P0 aceita confirmação manual.

### POS-009 — Fechar Tab

Tab fecha normalmente com exposure zero. Divergência exige manager action.

### POS-010 — Caixa

CashShift registra abertura, recebimentos por método, ajustes e fechamento resumido.

### POS-011 — Localização flexível

Tab pode se associar/desassociar de ServicePoint ou TableOccupancy sem alterar pedidos, ledger ou Customer.

### POS-012 — Múltiplas Tabs no mesmo contexto físico

Duas ou mais Tabs podem coexistir no mesmo TableOccupancy sem compartilhar saldo, pagamentos ou fechamento.

### POS-013 — Disponibilidade operacional

Bar/Cozinha com permissão pode marcar Product da sua estação como `AVAILABLE` ou `UNAVAILABLE`. Manager pode alterar qualquer produto.

A mutation registra ator, horário, valor anterior, novo valor e motivo opcional.

### POS-014 — Uma fonte de verdade

Menus de staff, caixa e guest usam a mesma disponibilidade operacional. Um Product indisponível aparece claramente como indisponível e não pode gerar novo item confirmado.

### POS-015 — Revalidação na confirmação

A API valida disponibilidade ao confirmar o Order. Se o produto ficou indisponível depois de entrar no carrinho, a confirmação falha para os itens afetados com resposta explícita para atualização do carrinho.

OrderItem já confirmado não é cancelado ou alterado por mudança posterior de disponibilidade.

## Fora de escopo

- fiscal/NFC-e;
- estoque profundo e baixa automática por insumo;
- delivery/iFood;
- PSP real;
- pré-autorização;
- dispatch automático;
- guest ordering completo;
- lifecycle/limpeza de mesa;
- NFC/QR de acesso;
- loyalty.

Esses comportamentos de mesa/guest são detalhados em `specs/004-table-guest-ordering/`.

## Requisitos não funcionais

- fluxo mobile-first;
- dinheiro em centavos;
- mutations transacionais;
- auditoria para cancelamento/ajuste;
- pedido comum deve ser lançável em poucos toques;
- API desenhada para realtime posterior;
- não expor IDs sequenciais como credenciais públicas.
