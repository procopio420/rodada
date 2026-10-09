# V03 parcial — contrato de comparação da Cozinha

Contrato registrado antes das alterações de teste, em 09/10/2026. Base isolada origin/main `742faac639adc998f3a4da6d8af485b407317851`, branch `codex/v03-kitchen-fixture`.

## Fonte e recorte

Export atualizado `prototype/references/kitchen/Cozinha.dc.html`, ZIP SHA256 `ffa32367f3a04131922f75f2d7ebb4968c92e01451c7c32d6e4be1a94d428e63`. Literal intacto capturado antes da derivação. Conteúdo comum: fixture test-only; produção recebe os DTOs pelo harness HTTP existente.

1280×800 px, DPR 1, pt-BR, America/Sao_Paulo, relógio 2026-10-09T02:14:00Z (08/10 às 23:14). Archivo e JetBrains Mono locais; icons usam exatamente os SVGs do export por interceptação de requests do navegador, sem publicar assets de teste. Captura de viewport mantém header, conectividade e conteúdo real; captura fullPage adicional conserva disponibilidade/Quick Catalog. Sem máscaras ou mudanças no CSS da referência/aplicação.

## Cenário compartilhado

| Order/Tab | Produto | Qtd | Estado | Idade do pedido | Idade no passe |
| --- | --- | --- | --- | --- | --- |
| P22 | Bolinho de bacalhau | 2 | PREPARING | 13:10 | — |
| P08 | Fritas | 1 | PREPARING | 9:22 | — |
| P08 | Calabresa | 1 | PREPARING | 9:22 | — |
| P25 | Fritas | 2 | PREPARING | 6:15 | — |
| P41 | Calabresa | 1 | PREPARING | 4:10 | — |
| P37 | Fritas | 1 | NEW | 0:31 | — |
| P12 | Calabresa | 1 | READY | 15:00 | 3:40 |
| B4 | Bolinho de bacalhau | 1 | READY | 10:00 | 1:20 |
| P44 | Torresmo | 1 | PICKED_UP | 8:00 | 2:00 antes da retirada |

Resumo coerente: Fritas 4, Bolinho de bacalhau 2, Calabresa 2; 5 Orders / 6 OrderItems em preparo. READY: 2; PICKED_UP: 1, fora do resumo e do contador de prontos. O DTO mantém product_id e order_id explícitos; produtos distintos não são agrupados por nome. Horários são derivados por subtração ao mesmo now, sem timers/SLA de produção inventados. Idades criadas para linhas no passe são apenas contexto da fixture, pois o export informa somente ready age nessas linhas.

## Derivação enumerada

1. Header 6 pedidos → 5 (Orders aguardando); 3 no passe → 2 READY. Relógio 23:14 mantido. Meta/equipamento/alerta de atraso originais permanecem visíveis como diferenças sem contrato real.
2. Resumo reconstruído a partir de waiting: remove Torresmo que está retirado, Bolinho 3→2 e chips de Calabresa P41/P12→P08/P41. Nome canônico Bolinho de bacalhau nas duas páginas. Classes/estilos/templates originais preservados.
3. Tickets permanecem agrupados por Order no export: P08 contém dois itens; app continua duas linhas por item. Rótulos/dados/timers vêm do mesmo cenário. P37 NEW mantém NOVO e botão recebe Aceitar; demais PREPARING mantêm Pronto. Nenhuma mutation coletiva adicionada à aplicação.
4. Passe contém dois READY com tempos 3:40 e 1:20; P44 recebe texto Retirada registrada, sem Carlos/avatar que o DTO não comprova. A referência mantém essa linha na composição original, identificada como PICKED_UP; app a coloca em Em entrega. Essa diferença estrutural fica exposta.
5. Equipamento, zonas e clientes demonstrativos dos tickets não entram no DTO: o export ainda os mostra e isso permanece uma diferença documentada, não um campo de produção inventado.
6. Animação/caret são estabilizados pelo helper de teste existente, fontes/images aguardadas; nenhum layout de produção é substituído por markup exportado.

## Reuso e gates

Manter testes de geometria, identidade Product, transições individuais, disponibilidade e primitivos. O comparador de parity.spec.ts conserva threshold 0.1/includeAA false e limiar existente ≤0,1%. O novo recorte valida dados/tempo/assets/estabilidade e registra diferença integral e por região; não transforma esse diagnóstico em aprovação de fidelidade. V04 deverá corrigir composição antes do gate de equivalência total.

Aplicação/CSS/API sem alterações. Não há seed, request real de criação, import de fixture em produção ou mudança em estados canônicos.
