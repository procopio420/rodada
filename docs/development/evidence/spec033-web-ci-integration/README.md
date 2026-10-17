# Spec 033 — integração dos testes das páginas Web

Integração da PR #224: `752a831b` reúne a regressão das cinco suítes de páginas, mantendo as correções de produção já existentes em `6afc602f`; `02be9e80` migra lifecycle, paginação e busca global. Não houve conflito de merge nem alteração adicional de produção nesta integração.

A evidência da branch de regressão está em `../spec033-page-regressions/README.md`: 12 cenários reais com Django/PostgreSQL passaram em 3,3 min, sem retries. Inclui perda de ACK/replay idêntico, histórico e estação canônicos, reversões financeiras, rascunhos por Tab e mesa compartilhada. As assertions de identidade, payload, UUID, ledger e isolamento permanecem.

Os três testes restantes foram executados na branch fonte `a46e274c`, em banco PostgreSQL real isolado na porta 55634 (API 8134/Web 3134). A execução inicial teve 2 PASS/1 FAIL: paginação da 201ª Tab e busca global de homônimos passaram; lifecycle falhou por texto exato legado sem o estado traduzido. Após exigir o item completo com estado Novo, lifecycle passou isoladamente em 13,5 s (22,4 s incluindo setup). Os dois logs, inclusive a falha, estão preservados nesta pasta. Não se declara uma única execução 3/3 nem execução desses cenários no SHA composto.

Revisão da integração: os seletores acompanham as páginas reais, os retornos aguardam estado observável e as verificações financeiras não foram removidas. A integração não executou flush ou servidores em bancos de outros agentes. A regressão Web completa e CI ainda são gates; esta evidência não concede paridade visual, aceite Android ou conclusão de épico.
