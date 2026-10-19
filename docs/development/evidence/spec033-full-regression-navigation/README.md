# E02/E06 — regressão de navegação real

Base PR245 36f3444f. A execução ampla anterior em 0f37fb03 terminou com 106 PASS, 8 FAIL, 29 NOT_RUN (23,9min). Quatro falhas de seletor foram corrigidas em245. As demais usavam Voltar legado na rodada e descarte na superfície resumo.

Delta somente nos testes: rotas reais resumo→catálogo→comanda→conta; descarte/cancelamento na Conta e retorno ao resumo. Repetição usa Voltar atual e seleção das unidades. A antiga assertion de um total em elemento que não existe no protótipo é substituída por quantidade selecionada e quantidade efetivamente enviada; exposição real3400, pagamentos, pedido original, UUID/payload de replay e estados continuam verificados. Não há mudança no produto ou aumento de timeout/retries.

6/6 cenários reais PASS em1,8min, 360/390/430; ESLint/typecheck PASS. Falhas iniciais e tentativa interrompida preservadas. O primeiro ajuste continha um Back excedente e depois um Ver resumo excedente; corrigidos conforme a navegação observada, sem enfraquecer assertions financeiras.

Próximo gate: regressão ampla no HEAD corrigido. Revisão do delta escrito pelo integrador: SELF_REVIEW; revisão independente pendente de contexto disponível (agentes interrompidos por limite de uso). Não apresentar este registro como aprovação R3/GitHub, aceite global ou autorização de merge/deploy.


## Revisão independente e orçamento agregado

Reviewer /root/review_navigation_and_delivery_pixels, contexto novo sem autoria, confirmou NO_FINDINGS_WITH_GAPS no delta36f3444f→4e4c4c62 e na proposta de orçamento restrito. Composição05666768 terminou146PASS/2FAIL/3SKIP em21,9min. Os três skips são o pacote de menuCSV opt-in, que necessita execução separada, não aceite implícito.

Traces revisados independentemente: preparaçãoisolatedFile7,688s em360 e10,329s em390; expectativa final da terceira abertura foi interrompida após175ms/258ms pelo deadline GLOBAL30000ms, antes de seus5s locais.430 passou29,4s. Não há evidência de falha do contrato local de abertura em5s nem causalidade comprovada doSDK.

Ajuste exclusivamente test.setTimeout(90000) no cenário de três comandas, igual ao cenário de repetição real. Preserva limites locais, assertions, número de etapas e zero retries. Nova execução obrigatória; não declarar green a partir do ajuste isolado. Não substituir jornadas por fixtures diretas para contornar o deadline. Aprovação GitHub/aceite global continuam gates separados.


## Regressão composta final — fonte87306a67

Execução real Django/PostgreSQL55634/API8134/Web3134 terminou: **148 PASS,
três skips, 19,5 minutos**, zero retries. Log completo sanitizado de códigos ANSI
em composed-final-pass.log. Os três skips são exclusivamente venue-menu-acceptance,
opt-in RODADA_E2E_MENU; execução separada permanece obrigatória e não é dispensada.
O orçamento de90s aplica-se somente à jornada de três Tabs; expectativas locais
continuam5s. As duas falhas anteriores por prazo global permanecem no log histórico.

Revisão independente /root/review_navigation_and_delivery_pixels inspecionou
mudança de navegação e traces, sem achados reproduzíveis no delta e concordou com
orçamento restrito sem relaxar assertions. Esta revisão não é aprovação GitHub.
Resultado prova a composição87306a67, não main posterior nem aceite global/paridade
integral. Reconciliar mudanças concorrentes e repetir gates pertinentes antes do piloto.
