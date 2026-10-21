# Manutenção global — leitura de ajustes da conta

2026-10-21. Branch codex/management-ux-alerts, base HEAD860b25d93da486d2416c6ddaccfdccd9605f8953. Working tree acumulado sem commit/push/merge/deploy. R3; preservação dos ajustes comerciais e recuperação existente.

readPricing separaGET do aplicador de estado. Efeito inicial usa callbacks de Promise/cleanup; callback verifica atividade antes de aplicar pricing e após auth/me antes de restaurar storage. Load manual continua reutilizando aplicador. Transport error inicial passa a mensagem explícita com preview bloqueado. Fórmulas em centavos/basispoints, POST, PIN, storagekey, preview e commit intactos.

Executados: build webpack PASS; typecheck inicialmente FAIL por inferência de predicate()=>true, anotado()=>boolean, build e typecheck final PASS. Lint focado de componente/teste PASS. Visual9PASS11,7s (8existentes pricing e1recuperação); após adicionar erro de transporte,2novos testesPASS3,9s. Não declarar10 em uma só execução. Recuperação seeded por Venue/staff/Tab conserva comando/chave e rawpayload no retry após abort e limpa storage após confirmação. Casos existentes: leitura lenta bloqueia preview, valores/preview acessíveis360/390/768 e política/aprovação.

Lint global FAIL323arquivos/4erros/0avisos (antes5), JSON visual-artifacts/spec034-global-lint-after-pricing-read.json. Restam guest-ordering2,staff-auth-screen,table-service-rollout.

Revisão independente local do componente NO_FINDINGS_WITH_GAPS. Limites herdados: recoveryKey não reinicializa sozinho se tabId mudar sem remount (callsite atual usa keyselected.id), consultas manuais concorrentes não têm proteção do efeito. Mocks não provam ledger/deduplicação/isolamento real de Venue. Auth/tenant não reexecutados nesta slice; integração real, visual composto, CI e homologação manual pendentes. Gate autenticado REVIEW_BLOCKED;NO-GOrelease/piloto.

Próximo responsável:4erros globais e composição pendente;preservar patches. Hashes docs/development/evidence/spec034-pricing-adjustment-read/SOURCE-SHA256SUMS.
