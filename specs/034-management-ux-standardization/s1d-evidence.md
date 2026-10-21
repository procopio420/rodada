# S1d — formulário de destino de impressão

2026-10-19, branch codex/management-ux-alerts, HEAD
860b25d93da486d2416c6ddaccfdccd9605f8953 com S1c/S1d locais sem commit.
Escopo R2: JSX do formulário e CSS Module, sem alterar handlers ou componentes
PrintAgents/PrintAgentRoutes/trabalhos. PRs268/269/270 continuam abertas/draft;
main remota e82d36c na consulta. CI não revalidada nesta etapa.

## Resultado por critério

AC04 e parte automatizada AC09/10/11/12: grupos Identificação, Conexão e papel,
Uso na operação, mantendo labels, campos condicionais, defaults e POST existente.
Conexão usa coluna mobile/duas desktop; escolhas operacionais usam grade2/4.
Nenhum estado desconhecido ou envio aceito foi convertido em papel confirmado.

Baseline do build anteriorS1c, mesmo destino NETWORK de teste/papel80/estaçãoKITCHEN,
healthUNKNOWN/bridgeOFFLINE, sem jobs/filas/pareamento. Chromium360/390/430/1280x932,
mesma fixture antes/depois. Quatro capturas baseline antes do código, quatro
depois e quatro zoom CSS200%, [com manifestSHA256](../../docs/development/evidence/spec034-print-destination/).
Capturas390/1280 inspecionadas. Não comprova ganho medido ou aceite de operador.

## Comandos e resultados

- pnpm run typecheck: PASS.
- pnpm run build --webpack: PASS.
- pnpm exec eslint tests/visual/management-print-destination.spec.ts: PASS.
- Lint página: FAIL em react-hooks/set-state-in-effect, linha24; mesma falha
  reproduzida por git show HEAD da página via eslint stdin, linha23. Não suprimida.
- pnpm run test:auth:4 PASS.
- pnpm run test:visual nos arquivos management-print-destination, printing,
  management-subpages e management-alert-settings:42 PASS,1,2min.
- Testes novos:6 PASS (quatro larguras/axe/alvos/overflow/zoom/teclado,
  condicionaisAGENT/BROWSER/NETWORK e POST simulado200/403 com payload/busy).
- Primeira execução:8 PASS/5 FAIL/29 NOT_RUN. Quatro falhas em seletor getByLabel
  exato de select (label contém opções), uma por alert duplicado do Next. Corrigidos
  para role combobox com nome exato e alert dentro de main; assertions preservadas.
  Nova execução completa42 PASS. Baseline é captura, não aceite automático antigo.
- KB e git diff --check: PASS. Nenhuma tolerância ou baseline existente alterado.

test:visual executado pelo pnpm disponível, mesmo script playwright do package.
Suíte ampla não repetida nesta slice: mantém resultado anterior S1c8PASS/5FAIL/
700NOT_RUN em Atendimento, sem contraprova de baseline. Gate global não está verde.

## Limitações e continuidade

Browser com API local abriu /manage/printing e mostrou os três grupos, sem salvar
destino ou alterar agentes/rotas/trabalhos. Escritas dos testes interceptadas no
browser, sem banco compartilhado. Prévia3001, API8000 e serviços existentes
preservados; somente a prévia desta worktree reiniciada após build.
Next dev pode alterar next-env.d.ts automaticamente para .next/dev/types.

Revisão de autoria R2, não independente. Pareamento, impressão física, integração
real de escrita, rede/recovery/revogação, leitor de tela, zoom nativo e aceite humano:
NOT_RUN. Não há GO de piloto/produção ou S1 completa. GO somente para inspeção local.
Rollback de apresentação reverte JSX/CSS, sem migration/dados. Próximo responsável:
autor para outra slice de Gestão e operador para aceite visual. Sem commit/push,
merge ou deploy. Alterações S1c anteriores preservadas.
