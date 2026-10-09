# Spec 023 — V02 parcial: Field e StatusBadge Web

Data: 09/10/2026. Base: `origin/main` em `742faac639adc998f3a4da6d8af485b407317851`. Branch isolada: `codex/v02-field-status-badge`.

## Resultado e escopo

Corrigido somente o Field confortável do Quick Catalog de Cozinha e Bar: nome/combobox e preço. Reutiliza a estrutura Field e tokens compartilhados. Os campos compactos existentes e StatusBadge continuam com seus contratos anteriores. Spec, plano, tarefas, aceite e design system foram atualizados antes do CSS/componente.

A branch do usuário `codex/ux-operational-polish` permanece limpa em `6e2f4ca4f386f6ee54325cbff2fdf09b05bef597`. A entrega V01 local permanece em `codex/v01-kitchen-inventory`, commit `c909c93fe5168ef39efd54123e82c09a9ba42c74`; não foi incorporada ou sobrescrita. Esta entrega não faz merge, push, PR ou publicação.

## O que já estava entregue

A main contém as integrações #44, #45 e #46. Field compacto já tinha labels associados, controle mínimo 44 px, foco âmbar e autocomplete acessível no Quick Catalog. StatusBadge já usava texto + estado semântico, raio 4 px e estados de disponibilidade. Os gates antigos de Field e badge comparavam `prototype/index.html` / `prototype/design-system.css`; continuam intactos e aprovados. Eles não comprovavam o export atualizado.

## Fontes e medidas

| Fonte | Hash SHA256 |
| --- | --- |
| ZIP Atendimento atualizado | `10f5b7ce9a749094e9bb6adbdd09ac5eb26e3571fd82cce805f9b3f880d95e28` |
| HTML executável Atendimento com fontes locais | `912b59ca1bfc6f0f7c92927ac6e0d8f4f663963f34f7adbb6a228e48c98d0a2f` |
| ZIP Sistema atualizado | `34d0afb8517b4ead16c2d787b70a5ac13bc3eee3f118d5dcffd1853323715e70` |

Fontes executadas: `prototype/references/night/Main.dc.html`, `.inp` e `.fld`; `prototype/references/system/Sistema.dc.html`, `.rel`/`.casa`. ZIPs conferidos contra o manifest, sem alterações nas referências. A suíte adicional fixa o hash do ZIP Atendimento.

| Field | Atual antes | Referência / depois |
| --- | --- | --- |
| Altura do controle | 44 px | 56 px |
| Raio | 8 px | 10 px |
| Padding horizontal | 12 px | 16 px |
| Archivo | 15 px / 500 | 20 px / 600, largura 100% |
| Borda | externa 1 px | interna 1,5 px, border-strong |
| Foco | borda âmbar + halo | interno 2 px, text/papel |
| Placeholder | padrão do navegador | text-subtle |
| Label | 12 px / 800, tracking 0,04em | 14 px / 800, tracking 0,1em |
| Gap label/controle | 4 px | 6 px |

[Medidas antes](evidence/v02-field-status/before/normal.measurements.json), [medidas depois](evidence/v02-field-status/after/normal.measurements.json), [label e badges](evidence/v02-field-status/after/label-badge-inventory.json).

A variante `fieldComfortable` aplica essas medidas apenas ao Quick Catalog. Cores, altura, padding e escala de texto reutilizam tokens existentes; raio, espessuras, gap e tracking foram promovidos ao design system. Não altera event handlers, payloads, API/BFF, disponibilidade, permissões, ledger ou regras financeiras.

## StatusBadge: comparação e limite

Disponível no Web mede 28 px, raio 4, texto 12/900. Regular/Conhecido do Sistema medem 28 px, raio 4, texto 14/800 e tracking 0,09em. A primeira amostra Da Casa no swatch recebe override de texto 15 px; o selo na seção de componentes usa 14 px. Essa diferença de tipografia foi registrada, não copiada automaticamente.

`.badge` de Atendimento é contador de navegação. `.rel`/`.casa` indicam relacionamento. NOVO indica pedido recente. Nenhum é equivalente a ProductAvailability. Sem contrato atualizado explícito para Disponível/Indisponível, alterar seu tamanho/cor como se fossem esses selos seria uma extrapolação. StatusBadge foi inventariado e preservado; sua paridade atualizada completa permanece não verificada.

