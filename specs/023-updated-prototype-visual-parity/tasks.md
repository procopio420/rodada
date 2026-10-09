# Tasks

## Continuação completa — demo importante

- [ ] V01: contratos/jornadas principais dos cinco exports e fontes atuais.
- [ ] V02: componentes essenciais com diferenças comprovadas e contrato.
- [ ] V03–V04: comparação atual Cozinha/Bar e comandos individuais.
- [ ] V05: jornadas existentes Android, header/contas/pedido/cobrança.
- [ ] V06: pico/reconexão e feedback honesto.
- [ ] Responsivo/acessibilidade internos360/390/430 e fonte1/2.
- [ ] V07: gates atuais e roteiro integrado PostgreSQL/emulador.
- [ ] Evidências/limites, commits pequenos e PR rascunho atualizado.

## Recorte atual V01 — night/Agora e Bar

- [x] Auditar V01–V07 e sobreposição de PRs contra main45c4742.
- [x] Congelar contrato parcial antes de implementação; preservar fontes originais.
- [x] Medir Agora/Bar, regiões e tipografia com seletores únicos e capturas repetidas.
- [x] Validar hashes/assets/fontes; revisar imagens e documentar ambiente/limites.
- [x] Commit e publicação remota com PR rascunho, sem conclusão global.

Resultado parcial: [V01 Agora/Bar](../../docs/design/v01-night-agora-inventory.md), evidência bc9575b publicada no [PR68 em rascunho](https://github.com/procopio420/rodada/pull/68). V01 global permanece aberto.

- [x] Documentar plano especÃ­fico de pixel-perfect e corrigir o foco da documentaÃ§Ã£o.
- [ ] V01: inventÃ¡rio e contratos por tela/estado/recorte.
- [ ] V02: medidas, tokens e componentes atualizados Web/Compose.
- [ ] V03: fixtures equivalentes e normalizaÃ§Ãµes rastreÃ¡veis.
- [ ] V04: composiÃ§Ã£o fiel de Cozinha/Bar e assertions completas.
- [ ] V05: shell/jornadas Android e screenshots contra referÃªncia.
- [ ] V06: pico e conectividade em todos os estados demonstrados.
- [ ] V07: gates CI, contratos responsivos e relatório final de cobertura.

## V01 parcial — apenas Cozinha

- [x] Conferir Git e preparar checkout isolado da main `1dfdf8a`, preservando `6e2f4ca`.
- [x] Identificar hashes, estados, interações, dimensões e recortes literais.
- [x] Capturar/medir a implementação da main e identificar extensões sem referência.
- [x] Registrar evidências e ajustes pequenos, sem concluir V01 dos cinco exports.

Evidências e limites: [inventário](../../docs/design/v01-kitchen-inventory.md). Somente os itens desta subseção foram verificados; os critérios globais permanecem pendentes.

## Recorte V02 — Field / StatusBadge

- [x] Medir e registrar Field atual/atualizado e limites de equivalência de StatusBadge.
- [x] Promover variante confortável com tokens e aplicar somente no Quick Catalog.
- [x] Comparar normal/foco/placeholder do controle contra CSS atualizado imutável; conservar gates compactos.
- [x] Verificar Cozinha e Bar adjacente e executar typecheck/build/test.

Este checklist não conclui V02 global nem V01.

## V03 parcial — Cozinha

- [x] Contrato prévio com fonte, dados e normalizações explícitas.
- [x] Modelo comum e adapters test-only reutilizam fixture/comparador existentes.
- [x] Dados equivalentes e captures determinísticas verificados.
- [x] Comparação literal/derivada/aplicação e diferenças documentadas.
- [x] Typecheck/build/test executados e resultados registrados.

V03 global e V04 continuam abertos.

## V04 parcial — agrupamento de tickets

- [x] Contrato e design system atualizados antes do código.
- [x] Agrupamento apenas por identidade de Order; fallback independente para DTO antigo.
- [x] Estado/tempo/customização/ação por OrderItem preservados; transition isolada comprovada.
- [x] Geometria e tela adjacente verificadas; comparação V03 mantém fontes/tolerâncias.
- [x] Typecheck/build/test e diferenças documentados.

Este recorte não conclui V04 global nem declara fidelidade total.

Resultados: [relatório V04 parcial](../../docs/design/v04-kitchen-tickets.md).

- [ ] V07: gates CI, contratos responsivos e relatÃ³rio final de cobertura.

## V05 parcial â€” navegaÃ§Ã£o do Atendimento

- [x] Contrato antes do cÃ³digo e tokens documentados.
- [x] Composable integrado sem alterar comandos.
- [x] ReferÃªncia e Android comparados por regiÃ£o.
- [x] Unit/build/lint/instrumentaÃ§Ã£o e limitaÃ§Ãµes documentados.

Contrato: [V05](../../docs/design/v05-atendimento-shell-contract.md). V05 global permanece aberta.

Resultado: [relatório parcial](../../docs/design/v05-atendimento-shell.md).

## Continuação — integração e navegação acessível

- [x] Contrato de adaptação e integração registrado antes do código.
- [x] Matriz 360/390/430, fonte 1/2 e overflow de texto verificados/corrigidos.
- [x] Gate impede aceitar XML antigo/nenhum teste executado.
- [x] Typecheck/build/Web/realtime e Android unit/build/lint/instrumentação integrados passam.
- [x] Inventário e branches publicados com commits verificados.

Resultado: [validação integrada](../../docs/design/spec023-review.md).

## V02 parcial — hierarquia da Gerência

- [x] Base isolada da main atual e fontes/ausência de export próprio identificadas.
- [x] Capturar antes/depois com fixture equivalente e documentar diferenças.
- [x] Promover ícones/medidas/tokens, preservar cinco destinos e Impressoras em Mais.
- [x] Hierarquia financeira e sectionHeader sem alterar dados ou exceções.
- [x] Verificar alvo/foco/fonte ampliada, comparação de ícone e telas adjacentes.
- [x] Executar gates e registrar commit/evidências/limites, sem conclusão global023.

Resultado deste recorte: [evidências e limites](../../docs/design/spec023-management-hierarchy.md). Gates locais passaram; não conclui V02 ou023 global.

## Acabamento de todas as telas Web

- [x] Conferir Git/main ae416da, branch original e contrato antes do código.
- [x] Inventariar cobertura de todas as rotas e preservar documentos impressos.
- [x] Reutilizar ícones/headings/tokens em telas e componentes compartilhados.
- [x] Melhorar identificação de navegação e hierarquia de tickets sem mudar comandos.
- [x] Verificar matriz visual, estados, acessibilidade, adjacentes e API/PostgreSQL.
- [x] Registrar capturas, cobertura, limites, commits e PR; atualizar prévia isolada.

Resultado: [cobertura, evidências e limites](../../docs/design/spec023-all-web-hierarchy.md). Acabamento compartilhado entregue; Spec023 global permanece aberta.
