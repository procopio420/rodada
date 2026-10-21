# Manutenção global — leitura do rollout das mesas

2026-10-21. Branch codex/management-ux-alerts, base HEAD860b25d93da486d2416c6ddaccfdccd9605f8953;working tree acumulado sem commit/push/merge/deploy. R3.

TableServiceRollout captura recuperação local sem setters e aplica resultado em callback da consulta canônica (sucesso ou falha). Cleanup ignora leitura inicial desativada. Policy inicialnull mantém botão bloqueado. ReadPolicy compartilhado com refresh manual;POST/payload/chave/localStorage antes do envio/readback de conflitos intactos. Scope/canConfigure não mudaram.

Build webpack/typecheck/lint focado/diff check PASS. Visual15PASS15,2s:3novos casos (persistência antesPOST, resposta perdida→reload→retryrawidêntico/chave/expected_version original apesarGETversion2 e storage limpo após confirmação;storage corrompido bloqueia;GET503 bloqueia).12regressões setupread/layout cobrem360/390/430/1280,vazio/loading/erro,capacidadeABA e recuperação pendente. APIs interceptadas, sem alterar ambiente real.

Lint global FAIL325arquivos/2erros/0avisos (antes3), JSON visual-artifacts/spec034-global-lint-after-rollout-read.json. Restam2erros em guest-ordering.tsx.

Revisão independente local:NO_FINDINGS_WITH_GAPS na montagem inicial. Limites:GETindefinidamente pendente adia aviso de recuperação;erroGETpode substituir mensagem de storage ilegível mantendo bloqueio. Troca de scope na mesma instância não coberta;policy anterior não invalidada imediatamente. Callsite atual Setup usa key=session.session.id,scope incluiVenue/staff/session;isso não prova todas transições possíveis. Concorrência e autorização real entreVenues não demonstradas. Auth/tenant não reexecutados nesta slice;passaram na etapa anterior. Integração,visualcomposto,CI,manual e reviewautenticado pendentes;REVIEW_BLOCKED/NO-GOrelease-piloto.

Próximo responsável:2errosguest-ordering e composição pendente;preservarpatches. Hashes docs/development/evidence/spec034-table-service-rollout-read/SOURCE-SHA256SUMS.
