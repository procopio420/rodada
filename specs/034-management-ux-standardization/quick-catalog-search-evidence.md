# Manutenção global — busca do Catálogo rápido

2026-10-20, branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`. Working tree acumulado, sem commit/push/merge/deploy. Recorte R2 em componente compartilhado da Gerência/Bar/Cozinha.

## Correção

Erro herdado de set-state-in-effect confirmado em quick-catalog.tsx:33. Os três resets de busca passaram para os eventos que a iniciam: abrir painel fechado, alterar nome e voltar da criação. O acionador não reinicia estado quando o painel já está aberto. Efeito mantém debounce180ms, AbortController, tratamento de resposta e cleanup. Não houve alteração de permissão, estação, cálculo de preço, POST resolve-or-create, seleção ou polling de ícone; nenhum timer artificial ou supressão de lint.

## Validação executada

- ESLint de componente/teste PASS, build webpack e typecheck PASS.
- Composição17casos:16PASS1FAIL por assert do teste que incluía opções nativas de estação, além das opções de produto. Seletor corrigido para a listbox Produtos existentes. Rerun2novos testes PASS4,5s. Assim,15regressões existentes e2casos novos passaram entre as execuções; não declarar17PASS numa mesma execução.
- Cobertura existente: criação em estação autorizada com preço1250centavos, editor/categorias, permissões, polling, falha de upload e fluxo acessível do Bar em360/390/430. Novos casos: clique no acionador já aberto, voltar/reabrir com nova busca e bloqueio de criação enquanto resposta atual está pendente. APIs interceptadas, sem produto real criado.
- Lint global reexecutado:FAIL com9erros (antes10), arquivo visual-artifacts/spec034-global-lint-after-quick-catalog.json. Catálogo rápido não consta mais. Os sete erros do conjunto gerencial anteriormente corrigido continuam encerrados; esta é a primeira correção dos erros globais adicionais.
- [Hashes de fontes/teste](../../docs/development/evidence/spec034-quick-catalog-search/SOURCE-SHA256SUMS). Sem mudança de layout; testes visuais existentes regeneraram capturas.

Revisão do autor R2; não houve nova revisão independente deste recorte. Integração real, operador, suíte global visual e reviewR3 autenticado da composição continuam pendentes. NO-GO release/piloto permanece.

Próximo responsável: triar/corrigir os9erros globais restantes com regressão e revisão conforme risco. A composição294casos interrompida anteriormente ainda precisa de execução completa. Não reabrir o redesign nem descartar patches locais.
