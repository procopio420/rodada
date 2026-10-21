# Manutenção global — leitura de Administrar equipe

2026-10-21. Branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`, working tree acumulado sem commit/push/merge/deploy. Contrato adjacente: specs/025-pilot-cohesion-dev-tools/spec.md. R3, leitura de recurso de administração de acesso; nenhum comando ou contrato de autorização alterado.

## Implementação

readStaffMembers centraliza GET/validação sem setters; callbacks estáveis aplicam sucesso/falha. Efeito inicial consulta somente com staff.manage e ignora resultado após cleanup. Render reconciliation de resourceAccess invalida freshness em cada troca de allowed, sem remontar ou perder intent/PIN/uncertain. Load manual/pós-comando continua invalidando freshness antes de consultar. POST/PATCH, reauth, payload/chave, locks e markup intactos. Não houve API/DB/configuração nova.

## Evidências executadas

- Build webpack e typecheck PASS; lint de componente/teste PASS; diff check PASS.
- Visual focal: primeiro run5PASS1FAIL porque o mock503 não incluía code, provocando mensagem genérica de asApiError. Mock corrigido para contrato code/message; rerun6PASS7,9s.
- Casos: falha inicial bloqueia criar até consulta manual canônica; sem staff.manage não consulta lista nem mostra comandos; criação com resposta perdida preserva payload/chave, reautentica e bloqueia edição; controles existentes/remover com PIN ausente e acessibilidade em360/390/430.
- Lint global FAIL:320arquivos/7erros/0avisos, antes8. JSON visual-artifacts/spec034-global-lint-after-developer-staff.json. Fonte corrigida não aparece mais entre erros.
- Revisão independente local: NO_FINDINGS_WITH_GAPS. Gate autenticado permanece REVIEW_BLOCKED. Sem recomendação de merge/deploy.

Limites: testes de UI interceptam API e não provam autorização servidora, isolamento real entre Venues ou habilitaçãoDEV em ambiente externo. Corridas de load manual/pós-comando e transição de capacidade durante mutação são herdadas; retry apósABA não tem nova evidência. Suíte visual composta e homologação manual/integração real pendentes. NO-GOrelease/piloto.

Próximo responsável: triagem dos7erros globais restantes e composição pendente, preservando todos os patches. Não reabrir redesign. Hashes em docs/development/evidence/spec034-developer-staff-read/SOURCE-SHA256SUMS.

Validação complementar: auth4PASS e tenant10PASS. Revisão independente final incluiu o novo teste, confirmou negativas sem relaxamento e ausência de novos achados. Não substitui revisão autenticada ou integração real.
