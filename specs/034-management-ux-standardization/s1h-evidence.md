# S1h — equipe existente, 2026-10-19

Branch codex/management-ux-alerts, HEAD860b25d93da486d2416c6ddaccfdccd9605f8953,
S1c–S1h locais sem commit. PRs268/269/270 abertas/draft e main remotae82d36c
reconsultadas. R3 conservador por contexto de edição de acesso, somente JSX/CSS.

Dois fieldsets Alterar vínculo/Confirmar alteração e estado atual em Surface2.
Labels/IDs/opções/ordem/aviso preservados. Comparação literal do trecho tipos/
estado/load/create/saveMember contra antesS1g confirmou igualdade. Não altera
reauth, expected_version, canManage, sending/busy/fresh, PIN ou readback.

## Validação de autoria

Baseline antes do patch no buildS1g. Mesma fixture de operador de teste com nome
longo e staff.manage, sem venue.configure, mesma seleção/função/situação e PIN
vazio. Chromium360/390/430/1280x932; [12 capturas e SHA256SUMS](../../docs/development/evidence/spec034-team/).
Capturas390/1280 inspecionadas pelo autor e pelo revisor. Nenhum dado real salvo.

- typecheck/build webpack/lint teste novo: PASS.
- test:auth:4 PASS.
- test:tenant: primeira tentativa FAIL de infraestrutura (alias Python ausente);
  repetição com RODADA_TEST_PYTHON apontando ao runtime existente:10 PASS.
  Não comprova isolamento real da edição de vínculos em duas Venues.
- test:visual management-team-layout, management-setup-layout, setup e
  management-subpages:34 PASS,59,2s.
- Nove testes novos: quatro layouts/axe/alvos/zoom/teclado e ausência de escrita;
  PATCH200/403/409 simulado com payload/versão/busy/PIN; reauth recusada sem PATCH;
  capability ausente sem editor ou consulta de memberships.
- Lint página não repetido: falha herdada set-state-in-effect comprovada emS1g,
  trecho de efeito intacto. Não declarar lint da página verde.
- KB/whitespace: PASS. Suíte ampla não repetida; resultadoS1c de Atendimento
  8PASS/5FAIL/700NOT_RUN continua pendente.

## Revisão independente local

Revisor /root/review_team_ux, contexto novo sem autoria, somente leitura conforme
rodada-code-review/pos-safety/CODE-REVIEW. Inspecionou diff isolado contra sources
before-* preservados, testes e capturas390/1280/zoom200. Resultado:
INDEPENDENT / NO_FINDINGS_WITH_GAPS, sem achados reproduzíveis.
Não executou testes e não afirmou confirmar os resultados do autor.

Hashes SHA256 revisados e reconfirmados após adendo visual:

| Arquivo | SHA256 |
| --- | --- |
| apps/web/app/manage/setup/page.tsx | B8285DFEACF8C8DC8F72766051757FD912C780D968BD7BD1B4B2D45B7A033836 |
| apps/web/app/manage/setup/setup.module.css | 093CC595E02A6CE8990DFCEF3475AC2959D259EC504FE3C42A5F63588DDD7BB3 |
| apps/web/tests/visual/management-team-layout.spec.ts | 4BBCC6E5F73BCF8308449FA27E782418F94EA061E6B692F0F3C9F0EACC6ED55A |

Review cobre working tree por hash, não commit novo. Não é aprovação GitHub.
GateR3 autenticado no SHA final: REVIEW_BLOCKED; sem recomendação merge/deploy.
Em zoom CSS200%, título quebra excessivamente e seletor trunca identificação
longa; ambos anteriores e inalterados nesta slice. Capturas não provam leitura
integral da opção. Leitor de tela, zoom nativo e operador continuam pendentes.

## Limites e continuidade

Integração real de escrita/PostgreSQL, duas Venues, revogação e resposta perdida
de alteração de vínculo: NOT_RUN. Fixtures não substituem esses gates. Sem aceite
global de Setup/S1/piloto/produção. GO somente para inspeção local de apresentação.
Rollback reverte JSX/CSS, sem migration/dados. Prévia3001 atualizada; API/dispatcher/
banco preservados; nenhuma permissão, vínculo ou cadastro real alterado.
Editor aparece apenas para staff.manage existente; não ampliar acesso para demo.
Próximo responsável: autor para Clientes/validação composta, mantenedor para gateR3
autenticado e operador para aceite humano. Sem commit/push/merge/deploy.
