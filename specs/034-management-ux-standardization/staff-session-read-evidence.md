# Manutenção global — consulta inicial da sessão

2026-10-21. Branch codex/management-ux-alerts, base HEAD860b25d93da486d2416c6ddaccfdccd9605f8953;working tree acumulado sem commit/push/merge/deploy. R3.

StaffAuthScreen compartilha leitor e callbacks de aplicação/falha/finalização. Inicial usa Promise callbacks/cleanup, sem repetir loadingtrue/errornull já iniciais. Consulta manual preserva reset e finally. Sucesso/401/403/outros erros/transporte preservados. Login/logout/invalidação/renovação e permissões sem alteração.

Build webpack/typecheck/lint focado/diff check PASS. Visual15PASS11,5s:3novos casos de leitura pendente→401/403/transporte,2DEVread,5sessionlogin e5setupread incluindoABA/recovery pendente. Auth4PASS. Tenant primeira execução3PASS7FAIL por alias Python sem runtime configurado; rerun com RODADA_TEST_PYTHON existente10PASS. Sem alteração do produto para acomodar ambiente.

Lint global FAIL324arquivos/3erros/0avisos (antes4), JSON visual-artifacts/spec034-global-lint-after-session-read.json. Restam guest-ordering2 e table-service-rollout.

Revisão independente local componente/teste:NO_FINDINGS_WITH_GAPS. Limites herdados: concorrência entre consultas manuais/invalidação e respostas tardias após logout fora da proteção inicial. Mocks e testes de gateway não comprovam integração real e isolamento completo de doisVenues. CI/suítevisualcomposta/homologação manual pendentes. Gate autenticado REVIEW_BLOCKED;NO-GOrelease/piloto.

Próximo responsável:3erros globais e composição pendente;preservar patches. Hashes docs/development/evidence/spec034-staff-session-read/SOURCE-SHA256SUMS.
