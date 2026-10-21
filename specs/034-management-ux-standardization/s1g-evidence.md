# S1g — Mesas e zonas em Setup, 2026-10-19

Branch codex/management-ux-alerts, HEAD860b25d93da486d2416c6ddaccfdccd9605f8953.
S1c–S1g locais sem commit; anteriores preservadas. PRs268/269/270 abertas/draft,
main remotae82d36c reconsultadas. R2 de apresentação, SELF_REVIEW.

Recursos confirmados usam listas nomeadas separadas e h3. Novo cadastro usa
fieldset e grade mobile/desktop, sem mudar campos, handlers, gates ou fluxo.
Comparação literal contra HEAD confirmou tipos/estado/handlers e toda a seção
Equipe existente iguais. Rollout, QR, criação incerta e vínculo não redesenhados.

## Evidência

Baseline do buildS1f antes do patch, mesma fixture com duas mesas e uma zona,
nomes longos, sem staff.manage, rollout desativado. Chromium360/390/430/1280x932.
[12 capturas antes/depois e zoom CSS200%, SHA256SUMS](../../docs/development/evidence/spec034-setup/).
Capturas390/1280 inspecionadas: nomes legíveis, consulta separada de cadastro,
sem alterar o painel da equipe. Não há ganho operacional medido ou aceite humano.

- typecheck/build webpack/lint do teste novo: PASS.
- test:auth:4 PASS.
- test:visual management-setup-layout, setup, management-subpages e
  management-navigation:43 PASS,1,6min.
- Sete testes novos: quatro larguras/axe/teclado/alvos/overflow/zoom, mesa→zona,
  rascunho preservado em refresh sem escrita, loading/vazio/erro sem falso vazio.
- Regressão setup existente: resposta perdida mantém barreira de novo cadastro;
  conflito de vínculo reconsulta estado e limpa PIN. Toda escrita interceptada.
- ESLint página: FAIL herdado set-state-in-effect linha44. Reproduzido nesta sessão
  em git show HEAD via stdin, linha43. Efeito intacto; nenhuma supressão adicionada.
- KB e whitespace: PASS. Suíte ampla não repetida; pendênciaS1c de Atendimento
  8PASS/5FAIL/700NOT_RUN permanece, sem gate global verde.

Partes automatizadas AC04/09/10/11 cobertas. Integração real de escrita, permissão
cross-tenant, QR, replay/revogação, leitor de tela, zoom nativo, dispositivo físico,
revisão independente e aceite humano: NOT_RUN. Não fechar Setup ou S1 inteira.

## Operação e próximo passo

Prévia3001 reiniciada após build; browser abriu Setup com API local e listas
carregadas, sem cadastrar ou alterar rollout/equipe. API/dispatcher/banco preservados.
Sem commit/push/merge/deploy. GO somente para inspeção local; sem piloto/produção.
Rollback do JSX/CSS de apresentação não exige migration ou mudança de dados.
Próximo responsável: autor para outra slice delimitada e operador para aceite.
Equipe/Clientes exigem classificação proporcional e revisãoR3 se afetarem
permissões, dinheiro, dados ou recuperação; não flexibilizar por estética.
