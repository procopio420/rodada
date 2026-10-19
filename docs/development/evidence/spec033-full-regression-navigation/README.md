# E02/E06 — regressão de navegação real

Base PR245 36f3444f. A execução ampla anterior em 0f37fb03 terminou com 106 PASS, 8 FAIL, 29 NOT_RUN (23,9min). Quatro falhas de seletor foram corrigidas em245. As demais usavam Voltar legado na rodada e descarte na superfície resumo.

Delta somente nos testes: rotas reais resumo→catálogo→comanda→conta; descarte/cancelamento na Conta e retorno ao resumo. Repetição usa Voltar atual e seleção das unidades. A antiga assertion de um total em elemento que não existe no protótipo é substituída por quantidade selecionada e quantidade efetivamente enviada; exposição real3400, pagamentos, pedido original, UUID/payload de replay e estados continuam verificados. Não há mudança no produto ou aumento de timeout/retries.

6/6 cenários reais PASS em1,8min, 360/390/430; ESLint/typecheck PASS. Falhas iniciais e tentativa interrompida preservadas. O primeiro ajuste continha um Back excedente e depois um Ver resumo excedente; corrigidos conforme a navegação observada, sem enfraquecer assertions financeiras.

Próximo gate: regressão ampla no HEAD corrigido. Revisão do delta escrito pelo integrador: SELF_REVIEW; revisão independente pendente de contexto disponível (agentes interrompidos por limite de uso). Não apresentar este registro como aprovação R3/GitHub, aceite global ou autorização de merge/deploy.
