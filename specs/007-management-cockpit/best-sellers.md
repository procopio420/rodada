# Agora — Mais vendidos (2026-10-23)

## Contrato
Refinamento visual solicitado em 2026-10-23: seletor interno compacto sem duas
caixas concorrentes; status de conexão em badge textual, cabeçalho com noite,
estado vazio centralizado com ícone e orientação. Data da noite, horário e
ação de atualizar no cabeçalho. O cálculo fica documentado nesta spec.

Adicionar seletor interno Resumo / Mais vendidos ao painel Agora, preservando
alertas e cinco destinos globais. Reutilizar componentes, cores e tipografia.
Mais vendidos mostra os dez produtos com maior quantidade bruta lançada na
noite (dia operacional retornado pela API, com fuso e corte do Venue).
Usar calendar e reports existentes, protegidos por management.reports.read.
Agregar snapshots do mesmo product_id; nome histórico da primeira linha do
relatório; ordenar quantidade decrescente, desempate por nome PT-BR e ID.
Exibir posição, nome e unidades lançadas. Cancelamentos e ajustes não são
deduzidos. Não apresentar essas quantidades como vendas líquidas ou recebimentos.
Exibir colunas verticais proporcionais ao maior volume da lista, com nomes e
quantidades escritos. Em telas estreitas, o gráfico de itens rola na horizontal
dentro do painel. Exibir uma pizza com unidades por categoria, incluindo produtos
fora dos dez primeiros. Usar as categorias atuais do cardápio, ignorar o
agrupador Todos e mostrar itens sem categoria em Outros. Se a consulta do
cardápio falhar, sinalizar indisponibilidade apenas no gráfico de categorias.
Usar a mesma cor para a categoria na pizza e nas colunas, independentemente
da posição no ranking. Compactar os painéis mantendo nomes e valores visíveis.
Durante a reconexão do canal ao vivo, indicar a atualização periódica enquanto
houver leitura bem-sucedida.
Revalidar via SSE existente e polling de segurança a cada 15s enquanto aberto,
inclusive mudança de dia operacional. Exibir última atualização, loading,
vazio confirmado, erro/retry e conexão degradada. Erro limpa o ranking para não
atribuir dados anteriores à noite atual; revogação limpa dados protegidos.

## Fora de escopo e risco
R2: somente leitura e UI; sem API nova, alteração de permissões, cálculo
financeiro, migrations, escrita, ranking líquido, deploy ou merge.

## Plano e tarefas
- [x] Componente isolado de ranking e seletor com botões aria-pressed.
- [x] Reutilizar gateway e realtime existentes, sem persistir dados do ranking.
- [x] Testar agregação, atualização, virada, vazio e erro (empates/limite pendentes).
- [x] Validar typecheck, build, auth e visual focalizado em mobile/desktop e zoom200%.

## Aceite
1. Resumo padrão preservado; Mais vendidos abre sem trocar área global.
2. Mesmo produto agrega quantidades; lista limitada a dez e ordenação estável.
3. API determina noite, autorização e escopo. Nenhuma mutação ao consultar.
4. Atualização automática e virada de dia não retêm ranking de outra noite.
5. Erro/403/vazio/loading distintos; retry disponível; sem falso Ao vivo.
6. 360/390/430/1280px, teclado, alvos44px, zoom200%, sem overflow e axe.

## Evidência local

Base b6f9a87; branch codex/management-best-sellers; alterações ainda sem commit.
TypeScript --noEmit e next build passaram. Testes de sessão: 4/4.
Playwright: 8/8 (management-best-sellers.spec.ts e management-now-layout.spec.ts),
360/390/430/1280px, axe, zoom200%, teclado, atualização por polling, agregação,
virada do dia, vazio, 403/retry e ausência de mutações. Capturas ignoradas em
visual-artifacts/best-sellers; inspeção visual real da captura360px realizada.
Execução direta pelos entrypoints Node equivalentes aos scripts package.json,
pois npm não está instalado no PATH. A primeira tentativa visual falhou por
Chromium ausente; navegador instalado e repetição passou. Tentativa pnpm
reinstalou dependências e falhou por build script bloqueado; pacotes originais
movidos para .ignored foram restaurados e arquivos pnpm gerados removidos.
Não executados: suíte visual completa, integração Django/PostgreSQL, CI,
sign-off de operador/dispositivo e teste dedicado de dez produtos/empates.
Sem alteração de API/auth/tenant; autorização existente permanece canônica.
GO para teste local; não homologado para release. Próximo responsável: usuário.

### Refinamento visual após feedback

Mantidos ranking e leituras; alterados apenas componente, CSS e teste visual.
Reduzidos botões/avisos concorrentes; status textual compacto, vazio com ícone,
rodapé de atualização e disclosure de cálculo. Evidência visual inspecionada:
visual-artifacts/best-sellers/empty-refined-360.png. Build com TypeScript passou.
Teste estendido cobre disclosure e acessibilidade do vazio. Uma execução de
regressão foi invalidada por rebuild concorrente do diretório .next (6/8);
repetição serial registrada no handoff. Suíte completa/integração não executadas.
Base/branch e ausência de commit/deploy permanecem iguais ao registro anterior.

