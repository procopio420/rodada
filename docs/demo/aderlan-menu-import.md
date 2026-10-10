# Cardápio do Bar do Aderlan — importação para o Rodada

**Origem informada em 2026-10-09:** https://www.canva.com/design/DAF3isHSAes/a045e0N-wDx0fB6zuK2XLw/view

**Situação:** link registrado; conteúdo e preços **não extraídos nem verificados**. Este PR entrega o mecanismo de importação, não afirma que o cardápio real já esteja carregado.

## Obter dados reais

1. No Canva, abrir o design e usar **Compartilhar → Baixar → PDF padrão**. Disponibilizar o PDF para revisão.
2. Transcrever do PDF **cada item efetivamente vendido**, incluindo nome, categoria e preço, sem corrigir lacunas por palpite.
3. Marcar **BAR**, **KITCHEN** ou **COZINHA** com confirmação do operador. A arte do cardápio pode não indicar a estação.
4. Diferenciar tamanhos/volumes e variantes comerciais no nome (ex.: 350 ml vs 600 ml), conforme o catálogo atual e a Spec 010. NÃO inventar complementos/variações a partir de uma arte.
5. Conferir cada preço com Aderlan antes de importar e registrar itens desatualizados ou indisponíveis separadamente.

Modelo CSV (UTF-8; delimitador vírgula, valores monetários entre aspas):

```csv
name,category,price_brl,station,description
```

- `price_brl` exige centavos separados por vírgula: `"12,50"` ou `"R$ 12,50"`. Nunca float ou preço estimado.
- `description` é opcional; estação é obrigatória e NÃO pode ser inferida automaticamente.
- O importador rejeita linhas inválidas e nomes iguais após normalização (acentos, caixa, espaços).

## Carregar no ambiente demo local

Com o demo iniciado e os produtos reais em `/caminho/cardapio-aderlan.csv`:

```sh
docker compose -f demo/compose.yaml cp /caminho/cardapio-aderlan.csv api:/tmp/cardapio-aderlan.csv

# Prévia; sem alterar nenhum produto
docker compose -f demo/compose.yaml exec -T api \
  python manage.py import_catalog_csv --file /tmp/cardapio-aderlan.csv --venue-slug bar-do-aderlan

# Só depois da conferência da planilha/preços; atualiza itens com mesmo nome normalizado
docker compose -f demo/compose.yaml exec -T api \
  python manage.py import_catalog_csv --file /tmp/cardapio-aderlan.csv \
    --venue-slug bar-do-aderlan --apply --update-existing
```

As telas do Rodada compartilham a mesma API/DB, portanto consultar Atendimento, Bar, Cozinha, Gerência e Guest após o comando, conferindo preço e estação. Reiniciar o backend não é necessário para persistir os dados.

Sem `--apply`, apenas exibe os totais. Sem `--update-existing`, mantém metadados e preços atuais de produtos já presentes. O script **nunca remove nem desativa produtos ausentes no CSV**, nem altera o status operacional de indisponibilidade. Para a demo, revisar manualmente os quatro placeholders do seed inicial (`Brahma 600ml`, `Fritas`, `Água 500 ml`, `Refrigerante lata`) e desativar por mecanismos administrativos apropriados caso não existam no cardápio real. Não remover itens vinculados a histórico.

`seed_demo` pode ser executado novamente: seus `get_or_create` não devem reverter preços já importados. Este mecanismo importa apenas produtos simples; combinações, modificadores e variantes da Spec 010 exigem análise própria.

## Evidências para concluir

- PDF original arquivado e data/revisor.
- CSV revisado, com linhas conferidas e estação confirmada.
- Transcript do preview e do apply, contagens de criação/atualização.
- Conferência de pelo menos um pedido BAR e um KITCHEN e respectivos preços reais.
- Reimportação repetida sem duplicação.
- Testes Django do importador passando localmente.

**Atenção:** dados do cardápio não são atestado de preços vigentes; a validação final é do estabelecimento. Não executar sincronização contra produção sem autorização.
