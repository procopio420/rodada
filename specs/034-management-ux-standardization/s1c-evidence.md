# S1c — formulário de Alertas, 2026-10-19

Base860b25d93da486d2416c6ddaccfdccd9605f8953; branch
codex/management-ux-alerts, alterações locais sem commit. R2, SELF_REVIEW.
PRs268/269/270 abertas/draft; main remota e82d36c na consulta desta sessão.

## Mudança e evidência

Fieldsets Produção/Pagamento/Atendimento/Confirmar alteração; CSS Module local,
tokens existentes, uma coluna mobile e duas desktop. Nenhum handler foi alterado:
mesmos campos/limites, segundos, endpoints, PIN, versão, erros e conflito409.
AC04 e parte automatizada de AC09/10/11/12 cobertos; aceite global pendente.

Baseline do build S1b antes do patch: quatro capturas via teste existente em modo
baseline. Mesma fixture versão1 com valores300/600/300/120/300, papel gerencial,
360/390/430/1280x932, Chromium. Antes/depois e zoom CSS200% preservados em
[evidências](../../docs/development/evidence/spec034-alerts/), com SHA256SUMS.
Pixels390/1280 inspecionados: grupos legíveis, confirmação separada, sem novos
tokens ou decoração. Não há medição de ganho operacional.

## Execução

- Baseline:4 capturas, PASS de execução; não é aceite do produto anterior.
- typecheck e build webpack: PASS; lint página/teste novo: PASS.
- test:auth:4 PASS.
- test:visual navegação/subpáginas/formulário:42 PASS.
- test:visual formulário + regressões originais de alertas:15 PASS (sete repetidos
  da execução anterior; total50 casos distintos entre as duas execuções).
- Cobertura nova: quatro larguras, axe, alvos44, overflow, teclado, zoom CSS200%,
  ausência de escrita ao navegar; confirmação simulada200/409/403, payload e busy.
- Suíte ampla com max-failures5:8 PASS/5 FAIL/700 NOT_RUN e erro de interrupção.
  Quatro falhas buscam região legada Outras comandas; uma mede alvo28px Detalhes
  em Atendimento. São as mesmas assinaturas relatadas em S1a, mas sem contraprova
  de baseline nesta sessão. Não atribuir causalidade nem declarar gate global verde.
- KB49 documentos/298 links/12 skills e git diff --check: PASS.

Teste original management-alerts.spec.ts preservado; teste novo em arquivo próprio.
Todas as escritas dos testes interceptadas no browser, sem usar DB compartilhado.
Integração real de escrita, timeout/revogação/polling durante edição, leitor de tela,
zoom nativo, dispositivo físico, revisão independente e aceite humano: NOT_RUN.

## Operação local e limites

Prévia webpack3001 retomada. Cluster PostgreSQL existente55460 retomado pelo
runbook; banco local existente confirmado, sem seed/reset/migration. API8000 e
dispatcher retomados no checkout principal existente, sem alterar código dele.
Readiness API e HTTP da prévia200. Não equivale a integração do patch com produção.
Percurso real Gestão→Alertas executado no browser com API local: grupos e campos
carregados, status Ao vivo; retorno à Gestão acionado sem salvar formulário.
Next dev atualizou automaticamente next-env.d.ts para .next/dev/types; arquivo
gerado fica separado do patch visual e não exige alteração de configuração.
Sem commit/push/merge/deploy. Rollback visual: reverter JSX/CSS local, sem mudança
de dados. Próximo responsável: autor para próxima slice, operador para aceite.
GO somente para inspeção local; gate global e homologação não aprovados.
