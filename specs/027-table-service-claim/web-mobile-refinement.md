# Atendimento Web: comandas e mesas no celular

## Escopo entregue

- Contas: paginação compacta com setas e 10 comandas por página.
- Nome da Comanda sempre visível e obrigatório no Atendimento.
- Abertura contextual escolhe mesa disponível ou ocupada. Mesa disponível usa comando atômico `service/open-tab`; mesa ocupada usa a ocupação existente e geração observada.
- Removida faixa informativa duplicada abaixo de Comandas abertas.
- Mesas: cartões com estado e contagem de comandas abertas; toque expande ações. Fundo quente e destaque âmbar seguem Contas.
- Formulário de pessoas removido dessa superfície; comandas não são uma contagem exata de pessoas.
- Mover comanda abre diretamente o diálogo e permite outra mesa ocupada. Recuperação, autorização e confirmação existentes são preservadas.
- Gerência: gestão de quantidade, cadastro, retirada e reativação de mesas documentada em `../004-table-guest-ordering/management-tables.md`.

## Validação local

Fechamento de 2026-10-14: 33 testes visuais focados PASS (Contas, paginação, busca, serviço de mesas, Gerência e cartões móveis). API: 42 testes PASS em SQLite; 2 testes de concorrência recusaram SQLite explicitamente por exigir PostgreSQL, portanto não constituem prova de concorrência nesta execução. Revisão independente incremental final: sem bloqueadores. Build/TypeScript e `git diff --check` PASS.

Build e TypeScript passaram. Testes focados de serviço de mesas: 10 cenários passaram antes do refinamento visual final. Testes móveis do refinamento final: 3 cenários passaram em 360, 390 e 430 px, incluindo acessibilidade, abertura direta do diálogo e escolha de outra mesa ocupada. Gateway autenticado passou. Django check e makemigrations sem alterações passaram; lint dos arquivos novos de API passou. Revisão independente identificou e confirmou correção do fallback de rollout desativado.

Limites: suite visual completa e integração completa não foram reexecutadas para este refinamento. Novas corridas PostgreSQL específicas de `service/open-tab` e matriz completa de capabilities desse endpoint permanecem sem evidência dedicada. Não representa homologação em aparelho ou estabelecimento nem autorização de deploy.
