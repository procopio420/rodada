# Manutenção global — relógio de Bar/Cozinha

2026-10-21. Branch codex/management-ux-alerts, base HEAD860b25d93da486d2416c6ddaccfdccd9605f8953. Working tree acumulado, sem commit/push/merge/deploy. Recorte R2 de apresentação temporal; comandos/recovery/autorização não alterados.

O relógio é inicializado ao aplicar snapshot consultado/restaurado. Intervalo15s e cleanup permanecem. Removido setter síncrono do efeito. Antes da leitura ou primeiro tick, cabeçalho pode mostrar —. Idade usa timestamps canônicos existentes, não altera preparo nem inicia comando. Revisor autor conferiu diff; sem nova revisão independente desta slice.

Validação executada: build webpack/typecheck/lint focado/diff check PASS. Visual11PASS16,7s:2novos testes Bar/Cozinha confirmam5:00 no primeiro snapshot,5:15 após tick15s, timestamp inválido explícito e0POST.9regressões existentes confirmam lote/item independente nas larguras360/390/430, payload/recovery e barreiras sessão/malformed/tampered. APIs interceptadas; sem prova de integração real ou servidor. Não há novo teste focal de restauração do cache; callback apenas inicializa relógio ao aplicar dados existentes.

Lint global FAIL322arquivos/5erros/0avisos, antes6: visual-artifacts/spec034-global-lint-after-production-clock.json. Restam guest-ordering2,pricing-adjustments,staff-auth-screen,table-service-rollout. Auth/tenant não reexecutados nesta slice de relógio; passaram na etapa anterior de equipe. Integração real, visual composto completo, CI e homologação manual continuam pendentes; reviewR3 autenticado da composição REVIEW_BLOCKED,NO-GOrelease/piloto.

Próximo responsável: corrigir5erros globais e concluir composição interrompida, preservando patches. Hashes docs/development/evidence/spec034-production-clock/SOURCE-SHA256SUMS.
