# Issue #106 — E2E-05: indisponibilidade após o carrinho

## Escopo implementado — PR #194

- Playwright testa interfaces reais **Guest QR**, **Atendimento Web** e **Bar** no mesmo Django/PostgreSQL descartável.
- Após adicionar o item ao carrinho, o Bar o torna indisponível antes do POST de confirmação chegar ao Django. O POST original é encaminhado sem mock de resposta.
- Ambas as interfaces devem receber `409 / PRODUCTS_NOT_CONFIRMABLE`; o rascunho permanece, sem novo Order nem exposição.
- `scripts/verify-issue106-unavailable.py` concilia os recibos Guest/Staff contra o mesmo SHA, Venue e PostgreSQL, exigindo produto UNAVAILABLE e zero Order/OrderItem/Charge/Payment por Tab rejeitada.
- `scripts/run-issue106-shared.sh` e o workflow de integração exigem a conciliação SQL e arquivam evidências sanitizadas.

## Evidências executadas (antes da integração da main)

**PASS no SHA `c2653671a6ca74b0e6bc92c600f7e496f8b48349`**:
- [Android](https://github.com/procopio420/rodada/actions/runs/38814395160): PASS.
- [Web](https://github.com/procopio420/rodada/actions/runs/38814395233): PASS.
- [Android real + Web + PostgreSQL](https://github.com/procopio420/rodada/actions/runs/38814395654): PASS, **11/11** cenários cross-surface no Chromium e verificação SQL independente de Guest e Web stale-cart: nenhuma Order, Item, Charge ou Payment indevida. Recovery Android→Web, idempotência, QR e caixa de teste também passaram nos gates desse run.
- Job opcional `actual-network-uplink-cut`: **SKIPPED**, não declarar PASS.

## Integração da UX de categorias (PR #195)

A main recebeu o PR #195 após a evidência acima. A resolução do conflito preserva a implementação atual de categorias/quantidades e os ajustes de testes de concorrência/QR já integrados na main; o novo teste E2E-05 de Atendimento passa a selecionar produtos pelo helper real `tests/visual/category-actions.ts`.

**Status atual: revalidação obrigatória no HEAD pós-integração.** Os resultados anteriores são válidos apenas para o SHA acima; solicitar revisão R3 em contexto independente e confirmar os checks finais antes de merge. O PR #194 cobre este slice; **não conclui** Android stale-cart/catálogo alterado em offline, integridade de pedidos já confirmados nem a matriz E2E-01..14 da issue #106. Não inferir homologação física, PSP ou fiscal.
