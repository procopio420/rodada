# Manutenção — consulta inicial de Preços e serviço

2026-10-20. Branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`. Alterações locais acumuladas; sem commit, push, merge ou publicação. Escopo financeiro adjacente classificado R3 para revisão independente.

## Correção

GETs de política e aprovações separados em readPricing; aplicação dos resultados usa callback estável. Consulta inicial passa a ser assinada no efeito, com tratamento de rejeição de transporte e cleanup para ignorar conclusão após desmontagem. Sem timer artificial ou supressão de lint.

Mantidos os resultados parciais anteriores, URLs, cálculo em basis points/centavos, mensagens da API, perform, PIN/reauth, versões, botões e comandos. Load manual/pós-comando continua aguardando os mesmos resultados e propagando erro como antes. Falha de transporte inicial agora informa conexão e atualização, sem afirmar confirmação financeira.

## Validação executada

- Regressão network antes do código:1FAIL, sem status esperado na tela.
- ESLint da página e teste, build webpack e typecheck:PASS.
- Auth4 e tenant10:PASS.
- `test:visual management-pricing-read.spec.ts management-pricing-policy.spec.ts management-pricing-approvals.spec.ts`:10 PASS em21,1s.
- Cobertura de quatro larguras, axe/layout, política/preview de aprovação, comandos interceptados, falhas de rede/503. Política ausente mantém salvar bloqueado mesmo com PIN; consultas não enviam escrita nem geram pageerror.
- Duas capturas de erro e hashes de fontes/imagens em [evidências](../../docs/development/evidence/spec034-pricing-read/). Inspecionada captura de rede390, sem PIN no campo. Não houve alteração de layout.
- Inventário de lint dos módulos acompanhados:3erros restantes, refunds55 e house-account108/115. Pricing deixou de constar; contagem4→3.

## Revisão e limites

Review independente `/root/review_team_ux`:NO_FINDINGS_WITH_GAPS. Conferiu aplicação parcial, callbacks e comandos intactos; não executou os testes. GateR3 autenticado global permanece REVIEW_BLOCKED, sem recomendação de merge/deploy.

Limites herdados fora deste recorte: falha de aprovações com política válida permanece silenciosa; botão de refresh manual ainda propaga rejeição sem catch; consultas manuais concorrentes não têm ordenação nova. Não afirmar que toda falha de leitura ou concorrência foi resolvida. Testes interceptados não comprovam integração financeira real, ledger, concorrência PostgreSQL ou replay. Suíte global/manual não repetidos. NO-GO release/piloto permanece.

Próximo responsável: manutenção limitada de refunds e house-account, com revisão independente e testes de recovery/dados. Preservar os patches locais e a padronização visual já entregue.
