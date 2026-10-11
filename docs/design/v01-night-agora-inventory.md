# Spec 023 — V01 Agora e Bar adjacente

Data: 09/10/2026. Base `45c4742b3de4e6a21ed607342f75e53e18b07d7d`, branch isolada `codex/spec023-next`. Recorte documental e de inspeção executável: contrato ausente do estado inicial night, sem alteração de produto. Spec/plano/tasks/aceite registrados antes do harness.

## Auditoria V01–V07 na base atual

Presença de código foi conferida na main atual. Resultados abaixo atribuídos a relatórios anteriores **não foram reexecutados** e não são validação atual desse produto.

| Etapa | Entrega encontrada | Pendência prioritária |
| --- | --- | --- |
| V01 | `kitchen/visual-contract.json`, inventário/capturas da Cozinha; manifesto dos cinco exports | Contratos completos de night/system/peak/connectivity e estados restantes. Este recorte acrescenta somente night inicial/Bar. |
| V02 | Field confortável/StatusBadge, OperationalHeading/Icon, hierarquia Web, tokens e navegação Compose presentes | Medidas e comparisons das demais primitives; header/linhas/tipografia Compose. Não refazer acabamento entregue. |
| V03 | `kitchen-scenario.ts`, adapters test-only e derivação rastreável da Cozinha | Fixtures equivalentes dos demais exports e estados; night literal não é DTO/API real. |
| V04 | ProductionBoard agrupa por Order, mantém ações por item, lote/fila/passe e Quick Catalog | Comparação integral/regiões ainda não atende 0,1%; relatório V04 registrou tickets16,6898% em sua base. Dados ausentes e faixa de conexão permanecem diferenças documentadas. |
| V05 | AttendanceNavigation, adaptação fonte ampliada e testes instrumentados; AttendanceScreen usa Header/TabList/TabWorkspace reais | Agora/Contas/detalhe/pedido/cobrança, um por vez, com referência equivalente; não há baseline nativa integral aprovada. |
| V06 | Pico e callbacks de conectividade/revalidação presentes em AttendanceScreen | Evidência de todos os estados HTML↔Compose e confirmação canônica de recovery. Código presente não conclui aceite visual. |
| V07 | Suítes Web/Android e relatórios parciais existentes | Gates nativos de regressão, contratos responsivos/fonte ampliada internos e roteiro integrado na composição atual. Não repetir resultados históricos como atuais. |

Fontes auditadas: [plano canônico](pixel-perfect-implementation-plan.md), [revisão integrada](spec023-review.md), [acabamento Web](spec023-all-web-hierarchy.md), [V03](v03-kitchen-comparison.md), [V04](v04-kitchen-tickets.md), [V05](v05-atendimento-shell.md). O plano canônico conserva seus números iniciais como histórico; esta tabela separa o código integrado das lacunas ainda abertas.

## Git, sobreposição e serviços

Remoto confirmado `procopio420/rodada`; fetch antes da criação do checkout. Main local estava em7227f7d, origin/main45c4742. Base usada foi origin/main, sem atualizar main local ou mover a branch do usuário. Branch original `codex/ux-operational-polish` conserva6e2f4ca e seu diretório `.worktrees/` preexistente. Worktrees anteriores V01–V05, revisão, demo e near-ready preservadas. Nenhum commit de Lucas foi substituído.

