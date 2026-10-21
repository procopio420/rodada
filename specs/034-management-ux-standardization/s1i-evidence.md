# S1i — busca e cadastro de Clientes, 2026-10-20

Branch codex/management-ux-alerts, HEAD860b25d93da486d2416c6ddaccfdccd9605f8953.
S1c–S1i locais sem commit; alterações anteriores preservadas. PRs268/269/270
abertas/draft, main remotae82d36c reconsultadas. R3 conservador por financeiro/PII.

Busca e cadastro/relacionamento usam dois fieldsets e CSS Module local. Mesma
ordem de campos/resultados, mesmos labels/IDs/controls. Comparação literal de
tipos/estado/handlers com before-house-account.tsx confirmou igualdade. Políticas,
override/replay, visitas, associação, centavos e gates não foram alterados.

## Evidência de autoria

Baseline antes do patch no buildS1h, fixture com customer.manage e cliente de
teste com nome longo/telefone vazio. Mesmo estado após busca, Chromium nas
larguras360/390/430/1280x932. [12capturas e SHA256SUMS](../../docs/development/evidence/spec034-customers/).
Autor inspecionou390 normal/zoom e revisor antes/depois390/1280/zoom390.

- build webpack/typecheck/lint do teste novo: PASS.
- test:auth4 PASS; test:tenant10 PASS com RODADA_TEST_PYTHON existente.
- test:visual management-customer-layout, management-subpages e
  management-team-layout:35 PASS,50,6s na execução final.
- Nove casos novos: quatro layouts/axe/teclado/alvos/zoom; cadastro200/403 com
  payload/busy/entrada preservados; erro de busca sem POST; ausência do editor
  sem capability; inspeção de limite somenteGET preserva valores canônicos.
- Primeira execução:32 PASS/3 FAIL em overflow no zoom200 mobile. Diagnóstico
  focal390:1 FAIL e label/input com borda direita456px para viewport390px.
  Corrigido no CSS local com minmax(0,1fr) e quebra de label; assertions intactas,
  diagnóstico temporário removido. Execução final35 PASS.
- Lint componente:2 FAIL herdados set-state-in-effect linhas108/115; reproduzidos
  em git show HEAD via stdin nas107/114. Sem supressão ou alteração de efeitos.
- KB/whitespace PASS. Suíte ampla não repetida; resultadoS1c de Atendimento
  8PASS/5FAIL/700NOT_RUN permanece pendente, sem gate global verde.

## Revisão independente local

Contexto /root/review_team_ux, sem autoria, somente leitura conforme skills de
review/pos-safety e protocolo local. Comparou source antes/depois, teste e CSS,
reavaliou correção de reflow e capturas. INDEPENDENT / NO_FINDINGS_WITH_GAPS,
sem achados reproduzíveis atribuíveis ao diff; testes executados pelo autor.

Hashes finais revisados:

| Arquivo | SHA256 |
| --- | --- |
| apps/web/components/house-account.tsx | D9181D0DB3E39F9B58D6C021BFB29947A92CD134D1A99BE72EF04439E7C6B8EB |
| apps/web/components/house-account.module.css | 184B40C40A270DF9D0928047508D6856B04918F2818B2EA57F3D6012FD8AA3D9 |
| apps/web/tests/visual/management-customer-layout.spec.ts | 1E0C483EA131C84BFE7F75C3EFD396CC87D052EA538CF4B872027EAF4114EC2F |

Review cobre working tree por hash, sem commit novo. GateR3 autenticado no SHA
final: REVIEW_BLOCKED. Sem aprovação GitHub ou recomendação merge/deploy.

Limitações herdadas: action() usa mensagem genérica de alteração confirmada após
GET de busca; não é prova de escrita financeira. Resultados/ações fora dos novos
grupos quebram palavras excessivamente em zoom200. Não declarar aceite global de
Clientes por continuidade desses comportamentos; candidatos a recortes próprios.

## Operação e continuidade

Retomada em20/10 encontrou Web/API/PostgreSQL parados; cluster existente55460,
banco local, API8000, dispatcher e prévia3001 retomados sem seed/reset/migration.
Readiness API e HTTP de Clientes200. Browser aberto em Clientes para inspeção;
nenhum cliente real criado nem relação/política/limite alterado. Testes interceptam
escritas no browser, sem usar banco compartilhado.
Conferência final do browser: sessão exige autenticação de staff; formulários reais
não foram percorridos nesta retomada. Usuário deve entrar pelo fluxo existente,
sem ampliar capability ou inferir credenciais. Pixels validados são da fixture.

Integração financeira/PII em PostgreSQL descartável, duas Venues, revogação,
replay/resposta perdida real, leitor de tela, zoom nativo e aceite humano: NOT_RUN.
GO somente para inspeção local da apresentação. Sem aceite global/S1/piloto.
Rollback reverte wrappers/CSS sem dados. Próximo responsável: autor para resultados/
feedback herdado ou composição, mantenedor para gateR3 e operador para aceite.
Sem commit/push/merge/deploy.
