# V03 parcial — fixture e comparação da Cozinha

Verificação: 09/10/2026. Base isolada da main `742faac639adc998f3a4da6d8af485b407317851`, branch `codex/v03-kitchen-fixture`. Escopo: somente testes e documentação; aplicação, CSS, API e referências em disco intactos.

## Entrega e reuso

- Contrato registrado antes do harness: [dados e normalizações](v03-kitchen-comparison-contract.md).
- Modelo compartilhado test-only: `apps/web/tests/visual/kitchen-scenario.ts`; adapters para DTOs reais e dados do export atualizado.
- Reutilizados `fixture`, `stable`, servidores e o comparador pixelmatch de `parity.spec.ts`. O helper fixture ganhou apenas uma opção de horário; default dos testes anteriores preservado.
- Um teste novo na suíte existente verifica produtos/identidades, quantidades, estados, horários, fontes, assets, derivações e estabilidade. Os testes de agregação por identidade, transições, disponibilidade e primitivos permanecem intactos.
- Branch original `codex/ux-operational-polish` limpa e preservada em `6e2f4ca4f386f6ee54325cbff2fdf09b05bef597`. As entregas locais V01 (`c909c93`) e V02 (`4c0b15d`) não foram mescladas nesta base ou sobrescritas. Sem merge, push, PR ou publicação.

## Comparação com dados equivalentes

Relógio congelado em `2026-10-09T02:14:00Z` (23:14 em São Paulo). 5 Orders / 6 OrderItems aguardando, 2 READY e 1 PICKED_UP. Resumo: Fritas 4, Bolinho de bacalhau 2, Calabresa 2. READY e PICKED_UP não entram na soma aguardando preparo.

O literal contém totais inconsistentes, incluindo Torresmo já retirado no resumo. A derivação corrige somente dados: contadores, quantidades, chips, nomes, estados/ação de P37 e texto de retirada; preserva templates e estilos originais. Equipamentos, zonas, clientes, metas e barras ilustrativas que não existem no DTO continuam diferenças expostas; nenhum desses dados foi inventado na aplicação.

P08 permanece um ticket agrupado no export, com Fritas e Calabresa. A aplicação mantém duas linhas por OrderItem e transições individuais. P44 fica no layout original do passe na referência, mas em Em entrega na aplicação; ambos representam PICKED_UP. Essa diferença estrutural permanece visível.

[Literal preservado](evidence/v03-kitchen/v03-kitchen-literal.png), [referência derivada](evidence/v03-kitchen/v03-kitchen-reference.png), [aplicação](evidence/v03-kitchen/v03-kitchen-actual.png), [lado a lado](evidence/v03-kitchen/v03-kitchen-viewport.side-by-side.png), [overlay](evidence/v03-kitchen/v03-kitchen-overlay.png), [diff](evidence/v03-kitchen/v03-kitchen-viewport.diff.png).

O arquivo `v03-kitchen-derived.html` é um snapshot do DOM derivado, não uma referência nova nem um documento executável independente. O teste o regenera a partir do export original e do modelo comum. Linhas em branco do snapshot foram limpas para versionamento; fonte, DOM capturado e imagens não foram alterados.

## Métricas e diferenças restantes

Viewport 1280×800, DPR 1. Comparador original `threshold: 0.1`, `includeAA: false`; gate de equivalência continua ≤0,1%. **Fidelidade total não passa**: 127.755 pixels / **12,4761%** divergentes. O teste V03 passa dados e determinismo, não o gate total de V04.

| Recorte nas mesmas coordenadas | Pixels divergentes | Percentual |
| --- | --- | --- |
| Header 1280×72 | 2.299 | 2,4946% |
| Resumo 420×728 | 39.409 | 12,8889% |
| Tickets 520×728 | 70.772 | 18,6951% |
| Passe 340×728 | 15.279 | 6,1728% |

As regiões usam as coordenadas da referência sem realinhar/mover a aplicação ou mascarar conteúdo. As larguras das colunas coincidem: 420/520/340. O header mede 72 nas duas páginas, mas a faixa real de conectividade desloca os painéis de y=72 para y=135 (+63 px). Esse deslocamento contribui para todos os recortes inferiores.

Diferenças observadas:

1. Faixa de reconexão e conteúdo operacional adicional não existem no export. A fixture reutiliza o SSE finito existente; sua conexão encerra e a aplicação mostra Reconectando. Não foi simulada conectividade ONLINE inexistente.
2. Header real não inventa equipamentos, meta de 12 minutos ou contagem de atraso. Há diferença de texto/contexto.
3. Resumo real mostra quantidade de OrderItems por Product; o export mostra equipamento/capacidade. Chips também diferem em altura/padding.
4. Tickets reais são por item, mostram estado e timer, sem clientes/zonas/barras/SLA que não existem na projeção atual. O export agrupa P08 e mostra esses metadados demonstrativos.
5. Passe real usa estado READY com texto/semântica próprios e seção Em entrega. O export usa alertas de espera e layout/rodapé diferentes.
6. Disponibilidade e Quick Catalog continuam presentes no produto: [captura completa](evidence/v03-kitchen/v03-kitchen-actual-full.png). Não há comparação equivalente dessas extensões no literal.

## Validação e determinismo

| Check | Resultado |
| --- | --- |
| Typecheck (`node node_modules/typescript/bin/tsc --noEmit`) | passou |
| Build (`node node_modules/next/dist/bin/next build`) | passou, Turbopack |
| test:visual (`node node_modules/playwright/cli.js test`) | 145 passaram |
| test:realtime (`node --experimental-strip-types --test tests/realtime.test.mjs`) | 8 passaram |
| Referência em disco/CSS da referência | preservados, verificados pelo teste |
| Capturas repetidas | iguais, byte a byte |
| `git diff --check` | passou |

[Resultado estruturado](evidence/v03-kitchen/v03-kitchen-contract-result.json), [estabilidade](evidence/v03-kitchen/stability.json), [log da suíte](evidence/v03-kitchen/test-visual.log), [hashes dos artefatos](evidence/v03-kitchen/sha256.json). Capturas literal/derivada/aplicação/fullPage foram iguais entre a execução focal e a suíte completa; o teste também captura dois frames idênticos de referência/aplicação em cada execução.

Ambiente: Windows, Node 24.19.0, Next 16.3.8, Playwright 1.58.2, Chromium 145.0.7632.6, pt-BR, America/Sao_Paulo. Fontes locais e SVGs foram aguardados/decodificados; os mesmos arquivos de produto abastecem as duas páginas por interceptação exclusiva do navegador. Dependências copiadas para o checkout isolado; package/lockfile intactos. Os executáveis dos scripts foram usados diretamente porque npm não está disponível no PATH.

## Limites e próximos recortes

Nenhuma escrita em banco, seed ou integração real de API/PostgreSQL foi executada. Dados demonstrativos e preço técnico do DTO estão restritos ao módulo de teste. Não houve mudança em estados, financeiro, disponibilidade, permissões ou transições de produção.

V03 dos demais exports, responsive equivalente, loading/erro, fidelidade total e V04 permanecem abertos. Próximos recortes pequenos: definir a composição de ticket por Order sem perder ações individuais; estabelecer contrato explícito para metadados ausentes; comparar separadamente a extensão de conectividade. Não esconder a faixa, inventar campos ou recalibrar o limiar para fechar essas diferenças.
