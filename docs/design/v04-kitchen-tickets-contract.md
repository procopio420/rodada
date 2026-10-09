# V04 parcial — contrato prévio dos tickets

09/10/2026. Base `origin/main` 742faac; branch isolada `codex/v04-kitchen-tickets`, com infraestrutura V03 reutilizada do commit 570a832. Escopo: agrupamento visual por Order no ProductionBoard de Cozinha/Bar; mudanças funcionais da API fora do escopo.

Fonte: export Cozinha atualizado, ZIP SHA256 ffa32367f3a04131922f75f2d7ebb4968c92e01451c7c32d6e4be1a94d428e63. Fixture e normalizações V03 preservadas. Diferença antes: cinco tickets agrupados no export versus seis blocos visuais por OrderItem no Web (P08 duplicado).

Contrato: agrupar somente order_id explícito; fallback por item.id com namespace diferente. Ordem por primeira ocorrência na fila, sem reconstruir intenção de domínio. Destino aparece uma vez por grupo; cada item mantém quantidade/nome/customização/estado/tempo e sua própria ação no endpoint original. Ação coletiva Pronto não pode ser inferida de um botão demonstrativo.

As seis linhas/action handlers e os DTOs continuam iguais; agrupamento não altera ledger, disponibilidade, dados financeiros ou estado confirmado. Erro, rede e lock de mutation seguem guardas existentes. Um POST bem-sucedido e a releitura podem remover um item pronto do grupo; os demais continuam.

No desktop, preservar 84 px para destino e 116×56 para ação, com conteúdo flexível. Mobile mantém destino acima dos itens e ações legíveis/tocáveis. Labels completos e customizações permanecem; metadata que a API não fornece não será inventada.

Reuso de checks: teste V03 mantém igualdade de dados e compara export inalterado; observação da Tab passa a usar o contexto do grupo. Novo check confirma 5 grupos/6 ações, geometria, fallback sem order_id, Orders distintos com a mesma Tab e POST isolado. Layout/a11y já existentes cobrem conteúdo longo, estados e superfície Bar adjacente.

O gate pixelmatch 0.1/includeAA false e tolerância 0,1% permanecem. Comparação de tela e tickets segue exposta, incluindo conectividade, metadados e diferença entre ação ilustrativa agrupada e ações reais individuais. Este aceite parcial não declara V04 global nem pixel-perfect da tela.
