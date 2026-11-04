# Retomada do PR #324 em outro computador

## Atualização publicada — etapa 3, cartão externo

O [PR #325](https://github.com/procopio420/rodada/pull/325), branch
`codex/pilot-stage3-external-card`, contém a slice cartão externo e a correção
do gate visual; continua empilhado no PR #324. Código validado `82a9f8d2`:
945 casos visuais e 26 testes Web/PostgreSQL aprovados. Ver
[relatório](pilot-stage3-external-terminal-2026-11-03.md) e
[manifesto](evidence/pilot-stage3-external-terminal/visual-repair-summary.json).
Retomar pelo #325 para a etapa 3; o #324 preserva o checkpoint de etapas 1–2.
A revisão R3 autenticada e a CI do candidato publicado ainda precisam ser
confirmadas. Sem homologação física, merge ou deploy; NO-GO produção.
As instruções abaixo preservam a fotografia anterior.

Atualizado em 03/11/2026. Repositório: `procopio420/rodada`.
PR: https://github.com/procopio420/rodada/pull/324.
Branch remota de continuação: **`codex/pilot-execution-plan`** (branch do PR).
O checkpoint publicado sucede a base documental
`1b6b20c74925f20d29e91f52dd9f96dc80669c89`; o SHA publicado aparece no PR.
Checkout de execução original: `codex/pilot-stage-1-scope`. Não procurar essa
branch local no outro computador; buscar a branch remota do PR.

## O que foi concluído

- **Etapa 1:** escopo aprovado explicitamente pelo usuário em 03/11/2026:
  Web com Atendimento, Bar, Cozinha, Gerência, Caixa e QR guest atual;
  dinheiro e cartão externo. Android nativo, impressora, PSP/Pix integrado,
  Pix manual, QR híbrido/FG84 e retirada rápida adiados.
- **Etapa 2:** ensaio local em PostgreSQL descartável e relatório/backlog
  entregues, incluindo os três complementos solicitados: turno por UI (CASH),
  90 s sem rede de navegador após commit de pedido/CASH e corrida de disponibilidade
  entre dois operadores na UI de BAR/KITCHEN.
- Produto examinado/testado:
  `main@67972d09200d43357b5b88dc0f64218967e4c24b`, reconsultado antes do checkpoint.
  Nenhuma alteração de código funcional, UI, permissões, ledger ou migrations.
- Testes adicionados, documentação e recibos/capturas sanitizados estão neste PR.
  A autorização para atualizar o PR foi dada explicitamente neste chat.

## Resultado e bloqueio que motivam a continuação

**NO-GO para produção.** Cartão externo pela interface não foi validado:
a opção Cartão está desabilitada no recebimento do Atendimento observado.
Registrar CARD por API no primeiro ensaio não prova capacidade de registrar
pela UI. O turno inteiro pela interface foi validado apenas com CASH.
Não assumir outro caminho de cartão disponível ou inexistente sem inventariá-lo.

**Próxima etapa é a 3 — resolver os gaps priorizados.** Recomendação apresentada
ao usuário: começar pelo recebimento de cartão externo pela interface, pois
integra o escopo aprovado. A prioridade foi recomendada, **não há implementação
da etapa 3 iniciada nem autorização inferida para merge/deploy**. O pedido atual
é salvar/publicar o checkpoint e indicar a retomada.

Ao receber pedido para executar a etapa 3:

1. Buscar PR/branch, conferir HEAD, main atual, arquivos concorrentes e AGENTS.
2. Ler este handoff, [escopo aprovado](pilot-stage-1-scope-2026-11-03.md) e
   [relatório da etapa 2](pilot-stage-2-rehearsal-2026-11-03.md), inclusive limites.
3. Confirmar a prioridade solicitada; se for cartão externo, inventariar telas,
   contratos e implementação antes de escolher a slice. Não integrar PSP nem
   presumir liquidação; registrar somente após confirmação externa.
4. Atualizar spec/acceptance/plan/tasks antes de alteração relevante. Ponto de
   partida: [Spec033 E04](../../specs/033-attendance-ux2-productization/epics/E04-settlement-and-table-turnover/spec.md),
   [Spec033/aceite](../../specs/033-attendance-ux2-productization/acceptance.md),
   contratos de Payments/ledger e Spec026 encontrados pelo índice da KB.
5. Ativar skills Web + POS safety; API quando pertinente. Dinheiro/auth/recovery
   exige revisão independente R3 no candidato. Não substituir por self-review.
6. Testar em PostgreSQL descartável, com autorização, centavos, auditoria,
   parcial/integral, idempotência, perda de resposta e isolamento. Mudança de UI
   exige `test:visual`. Não alterar os testes para acomodar resultado incorreto.

## Evidências disponíveis

- [Plano e acompanhamento](pilot-execution-plan-2026-11-03.md).
- [Etapa 1 e decisões aprovadas](pilot-stage-1-scope-2026-11-03.md).
- [Relatório completo, testes, cenários e impedimentos](pilot-stage-2-rehearsal-2026-11-03.md).
- [Manifesto do ensaio inicial](evidence/pilot-stage2-2026-11-03/manifest.json),
  [turno UI](evidence/pilot-stage2-2026-11-03/ui-manifest.json),
  [rede](evidence/pilot-stage2-2026-11-03/network-manifest.json),
  [disponibilidade](evidence/pilot-stage2-2026-11-03/availability-manifest.json).

Resultados locais em execuções separadas, não uma nova CI completa: 40 casos Web
existentes + seis casos novos = **46 casos Web distintos PASS**; **38 casos API
distintos PASS** (smoke de turno repetido para capturar evidência); 14 testes
Node auth/tenant, seis de coordenação do banco e cinco do verificador KB PASS.
TypeScript/build e ESLint dos novos testes PASS. Gate KB/links/diff revalidados
na publicação. Não houve CI remota aprovada deste checkpoint no momento da autoria.
CI deve ser conferida no novo SHA do PR após o push.

## Ambiente e o que não viaja com o Git

Execução original: Windows, Python 3.12.14, Node 24.22.1, Next 16.3.8,
Django 5.2.19, PostgreSQL 17.11 em loopback 55432 e Chromium Playwright.
Cluster foi encerrado ao final; não há serviço de banco deixado ativo.
`.local/`, dependências, bancos, relatórios HTML e traces brutos **não são
versionados**. Os manifests preservam a fotografia da execução antes do commit;
menções a alterações sem commit nesses documentos são históricas e não significam
que as evidências publicadas estejam faltando.

Para conferir os arquivos publicados em outro SO, usar o
[manifesto de publicação](evidence/pilot-stage2-2026-11-03/publication-manifest.json),
calculado sobre blobs do Git (texto normalizado). Hashes dos manifests de execução
descrevem bytes locais originais e podem diferir num checkout que converta LF/CRLF.

No outro computador, preparar dependências próprias conforme
[workflow Web](../../.github/workflows/web.yml), `npm ci`, Python com
`apps/api[dev]`, Chromium e PostgreSQL local/descartável. Usar `RODADA_TEST_PYTHON`
explícito, `RODADA_E2E_POSTGRES=1`, banco `rodada_web_e2e` e credenciais próprias
de teste. Nunca reutilizar demo/produção. Reinício da suite exige banco de teste
limpo; startup sem reset pode colidir com a fixture já existente. Os guards dos
scripts de integração restringem resets ao banco local descartável.

## Pendências de etapas posteriores

Etapas 3–6 ainda não executadas. Além do cartão UI: revisão R3 independente,
backup/restore/rollback técnico, retenção periódica comprovada, responsáveis
fiscal/equipe/rede, dispositivos físicos e walkthrough humano. Rede foi emulada
no navegador, sem certificar Wi-Fi físico ou outage de backend. Nenhum AC global
Android/Spec033 ou issue315–319 foi encerrado. Sem merge, deploy, DNS, banco remoto,
permissões, flags/secrets ou operação real autorizados por este checkpoint.

## Pedido sugerido no próximo chat

“Retome o PR #324 na branch codex/pilot-execution-plan. Leia
docs/releases/pilot-handoff-2026-11-03.md e execute a etapa 3 começando pelo
registro de cartão externo pela interface. Preserve o escopo aprovado e prepare
spec/aceite antes da implementação. Sem merge ou deploy.”

Esse texto é uma sugestão para o usuário enviar depois; não inicia a etapa 3
por estar registrado neste arquivo.
