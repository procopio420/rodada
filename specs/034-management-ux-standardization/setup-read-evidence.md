# Manutenção — leitura inicial de Setup

2026-10-20. Branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`. Alterações locais acumuladas; sem commit, push, merge ou publicação. A área envolve freshness e equipe: revisão independente foi executada, sem aprovação autenticada de GitHub.

## Correção entregue

A consulta inicial de mesas, zonas e vínculos usa callbacks assíncronos com cleanup, sem setter imediato no efeito, supressão de lint ou timer artificial. Consulta de vínculos continua condicionada a `staff.manage`. `load()` manual e pós-comando mantém invalidação de freshness, `clearError` e semântica de `load(false)`.

Quando `canManage` muda, reconciliação condicional do estado invalida somente freshness e erro antes de confirmar a nova leitura. O formulário não remonta por capacidade: `uncertainCreate`, `sending`, `busy` e rascunhos permanecem. A key continua sendo a sessão original. Create/saveMember, reauth, PIN e versões não foram alterados.

## Revisão e contraprovas

O revisor encontrou dois riscos nos candidatos intermediários: comparar apenas o booleano da capacidade permitia reutilizar confirmação após ida/volta; remontar pela capacidade descartava recuperação de cadastro ambíguo e envio pendente. Ambos foram corrigidos antes da entrega.

A remontagem incorreta foi reproduzida com dois testes que falharam: resposta perdida e envio pendente seguidos de mudança de capacidade. A versão final preserva o campo e bloqueio, exige um único POST e só libera cadastro após conferência deliberada. O risco de ida/volta foi identificado por source e validado no cenário final com duas consultas503; não houve baseline executável desse primeiro candidato.

Review final `/root/review_team_ux`: NO_FINDINGS_WITH_GAPS, achados encerrados. O reviewer inspecionou código e testes; não executou os testes.

## Validação executada

- Lint antes: erro `set-state-in-effect` em Setup. Lint final da página e testes: PASS, sem supressão.
- Build webpack, typecheck, auth4 e tenant10: PASS no código final.
- Composição final:27 casos selecionados,26 PASS e1 FAIL. Falha adjacente de teste de mesas por ambiguidade entre alerta do produto e anunciador do Next. Seletor limitado ao main, sem mudar produto nem remover verificações negativas.
- Rerun de mesas:6 PASS em8,7s. Os27 casos distintos ficaram cobertos pelas duas execuções; não afirmar27 PASS numa mesma execução.
- Cobertura: recarga bloqueia escrita e preserva rascunho; falha de transporte/503; capacidade ida/volta sem snapshot reaproveitado; recuperação ambígua e pending preservados; equipe200/403/409, falha de reauth, ausência de permissão; layouts360/390/430/1280 e regressões de mesas.
- Inventário de lint dos módulos acompanhados:4 erros restantes — pricing15, refunds55 e house-account108/115. Setup, catálogo e impressão limpos. Contagem5→4.
- [Hashes do candidato final](../../docs/development/evidence/spec034-setup-read/SOURCE-SHA256SUMS). Sem alteração de layout nesta manutenção.

## Limites e continuidade

API interceptada e testes de auth/tenant não comprovam integração real de alterações de equipe, banco ou concorrência. Callbacks de load manual/pós-comando mantêm os limites herdados de respostas antigas; o cleanup novo protege a assinatura do efeito. A suíte global, dispositivos, leitor de tela e operação real não foram reexecutados. GateR3 autenticado permanece REVIEW_BLOCKED; NO-GO para release/piloto.

Próximo responsável: manutenção dos quatro erros restantes em pricing/refunds/house-account, com testes proporcionais e revisão independente das áreas financeiras, dados e recovery. Preservar todas as alterações locais e não reiniciar o redesign.
