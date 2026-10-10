# Spec 024 — Importação revisada de cardápio de Venue

**Estado:** implementação inicial em PR; dados reais do Canva ainda pendentes de acesso/verificação.

## Problema
O Bar do Aderlan já possui cardápio publicado no Canva, mas a demo usa quatro produtos fictícios. Precisamos de um caminho repetível e seguro para promover uma transcrição humana revisada para o catálogo canônico do Rodada, sem criar um segundo catálogo.

## Contrato do slice inicial
- Fonte auditável: link Canva original, export PDF e CSV verificado.
- CSV UTF-8 com `name,category,price_brl,station` e `description` opcional.
- Preços em BRL com duas casas decimais e persistência em centavos inteiros.
- Station explicitamente `BAR`/`KITCHEN` (alias `COZINHA`); nunca supor roteamento.
- Identidade de produto por Venue e nome normalizado existente, sem fuzzy merge.
- Validação completa de arquivo, nomes, preços, roteamento e duplicados antes de qualquer gravação.
- Dry-run default; `--apply` obrigatório para escrever; `--update-existing` explícito para atualizar itens existentes.
- Importação transacional e idempotente; não alterar ProductAvailability, histórico, reservas, contas ou ícones pré-existentes.
- Novos Products usam o fluxo canônico de ProductIcon. Nenhum serviço de IA é pré-requisito.
- Produtos ausentes não são excluídos/desativados automaticamente.
- O importador deve falhar quando o Venue não existir.

## Fora de escopo
- Scraping autenticado do Canva ou OCR automático não revisado.
- Geração de preços/fotos/categorias/routing por IA.
- Gestão de fichas técnicas, estoque, tributos ou custo.
- Variantes e modificadores estruturados (Spec 010).
- Sincronização contínua de catálogo ou UI de upload em produção.
- Habilitar vendas no estabelecimento sem homologação operacional.

## Integração
`Product`, `ProductIcon`, `Venue` e APIs atuais são fonte única de verdade. Seed demo existente continua provisionando o Venue; o arquivo revisado complementa/atualiza seus produtos.
