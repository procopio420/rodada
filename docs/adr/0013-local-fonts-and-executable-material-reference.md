# ADR 0013 — Fontes locais e material visual executável

Status: aceito. Data: 2026-10-08. Spec: 022.

## Contexto

O usuário forneceu cinco HTMLs e pediu fidelidade visual. Arquivo exportado contém runtime de mockup, dados simulados e Google Fonts. Fontes de sistema variam por plataforma e não reproduzem Archivo condensada. Dependência de rede para fonte prejudica comparação e operação offline.

## Decisão

Preservar originais/assets em prototype/material-reference; variante local muda somente o link de fontes. Produto usa seu próprio código e tokens canônicos. Fontes OFL são empacotadas localmente: WOFF2 variável no Web, faces TTF com largura explícita no Android. Comparações registram viewport, dados e região; igualdade de controle não implica igualdade de tela inteira.

Products continuam donos de ProductIcon. Assets fornecidos podem ser vinculados explicitamente ao Product no banco descartável de revisão com source e auditoria; nenhum resolver por nome/fuzzy é introduzido na aplicação. Novos campos product_id/order_id da fila são projeção aditiva e permitem agregação por identidade sem alterar mutations.

## Consequências

Tipografia funciona sem rede. Runtime exportado permanece exclusivamente de teste/referência. Ações, SLA e dados simulados não entram no domínio. Android precisa de validação nativa própria; screenshot Web nunca é apresentado como prova do app.
