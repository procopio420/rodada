# Bar do Aderlan — cardápio real para demo Rodada

**Fonte:** [cardápio do Canva](https://www.canva.com/design/DAF3isHSAes/a045e0N-wDx0fB6zuK2XLw/view) e **sete screenshots enviados em 2026-10-09** (capa + páginas 2 a 7 com itens). Não depende mais da exportação do PDF.

**Catálogo transcrito:** [CSV versionado](../../apps/api/modules/catalog/data/aderlan-menu-2026-10-09.csv) — **143 produtos**.
O CSV é um retrato do cardápio mostrado nas imagens, **não uma garantia de preços vigentes**. Antes do piloto comercial, validar com Aderlan.

| Categoria | Produtos | Estação |
| --- | ---: | --- |
| Caldos | 5 | KITCHEN |
| Pratos | 6 | KITCHEN |
| Porções | 4 | KITCHEN |
| Salgados | 16 | KITCHEN |
| Cervejas | 41 | BAR |
| Destilados | 26 | BAR |
| Drinks | 13 | BAR |
| Bebidas | 32 | BAR |
| **Total** | **143** | **31 KITCHEN / 112 BAR** |

## Preparar o app na máquina da demo

Na branch atualizada do Rodada:

```sh
# Banco da demo PostgreSQL existente, preservado; NÃO utilizar down -v
docker compose -f demo/compose.yaml up -d --build api dispatcher web

# Garantir importação também quando já existia um banco/seed anterior
docker compose -f demo/compose.yaml exec -T api python manage.py seed_demo_catalog

# Conferir catálogo e saúde da API
curl -fsS http://localhost:18764/ready/
```

A instalação nova cria os 143 produtos no Venue `bar-do-aderlan`. A reaplicação não duplica nada, e não redefine preço/ícone/disponibilidade já alterado por operadores.

**Se for desejado alinhar também os preços/metadados de itens preexistentes** após revisão com Aderlan, executar:

```sh
docker compose -f demo/compose.yaml exec -T api python manage.py import_catalog_csv \
  --file /app/apps/api/modules/catalog/data/aderlan-menu-2026-10-09.csv \
  --venue-slug bar-do-aderlan --update-existing

# Preview acima SEM escrita. Só após conferir:
docker compose -f demo/compose.yaml exec -T api python manage.py import_catalog_csv \
  --file /app/apps/api/modules/catalog/data/aderlan-menu-2026-10-09.csv \
  --venue-slug bar-do-aderlan --update-existing --apply
```

Não deleta/desativa os três antigos placeholders `Fritas`, `Água 500 ml`, `Refrigerante lata`, que podem permanecer em bancos anteriores. Verificar e desativar esses **três nomes exatos** pela gestão se forem de fato fictícios e não mais vendidos. `Brahma 600ml` já corresponde a um item real.

No app, conferir Android Atendimento, Gerência/Catálogo, Bar, Cozinha e Guest/QR. Criar um pedido com um item de BAR e outro de KITCHEN; conferir o valor lançado em centavos e o ticket correto. O app continua sem homologação para produção.

## Pontos que merecem confirmação do Aderlan

1. **Página 3:** `Arroz Negro com Frutos do Mar` (R$35) tem descrição claramente copiada de um hambúrguer. O CSV usa só nome/preço, não replica essa descrição.
2. **Página 5:** imagem traz `Brahama` em 300ml; normalizado como `Brahma 300ml` (R$6), **confirmar ortografia**.
3. **Página 7:** `Água Mamba sem Gás` (R$4) e `Água sem Gás` (R$5), além de alternativas com gás e preços distintos; ambas foram mantidas sem mesclar.
4. **Página 6:** `Pinga com Mel` (R$5) na seção Doses e (R$10) na seção Drinks; nomeado distintamente como `(dose)` e `(drink)`.
5. **Página 6:** `Cachaça G/P` e `Licor 43 G/P` preservam essa indicação textual, sem inventar mililitros.
6. **Página 3:** `Paleta Suína Defumada` aparece com `Inteira` R$120 e `Meia` R$70; criadas como **duas opções vendáveis**, sem implementar variantes vinculadas.
7. **Página 2:** `Carne com Batata ou Mandioca` (R$25) é produto único com instrução de escolha no campo descrição; modifier obrigatório ainda não está configurado.
8. Outros produtos listados sem tamanho específico (`Fys Sabores`, `Guaraná`, `H2O` etc.) mantiveram o nome genérico; exigir especificação no pedido se houver várias embalagens reais.
9. Destino BAR/COZINHA atribuído por categoria, **não confirmado com a equipe**, revisar itens que possam ser montados no bar.
10. Cardápio fotografado pode estar desatualizado. Nenhum preço deve ser considerado homologado até validação no local.

## Contrato de importação

O comando `import_catalog_csv` recebe arquivo UTF-8 com colunas `name,category,price_brl,station,description`. `price_brl` exige formato brasileiro (ex.: `R$ 25,00`); valida arquivo inteiro antes de escrever. `--apply` é obrigatório para qualquer escrita. `--update-existing` opt-in permite alterar produtos já cadastrados mantendo disponibilidade, identidade e histórico. Duplicatas por nome normalizado são rejeitadas. Ausências no arquivo não causam exclusão/desativação.

Os ícones usam o pipeline/fallback canônico e não são necessários para realizar vendas. CSV não modela modificadores e variantes da Spec 010.

## Critérios práticos de conclusão

- [x] Todas as seis páginas com produtos transcritas para CSV (143 linhas) a partir dos screenshots recebidos.
- [x] Seed da demo preparado para reutilizar fonte canônica.
- [ ] Confirmar preços e roteamento com o estabelecimento.
- [ ] Executar CI/testes e registrar resultado.
- [ ] Deploy na máquina via Docker Compose + rodar seed no banco da demo.
- [ ] Pedido real de teste KITCHEN + BAR validado na UI e API.
