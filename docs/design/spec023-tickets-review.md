# Spec023 — revisão de tickets10/10/2026

Main atual45c4742; branch isolada codex/spec023-next, PR68. Branch original6e2f4ca preservada. PR61 sobrepõe apresentação em sua própria base; PR69(cardápio) e70(deploy) independentes, não importados. Serviços locais anteriores foram encontrados parados; somente cluster próprio55523 foi reaberto com dados existentes. Bancos de testes anteriores renomeados e conservados; banco demonstrativo55459 intocado.

Comparação atual antes: tickets16.241%. Candidata21px/metadata6px eliminou quebra de Bolinho no desktop, mas piorou região para17.8714% por posicionamento/composição global diferente. Candidata descartada; CSS e testes de apresentação restaurados ao head, sem tolerância nova ou baseline aceita. [Antes](evidence/spec023-tickets/before) e [candidata rejeitada](evidence/spec023-tickets/rejected) conservam hashes/derivação/pares estáveis.

Não reduzir campos/ações para imitar o mock: P08 exige duas ações individuais, estado/tempo por OrderItem e agrupamento por Order; clientes/localização/equipamento/SLA/provenance ausentes continuam diferenças. Conectividade e heading canônicos ocupam espaço operacional que o export não possui. Dependência de dados de domínio pertence às specs001/003/014/017; Spec023 não inventa esses campos nem vira backlog de backend. Acabamento compartilhado preservado.

Candidata passou197visuais e12auth/realtime, mas isso não aprova paridade. Gates finais após descarte registrados separadamente. Integração revelou seletor ambíguo nos dois avisos legítimos de permissão e corrida de recarga após revogação de recibo; testes agora exigem ambos os avisos, resposta POST de revogação bem-sucedida, erro expirado e ausência de documento. API/produto unchanged; contratos008/015 atualizados. Não se aumentaram timeouts nem afrouxaram critérios.

Gates finais após descarte: types/build12auth/realtime,197visuais e13 integrações reais aprovados, sem skips/retries. Hash da referência608b5814a75482103c840c03fca8a84978bb6fe957a2b509e649fa7b494449c9 e métricas de todas regiões idênticos à captura anterior. Compartilhamento de recibo tem redirect308 de normalização de URL: a sincronização agora exige resposta final canônica, nunca considera redirect sucesso da revogação. Nenhuma alteração de comportamento Web/API.

Snapshots textuais derivados normalizam somente whitespace de fim de linha/final de arquivo para versionamento, sem alterar fonte executável, normalização visual ou captura do browser.
