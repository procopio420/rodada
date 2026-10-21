# S1e — leitura de destinos, 2026-10-19

Branch codex/management-ux-alerts, HEAD860b25d93da486d2416c6ddaccfdccd9605f8953.
S1c/S1d/S1e locais sem commit; alterações anteriores preservadas. R2 visual,
SELF_REVIEW. PRs268/269/270 abertas/draft e main remotae82d36c reconsultadas.

Lista de destinos agora usa articles nomeados/h3, ação Configurar com largura
própria e metadados separados. Mesmos valores, condicionais de bridge e hardware,
edit e novo destino. Comparação automatizada do trecho tipos/estado/handlers
antes do JSX contra HEAD: idêntico. Sem endpoint, migration ou regra nova.

## Evidência e validação

Baseline capturada antes do patch no buildS1d. Fixture fixa com NETWORK ativo de
nome longo e AGENT desativado, sem jobs/pareamento/filas, UNKNOWN sem health_at.
Quatro larguras360/390/430/1280x932, Chromium, mesma fixture antes/depois;
zoom CSS200% depois. [12 capturas e SHA256SUMS](../../docs/development/evidence/spec034-print-endpoints/).
Captura390 inspecionada: nome quebra, ação preservada, dados e estados legíveis.

- typecheck, build webpack e lint do teste novo: PASS.
- test:auth:4 PASS.
- test:visual management-print-endpoints, management-print-destination,
  management-subpages e printing:39 PASS,1,2min.
- Quatro testes novos: headings/articles/estados, AGENT sem bridge, seleção do
  destino correto, novo destino, ausência de escrita, axe/alvos44/overflow/zoom.
- KB e whitespace: PASS. Spec/aceite/plano/tarefas/design system atualizados.
- Lint de página não repetido: falha herdada já reproduzida naS1d; sem alteração
  do trecho types/handlers. Não declarar lint de página verde.
- Suíte ampla não repetida: resultadoS1c8PASS/5FAIL/700NOT_RUN em Atendimento
  permanece pendente; nenhuma contraprova nova nem gate global verde.

AC04 e parte automatizada AC09/10/11 cobertos. Aceite humano, leitor de tela,
zoom nativo, impressão física, integração real de escrita, rede/recovery e revisão
independente: NOT_RUN. Não fechar S1 ou toda a página de Impressoras.

## Estado local e continuidade

Prévia3001 reiniciada após build e página Impressoras atualizada no browser.
API/dispatcher/PostgreSQL preservados. Ambiente real sem destinos; não criar
cadastros para simular evidência. Escritas do teste são interceptadas no browser.
Sem commit/push/merge/deploy. GO somente para inspeção local; sem aceite global.
Rollback visual reverte JSX/CSS desta lista, sem dados. Próximo responsável: autor
para próxima slice e operador para aceite. Próximos candidatos: trabalhos de
impressão ou Setup; qualquer impacto em auth/dados/recovery exige reclassificação.
