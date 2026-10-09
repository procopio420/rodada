# Aceite

## Planejamento

- [x] Plano identifica fontes, estado atual, sequência, arquivos-alvo, métricas e limites de comparação entre plataformas.

## Implementação pendente

- [ ] Cinco exports têm contratos versionados por estado, selector, dimensão, crop, fixture e hash.
- [ ] Primitives novas usam typography/axes e medidas da referência, com comparação estrita.
- [ ] Cozinha/Bar equivalentes passam assertions ≤0,1% e revisão de geometria por região; teste não é apenas auditoria.
- [ ] Atendimento, pico e recovery Android possuem evidência HTML↔Compose e gates nativos no emulador fixado.
- [ ] Fixtures reproduzem dados/relógio/assets; inconsistências do export têm derivação documentada, sem produção incorreta.
- [ ] Responsive 360/430/768 tem contratos derivados; acessibilidade, toque, foco e conteúdo longo passam.
- [ ] CI retém referência/actual/diff/overlay/stats e falha em regressão; não usa baseline atual ou masks para ocultar diferenças.
- [ ] Audit/KB registram cobertura completa e diferenças restantes; nenhuma tela sem referência é declarada pixel-perfect.

## Inventário parcial da Cozinha

- [x] Referência/hash e ambiente identificados; selector único `.k` e recortes medidos.
- [x] Estado literal e comportamento dos controles observados; estados não disponíveis explicitados.
- [x] Evidência da implementação identifica base Git, fixture, geometria e diferenças sem alegação de equivalência.
- [x] Aplicação/exports originais e branch anterior preservados; V01 global permanece pendente.

Evidências e limites: [inventário](../../docs/design/v01-kitchen-inventory.md). Somente os itens desta subseção foram verificados; os critérios globais permanecem pendentes.

## Aceite do recorte V02 — Field / StatusBadge

- [x] Field confortável: 56 px, raio 10 px, padding horizontal 16 px, Archivo 20/600, borda interna 1,5 px; foco interno 2 px papel. Label 14/800, tracking 0,1em, gap 6 px.
- [x] Controle normal/foco/placeholder compara com `.inp` atualizado em ≤0,1%, pixelmatch threshold 0.1 / includeAA false; nenhuma referência ou tolerância substituída.
- [x] StatusBadge tem diferenças e ausência de equivalências documentadas; estados operacionais preservados.
- [x] Cozinha/Bar em 360/430/768 sem overflow, labels/foco preservados; fluxo de criação/reutilização continua passando.
- [x] Typecheck/build/test registrados com evidências e limitações; branch original preservada, sem merge/push.
