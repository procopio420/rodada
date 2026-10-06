# Rodada Catalog Icon Style

## Version

`rodada-icon-v1`

Este documento é o contrato visual para ícones de Product gerados por IA ou preparados manualmente.

O objetivo é que o cardápio pareça um único sistema visual mesmo quando os assets forem criados em momentos diferentes.

## Princípios

- leitura imediata em tela pequena;
- um único assunto principal;
- silhueta reconhecível;
- composição centralizada;
- pouco ruído visual;
- aparência amigável e moderna, sem parecer clip-art genérico;
- consistência entre comida, bebida e itens de bar.

## Canvas

- proporção: `1:1`;
- alvo recomendado: 1024×1024 na geração;
- safe area: manter o assunto principal aproximadamente dentro dos 80% centrais;
- fundo: transparente quando o provider suportar;
- sem moldura embutida no arquivo.

O componente da UI é responsável por superfície, borda, raio e estados de interação. O asset não deve desenhar seu próprio card.

## Estilo visual v1

- ilustração limpa e simplificada;
- formas suaves;
- volume leve;
- detalhe suficiente para reconhecer o produto, mas sem textura excessiva;
- perspectiva consistente, preferencialmente levemente elevada/3D suave;
- iluminação neutra;
- sem cenário;
- sem pessoas;
- sem mãos;
- sem lettering;
- sem logo inventado;
- sem preço;
- sem badge;
- sem sombra pesada fora da safe area.

## Bebidas com marca

Quando o Product representar uma marca específica, não pedir para o modelo inventar embalagem/logotipo.

Preferência:

1. asset oficial/licenciado fornecido pelo estabelecimento;
2. upload manual;
3. ícone genérico da categoria quando não houver asset aprovado.

Exemplo: para `Brahma`, um ícone genérico de cerveja é aceitável como fallback; não gerar um rótulo falso da marca.

## Prompt base

```text
Create one restaurant POS/menu icon for "{product_name}".

Visual contract: Rodada Icon Style rodada-icon-v1.
Square 1:1 composition. One centered subject. Clear silhouette.
Clean simplified illustration with soft volume and neutral lighting.
Readable at small mobile size. Keep the subject inside the central safe area.
Transparent background when supported.
No text, no logo, no price, no badge, no border, no scene, no people.

Category/context: {category_or_description}.
```

Adapters podem ajustar sintaxe para cada provider, mas não devem alterar a intenção visual sem subir `style_version`.

## Exemplos conceituais

### Omelete

Assunto: um omelete dobrado/prato simples, reconhecível de imediato.

Evitar:

- café da manhã inteiro ao redor;
- mesa/cenário;
- talheres dominando a composição;
- texto "omelete".

### Fritas

Assunto: porção única de batatas fritas.

Evitar:

- embalagem com marca inventada;
- combo completo;
- ketchup ocupando o foco principal.

### Cerveja genérica

Assunto: copo/garrafa genérica de cerveja.

Evitar reproduzir identidade de marca sem asset oficial.

## Estados da UI

O ícone deve funcionar dentro dos mesmos componentes em:

- normal;
- indisponível;
- selecionado;
- carrinho;
- lista compacta.

Estados como `UNAVAILABLE` são aplicados pela UI (opacity/overlay/label), nunca queimados no asset.

## Evolução

Mudança significativa de linguagem visual cria uma nova versão, por exemplo `rodada-icon-v2`.

Assets existentes não são regenerados automaticamente. Migração em massa precisa de decisão explícita para evitar custo e mudança visual inesperada.
