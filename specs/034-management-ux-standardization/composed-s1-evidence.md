# Composição automatizada de Gestão/S1 — 2026-10-20

Branch codex/management-ux-alerts, HEAD860b25d93da486d2416c6ddaccfdccd9605f8953,
com alterações S1c–S1j locais sem commit. PRs268/269/270 continuam abertas/draft,
headsda644241/965dedea/860b25d9; main remotae82d36c reconsultada. As PRs existentes
não contêm as alterações locais. CI do conjunto atual não comprovada.

Esta etapa executou validações sobre a composição, sem novo código de produto.
Spec/plano foram corrigidos para distinguir planejamento histórico, PRs draft e
implementação local. Tarefas S1.1/S1.2 refletem implementação e evidência automatizada,
não aceite humano. S1 e S5 globais permanecem abertos.

## Gates executados

| Gate | Resultado desta rodada | Limite |
| --- | --- | --- |
| Build webpack e typecheck | PASS | Local, não implantação |
| Sessão | 4 PASS | Script test:auth |
| Tenant/backend-fetch | 10 PASS | Não comprova duas Venues no fluxo financeiro real |
| Visual focado composto | 112 PASS,2,4min | Fixtures, não homologação |
| Lint componentes/helpers/páginas limpas/testes focados | PASS | Comando delimitado abaixo |
| Lint Setup/Impressoras/Conta da casa | FAIL,4 erros de efeito | Assinaturas reproduzidas na base nas slices anteriores |
| Visual amplo com max-failures5 | FAIL:8 PASS/5 FAIL/749 NOT_RUN,1,1min | Runner também informou1erro fora de teste |
| CapturasS1c–S1j | PASS:96 hashes em8manifests | Evidências históricas, não pixels de produção |
| Links da spec/KB/whitespace | PASS:40links locais; KB49docs/298links/12skills | Escopo do checker, não aceite de produto |
| GateR3 autenticado no SHA final | REVIEW_BLOCKED | Reviews locais não aprovam GitHub |

Os [31 hashes de fontes/testes/configuração](../../docs/development/evidence/spec034-composed/source-manifest.json)
identificam o working tree testado e foram conferidos após iniciar a prévia.
next-env.d.ts é gerado pelo Next e foi excluído desse manifest. HEAD não é hash
de commit das alterações locais; não atribuir estes resultados ao código publicado.

## Recorte focado reproduzível

De apps/web, pnpm run test:visual com os13arquivos abaixo, max-failures5:

- management-navigation, management-subpages, management-alerts,
  management-alert-settings;
- management-print-destination, management-print-endpoints, management-print-jobs,
  printing;
- setup, management-setup-layout, management-team-layout;
- management-customer-layout, management-customer-results.

Todos são tests/visual/<nome>.spec.ts. Cobrem navegação/aliases/Back/foco/storage,
quatro larguras e zoom CSS200%, axe/alvos/overflow, estados e comandos simulados,
read-feedback sem confirmação falsa e manutenção de confirmação das mutações.
Não foram criados testes redundantes ou afrouxadas assertions nesta rodada.

Lint limpo incluiu management-settings, management-subpage-header,
management-return, páginas Clientes/Alertas e os dez arquivos de testes focados
management-navigation/subpages/alert-settings/print-destination/print-endpoints/
print-jobs/setup-layout/team-layout/customer-layout/customer-results.
Lint dos três módulos restantes reportou set-state-in-effect em Impressoras24,
Setup44 e Conta da casa108/115. Não suprimido ou corrigido por estética.

## Falhas amplas preservadas

Quatro falhas em attendance-catalog procuram a região legada Outras comandas
via attendance-actions.ts. Uma falha em attendance-credit-bar mede28px no botão
Detalhes, exigindo44px. Mesmas assinaturas dos relatórios anteriores, sem nova
contraprova de baseline nesta rodada; não atribuir causalidade ao patch nem
declarar inexistência de regressão global. Interrupção automática em5falhas.
Nenhuma dessas fontes/testes foi alterada para obter verde.

## Aceite e próxima etapa

AC01/02 e partes de AC03/04/05/09/10/11 têm evidência automatizada acumulada.
AC06–08 pertencem aos recortes S2–S4; não foram implementados nesta rodada.
Leitor de tela, zoom nativo, dispositivo físico, operador, impressão física,
integração real com PostgreSQL descartável, concorrência/replay/revogação e
gatesR3 autenticados: NOT_RUN/pendentes conforme o contrato de cada fluxo.
Reviews independentes locais S1h/S1i/S1j continuam limitados aos hashes relatados.

Decisão: GO para inspecionar a apresentação local e planejar a próxima slice;
NO-GO para merge/release/piloto por estes resultados. Não há aprovação globalS1.
Próximo recorte técnico: S2a Agora, com baseline e contrato específicos antes de
código; não refazer funcionalidades já existentes. Mantenedor responde pelos
gates autenticados e operador pelo aceite humano.

Prévia3001 retomada após build; API8000/dispatcher/PostgreSQL existentes preservados.
Sessão local continua exigindo login; não houve escrita real, seed/reset/migration,
commit/push/merge/deploy. Reversão documental desta rodada não altera produto/dados.