Consulta de PRs abertos identificou [PR61](https://github.com/procopio420/rodada/pull/61): demo/sessão/apresentação Web em base própria. Sobreposição documental/visual registrada; não reaplicar acabamento ou importar correções dessa branch. O recorte atual acrescenta contrato/harness, sem tocar seus arquivos de produto. Sem merge/force push/produção.

Serviços encontrados escutando: demo Web3119/API18764, prévia Web3123/API8123 e PostgreSQL55459. Nenhum deles foi reiniciado ou consultado para mutations. O harness abriu e encerrou exclusivamente seu próprio servidor estático em porta efêmera. Nenhum acesso ao banco, seed, pagamento ou alteração no histórico; pagamentos manuais/de teste mantêm sua identificação existente.

## Contrato e evidência atual

[Contrato](../../prototype/references/night/visual-contract.json), [medidas/fontes/assets/hashes](evidence/v01-night-agora/measurements.json), [telefone literal](evidence/v01-night-agora/phone.png), [conteúdo Agora](evidence/v01-night-agora/screen.png), [navegação](evidence/v01-night-agora/navigation.png), [Bar adjacente](evidence/v01-night-agora/bar.png).

| Região | Seletor | Dimensão observada |
| --- | --- | --- |
| Telefone | `.phone` | 390×844, posição410/40 no artboard |
| Header do produto | `.phone .top` | 390×60 |
| Conteúdo Agora | `.phone .screen` | 390×700 |
| Navegação | `.phone .nav` | 390×84 |
| Bar adjacente | `.kds` | 820×864, posição840/40 |
| Header Bar | `.kds .kh` | 820×68 |
| Produção Bar | `.kds .kcol.l` | 471,0625×796 |
| Bancada/espelho | `.kds .kcol:not(.l)` | 348,9375×796 |

Título Agora: Archivo46/900/wdth68%, line-height41,4px. Destino da primeira linha:30/850/wdth76%. Age: JetBrains Mono22/800. Ação:92×56, Archivo18/850/wdth84%. Estes valores são medidas da referência, não novos tokens aprovados. A região counters mostra2prontos/1chamando/1conta; Bar mostra4preparando/3na bancada. Nomes/valores do mockup permanecem exclusivamente nesta evidência de teste.

O header `.top` é conteúdo do produto. Não existe status bar de sistema simulada nesse estado inicial; não reservar uma faixa fake no Android por analogia. Rail/legendas/sombra externa são apresentação. A captura phone mantém o arredondamento literal do aparelho; screen/header/navigation fornecem recortes separados. Nenhuma captura vira baseline nativa.

Revisão visual observou limites do próprio export: a quarta linha continua por scroll atrás da navegação; bancada do Bar possui textos estreitos/quebrados. O valor do contador tem fontSize computado40px mas bounding box14px e raster pequeno no runtime, portanto CSS declarado e saída desenhada devem ser tratados separadamente antes de promover essa primitive. Não corrigir silenciosamente o original nem copiar comportamento inconsistente para produção.

Na implementação Android, Agora recebe `TabList(showDeliveries=true)` e mostra entregas/contas; a referência contém também chamadas, sugestão de run e estados de ownership. São diferenças de estrutura/dados; não autorizar criação de capacidades nesta Spec023. No Web, Bar usa ProductionBoard de três regiões compartilhadas com Cozinha, enquanto este export Bar tem duas colunas e espelho. Comparação exige um contrato derivado de dados/regiões antes de qualquer alegação integral.

## Verificação e reprodução

Executar, a partir do checkout com dependências Web disponíveis: `node scripts/spec023-night-inventory.cjs`. `RODADA_PLAYWRIGHT_PATH` pode apontar para o Playwright já instalado; `PLAYWRIGHT_BROWSERS_PATH` permite reutilizar os browsers locais. Nenhuma dependência nova ou instalação no projeto do usuário.

PASS atual: cinco ZIPs correspondem ao manifesto;88 arquivos ZIP/HTML/runtime/assets e3 arquivos de fontes locais têm hashes registrados e conferidos antes/depois;16 seletores únicos medidos; cinco pares de capturas byte-idênticas; fontes Archivo/JetBrains Mono carregadas; recursos HTTP200; nenhum pageerror ou requisição externa. PNGs revisados visualmente. Duas execuções independentes reproduziram o JSON completo e os hashes das capturas. Sintaxe do script e `git diff --check` passaram.

Ambiente: Windows, Node24.19.0, Playwright1.58.2, Chromium145.0.7632.6, viewport1760×1060, DPR1, pt-BR, America/Sao_Paulo. Clock pausado antes da navegação em2026-10-09T00:38:00Z; relógio literal21:38. Captura desabilita animação/caret; HTML/dados/estilos/fontes originais intactos. O export importado já referencia `prototype/fonts/fonts.css`; nenhuma substituição de stylesheet foi necessária.

Tentativas iniciais: sandbox bloqueou localhost; execução autorizada fora dele. Título uppercase exigiu textContent em vez de innerText; seletor da primeira linha exige `:nth-match` porque wrappers do runtime não permitem nth-of-type1. A ordem de conclusão das requisições variou entre execuções, portanto a lista de recursos no JSON é ordenada por caminho; pixels e dados não foram normalizados. Corrigido o harness; asserts de unicidade/estabilidade/fontes permaneceram. Nenhuma tolerância foi aumentada.

Typecheck/build/test:visual/test:realtime de produto, Android/emulador/hardware e integração PostgreSQL **não executados**: este recorte altera somente contrato/documentação e inspeção de referências, sem UI ou fluxo integrado. Não há nova prova de demo funcional ou fidelidade atual do app; V07 segue aberto.

Próximo recorte: V01 night **Contas/busca → detalhe da Tab**, congelando seletores/interações/medidas dessa única jornada antes de V02/V05. System/peak/connectivity também precisam seus contratos; nenhuma conclusão global da Spec023.

## Publicação

Contrato/harness/evidências versionados em `bc9575b0c99a7a8c9b55aae0a3b50a56e772d429`; SHA remoto confirmado por ls-remote. [PR68 em rascunho](https://github.com/procopio420/rodada/pull/68), base main45c4742. Este registro posterior só documenta publicação/aceite; não muda pixels ou implementação. CI remoto não foi tratado como validação concluída.
