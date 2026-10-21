# S2c — Salão e indisponíveis

2026-10-20. Branch codex/management-ux-alerts; HEAD base 860b25d93da486d2416c6ddaccfdccd9605f8953. Alterações locais sem commit. Spec034/S2c e Spec007. Risco R2 de apresentação; revisão do autor, sem nova revisão independente.

## Mudança

Salão como região nomeada, mesmos contadores/filtros e quatro destinos. Grade de contadores/atalhos reutilizada de S2b, duas colunas desktop. Itens indisponíveis seguem a condição existente e details; lista semântica com nomes completos e quebra. Nenhuma mudança em API, cache, autorização, cálculo, eventos ou comandos. Preserve todo trabalho S1 e S2 anterior.

## Validação

- Baseline final: 4 PASS antes do código de produto. Duas tentativas anteriores interrompidas por fixture incorreta: estado long não marca indisponibilidade e filtro requer active=true. Corrigida somente fixture isolada, sem alterar contrato.
- pnpm exec next build --webpack PASS; pnpm run typecheck PASS; ESLint página/teste PASS.
- pnpm run test:visual management-hall-layout.spec.ts management-operation-layout.spec.ts management-now-layout.spec.ts management-navigation.spec.ts: 32 PASS, 53.7s. Quatro larguras 360/390/430/1280, 12 produtos de teste com nomes longos, vazio confirmado, teclado/foco/alvos/destinos, axe/overflow, CSSzoom2 local e nenhuma escrita. Regressões de erro/cache/paginação e navegação incluídas.
- Capturas390/1280 e360CSSzoom examinadas. 12 PNG e3fontes com manifests SHA256 em docs/development/evidence/spec034-hall. Hash da página após apenas remoção de linha vazia final apontada no diffcheck; sem mudança executável após build/testes. Diffcheck final PASS.

## Limites e retomada

Zoom nativo, leitor de tela, dispositivo, integração real e aceite humano NOT_RUN. Gate global não repetido: continua FAIL conforme composiçãoS1; gatesR3 anteriores REVIEW_BLOCKED. Não declarar Spec034 ou S2 aceitos globalmente. GO inspeção local, NO-GO merge/release/piloto. Sem commit/push/merge/deploy ou escrita operacional real. Próximo recorte: S3a entrada Financeiro, sem antecipar alterações de comandos financeiros; atualizar critérios antes de editar. Preview3001 reiniciado sessão24679; autenticação de staff necessária. Manifestos S2a/S2b anteriores são fotografias históricas e não representam fonte compostaS2c.
