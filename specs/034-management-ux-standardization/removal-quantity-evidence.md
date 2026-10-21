# Manutenção global — quantidade da remoção

2026-10-21. Branch codex/management-ux-alerts, base HEAD860b25d93da486d2416c6ddaccfdccd9605f8953. Working tree acumulado; sem commit/push/merge/deploy. R3; contrato adjacente specs/025-pilot-cohesion-dev-tools/spec.md e correções Spec017.

## Alteração

ConfirmedItemRemoval reconcilia o próprio estado em render somente quando editável e a quantidade diverge do clamp1..item.quantity. Guarda !busy&&!uncertain&&!applied preservada. Elimina set-state-in-effect sem alterar POST, intenção/chave, refresh, modal ou markup. Não há novo cálculo financeiro, API ou migração.

## Validação

- ESLint de componente/teste, typecheck, build webpack e diff check PASS.
- Visual6casos: primeira execução5PASS1FAIL por status ambíguo (output também tem role status enquanto refresh atualiza item). Seletor restringido à mensagem; rerun6PASS11,8s.
-360/390/430: resposta perdida mantém payload bruto idêntico no retry, quantidade3, campos bloqueados e Escape não fecha. Rejeição409 e refresh com quantidade1 limitam escolha a1 antes de nova tentativa com chave diferente. Sucesso fecha modal. layoutAndA11y executado nos6casos.
- Lint global FAIL:321arquivos/6erros/0avisos, antes7. JSON visual-artifacts/spec034-global-lint-after-removal-quantity.json.
- Revisão independente local do componente: NO_FINDINGS_WITH_GAPS. Quantidade válida converge; guarda e comandos preservados. Gate autenticado REVIEW_BLOCKED.

Limites: APIs interceptadas, sem prova de ledger, concorrência ou autorização entre Venues. Item.quantity pressupõe contrato numérico válido. Não executados nesta slice: auth/tenant novamente (passaram na etapa anterior), integração real e suíte visual global. Composição interrompida e homologação manual pendentes. NO-GOrelease/piloto.

Próximo responsável: corrigir6erros globais (guest-ordering2,pricing-adjustments,production-board,staff-auth-screen,table-service-rollout) e concluir composição pendente. Preservar trabalho anterior. Hashes em docs/development/evidence/spec034-removal-quantity/SOURCE-SHA256SUMS.

Revisão independente final do novo teste: NO_FINDINGS_WITH_GAPS; filtro mantém assert de clamp e replay bruto. Resultado final do autor:6PASS11,8s. Revisão autenticada pendente.
