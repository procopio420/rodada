# Manutenção global — leitura de pessoas

2026-10-21. Branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`. Alterações locais acumuladas; sem commit/push/merge/deploy.

## Escopo e implementação

Erro set-state-in-effect em PartySizeEditor resolvido separando leitor sem setters e callbacks estáveis. Consulta inicial usa callbacks de Promise e ignora resultado após cleanup. Consulta manual e conflito409 mantêm o mesmo leitor e estados. POST, payload/chave pendente, locks e markup não mudaram. Nenhum callsite TSX ativo encontrado; controle não foi reintroduzido no popup simplificado. Contrato adjacente: specs/016-covers-party-size/spec.md.

## Evidência

- ESLint do componente PASS; typecheck e build webpack PASS.
- Lint global FAIL:319arquivos,8erros,0avisos (antes9erros). JSON: visual-artifacts/spec034-global-lint-after-party-size.json. PartySizeEditor não aparece mais entre os erros.
- Revisão independente local: NO_FINDINGS_WITH_GAPS. Leitor e sucesso/erro preservados; sem alteração no comando/retry. Revisor não executou testes.
- Não há cobertura de montagem do componente pelas rotas atuais. Teste de ausência do controle/request no popup é regressão de exposição, não prova de execução do editor. Sem teste novo que espelhe a implementação.
- Corridas herdadas de consulta manual/pós409 e troca de occupancyId sem remontagem não foram resolvidas por este cleanup. Não ampliar a garantia para além da leitura inicial.
- Integração real, suíte visual composta completa e homologação manual pendentes. GateR3 autenticado REVIEW_BLOCKED. NO-GO release/piloto.

Próximo responsável: continuar triagem dos8erros globais (confirmed-item-removal,developer-staff,guest-ordering2,pricing-adjustments,production-board,staff-auth-screen,table-service-rollout), preservando patches e recuperação. Concluir composição de testes interrompida em etapa anterior. Hashes em docs/development/evidence/spec034-party-size-read/SOURCE-SHA256SUMS.

## Regressão de exposição

Teste visual focal attendance.spec.ts: duas falhas reproduzidas por caminho antigo (primeiro procura Mesa24 em Agora; depois espera dialog onde existe region). Ajustado somente o caso focal para navegar Mesas, selecionar region Mesa24 e confirmar ação Grupo saiu · Liberar mesa. Asserts de ausência de input/texto e requests=[] e layoutAndA11y preservados. Rerun1PASS4,1s. Uma tentativa intermediária foi interrompida após erro de caminho do script de edição; não representa resultado de teste. Sem alteração no produto para acomodar o teste.

Revisão independente adicional do teste: NO_FINDINGS_WITH_GAPS; confirma manutenção das negativas e acessibilidade, sem mock novo. Lint final de componente e teste PASS. Diff check PASS. Revisão autenticada continua REVIEW_BLOCKED.
