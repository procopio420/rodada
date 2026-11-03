# Spec 035 — Retirada imediata no Bar

## Objetivo
Permitir que produtos sem preparo (água, lata, garrafa, etc.) sejam separados no Bar com um toque, sem passar artificialmente por **Iniciar preparo**.

## Contrato
- `Product.fulfillment_mode` distingue `PREPARE` (padrão compatível com o legado) de `PICKUP` (somente `BAR`). Escolha **por produto**, não por categoria; chope ou drink podem continuar com preparo.
- Cadastro rápido e edição gerencial expõem a escolha. A API valida estação/modo e reutilizar produto existente não reconfigura silenciosamente o produto.
- Confirmação do pedido registra o modo no `OrderItem.customization_snapshot`. Alterações posteriores do Product não mudam pedidos já confirmados; snapshots legados sem modo continuam exigindo preparo.
- Um item `PICKUP` do Bar pode ir de `NEW` ou `ACCEPTED` direto para `READY`, somente por comando validado da estação com lock, precondições de quantidade, fingerprint, sessão, capability e idempotência. Não aceita `PREPARING`.
- Item `PREPARE` preserva `NEW → PREPARING → READY` no fluxo normal. O comando por lote continua atômico: uma linha inválida rejeita todas.
- Itens mistos avançam **independentemente**, sem alterar a cobrança da Tab, criando dispatch por item pronto com o mecanismo atual. READY não significa DELIVERED: confirmação de entrega segue fluxo existente e não se força toque extra para métricas.

## Fora de escopo
- Picking de estoque, reserva física, liberação automática de mesa, baixa obrigatória de entrega e detecção automática por nome/categoria.
- Aplicação de migração em produção ou deploy nesta entrega.
