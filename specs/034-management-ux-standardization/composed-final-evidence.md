# Validação composta da Gerência —2026-10-21

Branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`. Working tree acumulado com UX e manutenção anteriores; nenhum código de produto/teste foi alterado nesta rodada. Sem commit/push/merge/deploy; estado remoto não atualizado. Execução local em apps/web, API interceptada por fixtures, servidor de produçãoNext na porta3100 e referência estática3101 isolados.

## Resultado

**PASS296testes/0falhas/7,3min**, uma execução completa,1worker,sem retries. Seleção explícita dos47arquivos management*.spec.ts e3arquivos adjacentes:manual-refund-intent.spec.ts,correction-without-refund.spec.ts,refund-labels.spec.ts. Esta fotografia supersede a composição anterior294casos interrompida após39PASS; preservar esse histórico, sem reclassificá-lo como execução completa.

```powershell
$env:RODADA_REFERENCE_PYTHON='<runtime Python existente>'
$managementSpecs = @(Get-ChildItem tests/visual -Filter 'management*.spec.ts' | ForEach-Object { $_.Name })
$managementSpecs += @('manual-refund-intent.spec.ts','correction-without-refund.spec.ts','refund-labels.spec.ts')
pnpm run test:visual @managementSpecs
```

Não usar regex simples management, pois o nome do worktree amplia a seleção. Lista e hashes das50fontes de teste em docs/development/evidence/spec034-composed-final/SOURCE-SHA256SUMS. HTML temporário em apps/web/playwright-report/index.html; pode ser substituído pela próxima execução.

Cobertura:Agora/Operação/Financeiro/Cardápio/Gestão;alertas,fechamento,clientes,personalizações,preços,impressão,estornos,relatórios,configuração,equipe;360/390/430/1280quando previsto;fonte200%,teclado/foco/retorno,axe;loading/vazio/erro,permissões/403/conflitos409,respostas atrasadas,polling,storageindisponível,readback,reload,replaycomintenção/chavepreservada,revogação e recuperação financeira comAPIinterceptada.

## Outros gates e limites

Lint global325arquivos/0erros/0avisos,buildwebpack/typecheck/auth4/tenant10 passaram na rodada imediatamente anterior de bootstrapguest sobre as mesmas fontes de produto. Não reexecutados aqui por não haver alteração de código. Diff checkPASS nesta rodada. Os59testesguest passaram separadamente; não somar como se fizessem parte desta execução296. Suíte visual global do repositório NÃO executada nesta rodada; falhas históricas deAtendimento permanecem sem revalidação global.

Revisões locais anteriores preservadas com gaps por slice; esta rodada verifica composição e não cria aprovação independente nova. ReviewR3autenticado permanece REVIEW_BLOCKED. Integração realDjango/PostgreSQL/duasVenues/concorrência,CIremota e homologação manual comoperador/dispositivo/leitor de tela não foram comprovadas. **NO-GOrelease/piloto permanece**; PASS296 não autoriza merge/deploy.

Próximo responsável:conferência manual daGerência sobre runtimeWeb/API verificado e acompanhamento dosgates reais deintegração/CI/reviewautenticado. Não inventar nova etapaUX nem tratar testesfixtures comohomologação. Preservar working tree e dados; não executar seed/reset/migration ou publicação.
