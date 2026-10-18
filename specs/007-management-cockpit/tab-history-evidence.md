# Histórico de comandas na Gerência — evidência local

2026-10-17, branch codex/android-attendance-colors, base fb3ea55d; patch local sem commit. Classificação R2: consulta operacional, sem alteração de API, BFF, autorização ou ledger.

## Escopo

Novo components/management-tab-history.tsx e entrada no cabeçalho app/manage/page.tsx. Ícone history com alvo touch-min, ActionDialog, campos, BillSummary, dataRow e dialogReturn existentes. globals.css adiciona somente largura compacta do ícone usando tokens; docs/design/system.md registra o padrão. Spec007 contém o contrato.

Dia operacional padrão vem da API existente; data e busca são explícitas, paginação200 fixa a data respondida. Detalhes incluem pedidos, valores, pagamentos e responsabilidade transferida assinada. Nada é persistido no browser. Aborto e geração impedem respostas antigas; desmontagem/trava de revogação limpam o popup mesmo se uma leitura antiga do pai terminar depois.

## Validação executada

- PASS: typecheck e build Next.js.
- PASS: ESLint focado nos três arquivos TypeScript deste slice.
- PASS: nove testes da suite visual Playwright: lista/detalhe/voltar/foco em360/390/430/1280px e360px com fonte200%; data/busca/paginação/erro/retry/vazio; fechar/reabrir com leitura pendente; transferência; revogação de sessão.
- Axe e alvos mínimos44px sem violações nos cenários visuais. Corrigido uso inicial de aria-label em div genérica, substituído por nav semântico; repetição9PASS.
- Revisão independente encontrou revogação incompleta e transferência ausente; ambas corrigidas e reavaliadas sem achados. Revisor não executou os testes.
- Jornada local real via navegador/BFF/API, somente GET: Gerência -> ícone -> dia operacional atual -> comanda concluída -> detalhe com itens/pagamento confirmado/saldozero. Aba mantida aberta. Nenhuma transação alterada.

Scripts package.json de typecheck/build/test:visual executados pelos binários Node locais equivalentes; npm não disponível no PATH. Logs ignorados em visual-artifacts/management-history-*.log; previews com fixtures sem dados pessoais em visual-artifacts/management-history/.

## Limites

Não executados: suite visual completa, lint global, suite completa de integração/CI, leitor de tela manual e aceite em aparelho físico. Capturas de testes são fixtures; consulta local real não certifica produção. Paginação offset não constitui snapshot imutável sob encerramentos concorrentes. Sem commit/push/merge/deploy. Trabalho anterior preservado; próximo responsável: solicitante para aceite local. Não é GO de produção.

## Extrato de conta paga — atualização de 2026-10-17

HistoryStatement local ao histórico substitui BillSummary compartilhado somente nessa tela. Total da conta e Paga/Pagamento confirmado passam a dominar; saldozero e parcelas sem efeito são omitidos. Nenhuma alteração de API, ledger ou pagamento. Pagamento líquido confirmado, estadoCLOSED, exposiçãozero, totalpositivo e avaliação de serviço válida condicionam o selo; simulação identificada. Aviso de taxa desatualizada preservado após revisão independente.

Validação: typecheck/build/lint focado PASS; visual15PASS com axe, cinco cenários de tela/fonte e negativos de selo. Primeira repetição falhou somente por seletor textual exato do teste (a frase compartilha parágrafo com Paga); ajustado seletor sem enfraquecer a asserção e repetidos15PASS. Revisão independente sem achados restantes. Consulta local real confirmou total canônico e selo pago da mesma comanda mostrada pelo solicitante; nenhum pagamento ou ledger alterado. Aba deixada no extrato. Preview com fixture: visual-artifacts/management-history/statement-390.png. Escopos/limites anteriores continuam válidos; Android não alterado neste ajuste.
