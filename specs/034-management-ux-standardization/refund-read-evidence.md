# Manutenção — consulta inicial de Estornos

2026-10-20. Branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`. Alterações locais acumuladas, sem commit/push/merge/publicação. Escopo R3 adjacente a estornos e recuperação; revisão independente executada.

## Correção

Separados GETs de comandas/caixas em readRefundResources e aplicação dos resultados em callback estável. O efeito inicial assina a consulta com callbacks e cleanup; loading começa true, termina após a resposta e não recebe updates após desmontagem. Removida chamada com setter imediato no efeito, sem supressão de lint ou timer artificial.

Load pós-intenção preserva setLoading(true), tratamento parcial, mensagem de erro e finally. Filtro de caixas com turno e atualização funcional que conserva escolha válida são idênticos aos anteriores. SelectTab, payloads, centavos, reauth/PIN, useManualRefundIntent, journal, locks e pending não mudaram. Sem alteração de layout.

## Validação executada

- Lint baseline:FAIL set-state-in-effect linha55. Lint final da página e teste:PASS.
- Build webpack, typecheck, auth4 e tenant10:PASS.
- Oito suites focadas de Estornos/correções/intenção manual:39 PASS em58,9s.
- Novos quatro casos:consulta atrasada conserva loading até resolução; transporte e503 mantêm erro e não expõem formulário de estorno sem comanda; caixa sem turno não é oferecido e caixa aberto é selecionado.
- Regressões de quatro larguras, valores/labels, resposta perdida, reload/double tap, mesmo payload/chave, falha de readback, reauth/conflito, sessão alterada/revogada e storage indisponível/corrompido/vazio passaram. Tudo com APIs interceptadas, sem estorno ou alteração real de dados.
- Inventário de lint dos módulos acompanhados:2 erros restantes em house-account108/115. Estornos deixou de constar; contagem3→2.
- [Hashes do candidato](../../docs/development/evidence/spec034-refund-read/SOURCE-SHA256SUMS). Testes visuais regeneraram suas capturas; não houve nova composição estética.

## Revisão e limites

Review independente `/root/review_team_ux`:NO_FINDINGS_WITH_GAPS. Conferiu GETs, aplicação parcial, preservação de caixa válido, loading e intenção/locks intactos. Reviewer não executou os testes; os resultados são do autor.

Lacunas específicas: falha exclusiva do GET de caixas, parcial inversa, escolha após refresh e corrida entre consulta inicial/readback não ganharam testes próprios. Callbacks manuais concorrentes mantêm limites herdados; não afirmar resolução de toda corrida. Não foram executados testes de integração real com Django/PostgreSQL/ledger, concorrência financeira, operador ou suíte global completa. GateR3 autenticado permanece REVIEW_BLOCKED e NO-GO para release/piloto.

Próximo responsável: manutenção de house-account, preservando contexto de ator, intenção de override, consultas, autorização e recuperação. Fazer revisão independente e testes de dados/auth antes de recomendar integração. Não reiniciar o redesign nem apagar patches locais.
