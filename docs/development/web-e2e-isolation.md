# Isolamento dos cenários Web/API

A suíte integrada tem cenários que alteram preço/disponibilidade do catálogo e
ownership das chamadas. Uma base nova apenas no início da suíte não isola testes:
o efeito de um cenário pode contaminar preço, filas e seletores do seguinte.

Contrato de QA: reset opt-in RODADA_E2E_RESET=1 somente no banco PostgreSQL
rodada_web_e2e, host loopback, com RODADA_E2E_POSTGRES=1. Executar entre testes,
quando o contexto anterior já foi encerrado, reutilizando a mesma fixture de
inicialização. Preservar migrations; remover exclusivamente dados de teste e
recriar identidades/catálogo/caixa de teste. Nenhuma rota de reset na aplicação,
comando comercial ou acesso a banco de demo/produção é introduzido.

Aceite: cada cenário começa com preço1000/500, disponibilidade AVAILABLE,
sem comandas/chamadas/pagamentos, identidades e sessão expirada conhecidas.
Flags/banco/host incorretos recusam reset. Cenários dentro de um mesmo teste
continuam compartilhando seu estado e suas assertions de replay/concorrência.

Consultas assíncronas/outbox podem terminar depois de o navegador fechar. Em
deadlock PostgreSQL40P01, repetir até três vezes somente a transação de limpeza
já revertida integralmente; demais erros continuam falhando. Isso não repete
cenários nem comandos do produto. O runner mantém retries=0.
