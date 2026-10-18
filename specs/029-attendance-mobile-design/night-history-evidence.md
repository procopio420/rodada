# Histórico da noite Android — evidência local

2026-10-17, branch `codex/android-attendance-colors`, base `fb3ea55d`; alterações sem commit.

## Implementação

Spec029 define o diálogo e Spec001 mantém estados financeiros. API ordering/views aceita history_day=current/data sem alterar o payload da consulta comum; usa timezone/cutoff do Venue, closed_at para concluídas e evento auditável tab.cancelled para canceladas. Android fixa business date entre páginas. TablesScreen abre TabHistoryDialog pelo ícone existente; lista e detalhe são somente leitura, isolados de selectedTab/rascunho. Totais, pedidos, itens e pagamentos vêm do detalhe canônico. LatestHistoryRead descarta respostas antigas após troca, retry ou fechamento.

Arquivos: API ordering/views e test_night_tab_history; Android TablesScreen, TabHistoryDialog, AttendanceScreen, OperationsHttpClient/Repository/ViewModel, LatestHistoryRead e testes correspondentes. Nenhuma migration, alteração de ledger, biblioteca ou interface Web.

## Validações executadas

- PASS: três testes PostgreSQL descartável — tenant, autenticação, cutoff/local após meia-noite, limites inclusivo/exclusivo, cancelamento por auditoria, parâmetros inválidos, payload legado e paginação201.
- PASS: 100 testes JVM, incluindo geração de leitura contra respostas fora de ordem; assembleDebug, assembleDebugAndroidTest e lintDebug.
- PASS: dois Compose para consulta/lista/detalhe/retorno, ausência de ações financeiras, loading/erro/retry/vazio/busca.
- PASS: jornada Compose repetida em360/390/430dp e360dp fonte200%; capturas da lista e detalhe inspecionadas. AVD restaurado1080x2424/density420/font1.
- Revisão independente: corrigida corrida A/lista/A; nova revisão sem achados, com limites abaixo. Revisor não executou testes.
- Jornada local real somente leitura: ícone abre histórico, comanda concluída abre detalhe, retorno à lista. APK instalado; API recarregada. Capturas de fixture ignoradas em visual-artifacts/android-native-port/night-history/.

## Limites e próximo passo

Gerência Web fora deste slice, a implementar na próxima etapa autorizada. TalkBack, aparelho físico e homologação operacional não verificados. Paginação por offset não é snapshot imutável diante de encerramentos concorrentes; reabrir histórico recarrega dados. A data operacional depende da política configurada no Venue. Sem alteração de dados financeiros compartilhados, commit, push, merge ou deploy. Próximo responsável: solicitante para aceite visual local; isto não é GO de produção.
