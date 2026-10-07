# Spec 001 — Core POS

**Status:** Draft for implementation

## Objetivo

Entregar o núcleo de PDV próprio do Rodada: catálogo, tab/comanda, pedido, cobrança, pagamento manual e fechamento, sem depender de mesa fixa.

## Usuários

- Staff: lança pedidos e recebe pagamentos.
- Cashier: fecha tabs e opera caixa.
- Manager: cancela/ajusta com auditoria.

## Histórias

### POS-001 — Abrir tab

Staff abre Tab anônima ou ligada a Customer/Relationship. ServicePoint é opcional.

### POS-002 — Catálogo

Produtos têm nome, preço, ativo/inativo e `fulfillment_station`.

### POS-003 — Criar pedido

Staff adiciona produtos a uma Tab e confirma Order.

### POS-004 — Snapshot de preço

OrderItem captura preço no momento da confirmação; alteração posterior no catálogo não altera pedido existente.

### POS-005 — Gerar charges

Itens confirmados geram charges idempotentes no ledger.

### POS-006 — Estados operacionais

OrderItem suporta estados mínimos `NEW`, `ACCEPTED`, `PREPARING`, `READY`, `PICKED_UP`, `DELIVERED`, `CANCELLED`.

### POS-007 — Cancelamento

Cancelamento após confirmação exige permissão e trilha de auditoria; ledger recebe reversão/adjustment em vez de apagar histórico.

### POS-008 — Receber pagamento

Registrar `CASH`, `CARD`, `PIX` ou `OTHER`; P0 aceita confirmação manual.

### POS-009 — Fechar tab

Tab fecha normalmente com exposure zero. Divergência exige manager action.

### POS-010 — Caixa

CashShift registra abertura, recebimentos por método, ajustes e fechamento resumido.

### POS-011 — Localização flexível

Tab pode mudar de ServicePoint/Zone sem alterar pedidos, ledger ou customer.

## Fora de escopo

- fiscal/NFC-e;
- estoque profundo;
- delivery/iFood;
- PSP real;
- pré-autorização;
- dispatch automático;
- loyalty.

## Requisitos não funcionais

- fluxo mobile-first;
- interface operacional de alto contraste, legível sob baixa luz e com alvos de toque generosos;
- superfícies principais organizadas como `Agora`, `Pedir`, `Contas` e `Caixa`;
- modo pico reduz a fila operacional ao essencial, priorizando itens mais antigos;
- perda de conectividade deve ficar explícita; pedidos e recebimentos em dinheiro ficam em fila persistente e sincronizam com idempotência, enquanto Pix e cartão aguardam conexão;
- tela de produção deve evidenciar idade, destino e estado de cada item, com visão dedicada de cozinha;
- dinheiro em centavos;
- mutations transacionais;
- auditoria para cancelamento/ajuste;
- pedido comum deve ser lançável em poucos toques;
- API desenhada para realtime posterior.