## Preparação do PR — 2026-11-03

Autorização do usuário: criar PR, documentar e fazer merge na main de todo o
trabalho desta conversa. Base remota conferida: main@b6f9a87049e99cf648759b092b3b5576bb5bb72b;
branch codex/management-best-sellers. PR adjacente aberto #314 altera Bar/PICKUP,
fora desta slice; nenhum contrato ou arquivo dessa frente foi incorporado.
Arquivos gerados de instalação Python e next-env não integram a feature.

Risco máximo R2: composição visual e consulta a projeções existentes, sem
alterar backend, permissões, dados persistidos, ledger, migrations ou CI.
Sem ADR: não há decisão arquitetural nova. Autorrevisão do diff; não constitui
review independente nem aprovação do GitHub.

Teste adicional cobre limite10, desempate por nome e agregação de snapshots;
o lint detectou leitura de ref na renderização do botão, substituída por estado
React para refletir revogação. Refs permanecem apenas na coordenação assíncrona.
Typecheck/build e ESLint dos três arquivos TS/TSX alterados: PASS.
Sessão/tenant/backend-fetch: 14/14 PASS; primeira tentativa falhou por Python
ausente no PATH, repetida com RODADA_TEST_PYTHON apontando ao venv local.
KB: PASS, 49 documentos e 307 links. Web added-line será conferido após commit.
Rodada ampliada visual: 23 PASS e 4 FAIL. As quatro falhas são
management-navigation.spec.ts:20 (espera5 destinos de Gestão; recebe6).
Inspeção de origin/main confirma seis destinos em management-settings.tsx e
expectativa5 no teste original; ambos fora do diff. Não se alega execução do
baseline separada. Sem mascarar a divergência ou atualizar teste alheio.
Reexecução focalizada após a correção do lint e checks do PR serão vinculados
ao SHA publicado. Equivalentes dos scripts npm executados pelos entrypoints
Node instalados, sem npm no PATH; gate ESLint incremental exige launcher POSIX
e não executa neste Windows, substituído localmente pelo lint dos arquivos
afetados e mantido intacto na CI.
Suíte visual completa, homologação de dispositivo/operador e release não são
declarados. Rollback: reverter o commit do PR; não há dados/schema a reverter.

### Handoff de implementação — 2026-11-03

Implementação: 9eed8785ed0e636c13af50011d31230052f63493; branch
codex/management-best-sellers; [PR #323](https://github.com/procopio420/rodada/pull/323).
Após a correção do lint: typecheck/build PASS e reexecução focalizada 9/9 PASS
(ranking, limite/desempate, resumo, quatro larguras, teclado, axe, zoom200%,
virada do dia, erro/retry, ausência de mutações). ESLint dos arquivos alterados
PASS; guard Web sobre o commit: 217 linhas adicionadas, zero achados (PYTHONUTF8=1).
As 4 falhas adicionais de Gestão descritas acima permanecem conhecidas.

Autorrevisão: nenhum P0/P1 identificado no diff; R2, sem aprovação independente
declarada. Escopo de escrita: page/CSS de Agora, novo componente e teste,
README Web e documentos da Spec007. Nenhuma ADR nova ou arquivo de API.
Evidência visual local: visual-artifacts/best-sellers/{360,390,430,1280}.png e
empty-refined-{360,390,430,1280}.png (fixtures sintéticas, não dados de bar).
Critérios1–6 cobertos pela suite focalizada; limite/desempate agora testados.
CI Web/Knowledge Base: pendente neste registro; resultado final no PR do SHA.
GO técnico local para a slice, merge condicionado aos checks reais do PR.
Próximo responsável: mantenedor/CI; não declarar release ou deploy deste registro.

### Correção de seletores legados para concluir os gates

CI do HEAD da908f5: [Web run41686134683](https://github.com/procopio420/rodada/actions/runs/41686134683)
falhou com 156 PASS, 9 FAIL, 3 SKIP na integração PostgreSQL; KB PASS.
Falhas: attendance-delivery-freshness.spec.ts:15 e attendance.spec.ts:62 buscam
“Registrar entrega por exceção”; peak-dispatch.spec.ts:53 busca “Voltar sem
concluir”. O componente attendance-delivery-page.tsx já presente na base usa
“Confirmar entrega” e “Voltar sem entregar”. Nenhum desses arquivos era alterado
pela feature; não foi executado baseline separado.

Para concluir o merge autorizado, alinhar apenas esses seletores aos nomes
acessíveis atuais. Manter asserts canônicos de task/item DONE/DELIVERED,
nenhum pagamento, valores e retorno à fila; não remover casos ou aumentar
timeouts. Corrigir também expectativa5→6 em management-navigation, acrescentando
assert explícito do link Políticas de consumo já existente. R2 de manutenção
de testes, sem alteração de produto, endpoints, auth ou workflow.
As falhas anteriores permanecem como evidência histórica; repetir gates e só
considerar GO de merge após resultado verde no novo SHA.