## Evidência visual e normalização

O teste usa o CSS executável atualizado imutável, com fixture `.inp` dentro de `.stage`; o lado Web clona o controle real do Quick Catalog com suas classes. Normaliza somente largura 320 px, valor Fritas e placeholder Nome ou apelido. Exclui ícone/padding de busca, moldura do telefone e dados do demo. Label fica fora do crop do input e tem medidas verificadas separadamente. Não replica telas com screenshots nem introduz rota de UI de teste.

O crop antes inclui arredondamento da coordenada vertical do label; a medida geométrica do controle era 44 px. Não redimensionamos a imagem para equipará-la a 56 px.

| Estado do controle | Pixels divergentes | Percentual |
| --- | --- | --- |
| Normal | 0 | 0% |
| Foco | 0 | 0% |
| Placeholder | 0 | 0% |

Pixelmatch `threshold: 0.1`, `includeAA: false`; limite ≤0,1%. Também verifica altura, raio, padding, borda, sombra, tipografia e cores. Nenhum limiar ou teste antigo foi relaxado.

[Normal lado a lado](evidence/v02-field-status/after/normal.side-by-side.png), [foco](evidence/v02-field-status/after/focus.side-by-side.png), [placeholder](evidence/v02-field-status/after/placeholder.side-by-side.png). A pasta inclui reference/actual/diff/overlay/stats. Os nove crops reference/actual/diff tiveram hashes idênticos na repetição serial: [estabilidade](evidence/v02-field-status/stability.json).

Cozinha e Bar adjacente passaram layout/acessibilidade em 360, 430 e 768 px: sem overflow horizontal, alvos mínimos 44 px e Field 56 px. Screenshots usam fixtures existentes, relógio fixo e API interceptada; não representam dados de uma operação real.

- [Cozinha 360](evidence/v02-field-status/after/kitchen-360.png) / [Bar 360](evidence/v02-field-status/after/bar-360.png)
- [Cozinha 430](evidence/v02-field-status/after/kitchen-430.png) / [Bar 430](evidence/v02-field-status/after/bar-430.png)
- [Cozinha 768](evidence/v02-field-status/after/kitchen-768.png) / [Bar 768](evidence/v02-field-status/after/bar-768.png)

## Validação

Ambiente: Windows, Node 24.19.0, Next 16.3.8, Playwright 1.58.2, Chromium 145.0.7632.6, DPR 1, pt-BR, America/Sao_Paulo. Dependências locais foram copiadas para a base isolada; package/lockfile não mudaram. npm não estava disponível no PATH; foram executados os mesmos executáveis dos scripts declarados.

| Check | Resultado |
| --- | --- |
| `node node_modules/typescript/bin/tsc --noEmit` | passou |
| `node node_modules/next/dist/bin/next build` | passou, Turbopack |
| `node node_modules/playwright/cli.js test` (test:visual) | 151 passaram |
| Recorte após acrescentar assertions geométricas/hash e artefatos | 7 passaram em execução serial |
| `node --experimental-strip-types --test tests/realtime.test.mjs` | 8 passaram |
| `git diff --check` | passou |

[Log completo](evidence/v02-field-status/v02-all.log), [repetição serial](evidence/v02-field-status/v02-repeat-serial.log). A medição anterior falhou no gate de altura (44 versus 56), como esperado. Um primeiro harness de acessibilidade exigiu contexto explícito, corrigido sem retirar assertions. Uma repetição simultânea colidiu no diretório de artefatos Playwright e teve timeout; foi repetida serialmente, sem aumentar timeout, e passou. Esses problemas não foram tratados como aprovação.

## Limitações e próximos ajustes pequenos

- V02 global, Compose e paridade de telas completas permanecem abertos. Este recorte não conclui V01.
- Não foi executada integração com backend real ou PostgreSQL nesta mudança de CSS/classes; os fluxos operacionais foram verificados pelas fixtures e testes Web existentes.
- Disabled/erro e textos extensos passam os gates existentes, mas não possuem referência atualizada equivalente neste recorte; não são declarados pixel-perfect.
- Próximo ajuste pequeno: definir um contrato atualizado explícito de StatusBadge de disponibilidade, com success/danger, antes de mudar sua tipografia.
- Próximo ajuste pequeno: medir os Fields compactos de uma tela específica antes de estender a variante confortável; não migrar globalmente por suposição.
