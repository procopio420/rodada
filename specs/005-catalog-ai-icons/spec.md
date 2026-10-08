# Spec 005 — Quick Catalog + AI Icons

**Status:** Implemented and verified; real generated-art approval pending provider credentials. See acceptance.md.

## Objetivo

Permitir que Bar, Cozinha e Manager criem rapidamente itens do cardápio durante a operação e tenham ícones visuais consistentes gerados por IA, sem tornar IA requisito para vender.

Caso principal:

> "Hoje tem omelete" → Cozinha toca **+ Item**, informa `Omelete` e preço, salva e o Rodada gera um ícone de omelete no padrão visual do produto.

## Usuários

- Bar/Cozinha: cria item rápido da própria estação quando autorizado e controla disponibilidade.
- Manager/Owner: cria/edita qualquer item, pode substituir o ícone e revisar/regenerar quando necessário.
- Guest/Staff: apenas consome o asset publicado no catálogo.

## Invariantes

- o campo de nome funciona como autocomplete/typeahead do catálogo do Venue;
- selecionar sugestão existente resolve o Product existente; nunca cria cópia silenciosa;
- confirmar um nome sem correspondência exata faz `resolve-or-create` atômico do Product;
- cada Product possui uma identidade visual própria: seu ProductIcon é 1:1 e permanece atrelado ao item ao longo do tempo;
- autocomplete, staff, Bar/Cozinha e Guest sempre resolvem o mesmo ProductIcon publicado daquele Product;
- geração de imagem é automática a partir de nome/descrição/contexto quando um Product é criado sem ícone manual;
- geração de imagem nunca bloqueia criação/edição do Product;
- o fluxo primário não expõe botão/toggle “Gerar ícone”; isso é comportamento padrão do catálogo;
- Product existe e pode ficar disponível mesmo sem ícone;
- ícone não participa de preço, ledger, ordering ou fulfillment;
- estação do quick create é herdada da superfície atual por padrão;
- toda geração usa um style contract versionado do Rodada;
- prompt gerado, provider/model e resultado ficam rastreáveis;
- asset gerado pode ser substituído ou removido sem alterar Product/Orders;
- falha de geração resulta em fallback/placeholder, não em erro de venda;
- prompts/inputs não devem incluir dados pessoais de clientes.

## Modelo conceitual

### ProductIcon

Relação estável **1:1 com Product**. O ProductIcon nasce junto com o Product, mesmo que inicialmente só represente placeholder/`GENERATING`.

Campos mínimos:

- `product_id` único;
- `source`: `AI_GENERATED | UPLOADED | NONE`;
- `status`: `NONE | GENERATING | READY | FAILED`;
- `published_asset_url` ou referência de storage;
- referência opcional a asset candidato enquanto uma nova geração está em andamento;
- `prompt` quando gerado;
- `style_version`;
- `provider` e `model` quando aplicável;
- `created_by`;
- `created_at`;
- `updated_at`.

O vínculo Product ↔ ProductIcon não muda quando o nome, preço, disponibilidade ou asset mudam. O mesmo ícone publicado é reutilizado em todas as superfícies. Histórico/revisões de assets podem ser preservados internamente, mas pertencem sempre ao mesmo ProductIcon.

## Histórias

### CAT-001 — Nome com autocomplete + resolve-or-create

Bar/Cozinha autorizado toca **+ Item** na tela da estação.

O primeiro campo é um typeahead de Product do Venue. Enquanto o operador digita, o Rodada retorna itens existentes relevantes com:

- ícone publicado/placeholder;
- nome;
- preço atual;
- estação;
- disponibilidade.

Comportamento:

- selecionar um resultado reutiliza o Product existente e seu ProductIcon;
- correspondência exata normalizada nunca cria duplicata;
- se não houver correspondência exata, a última opção é **Criar "{nome digitado}"**;
- confirmar essa opção executa `resolve_or_create_product` de forma atômica;
- em corrida concorrente, dois operadores tentando criar o mesmo nome normalizado convergem para um único Product.

Para Product novo, completar:

- preço;
- estação preenchida automaticamente;
- categoria opcional;
- descrição opcional;
- disponibilidade inicial, default `AVAILABLE`.

A criação gera Product + ProductIcon juntos. Se não houver upload manual, a geração do asset é enfileirada automaticamente a partir do nome/descrição/contexto.

### CAT-001A — Normalização e busca

Para evitar duplicatas óbvias, Catalog mantém uma chave normalizada de busca/identidade dentro do Venue, por exemplo:

- trim;
- espaços internos normalizados;
- comparação case-insensitive;
- comparação accent-insensitive quando tecnicamente viável.

Autocomplete pode usar prefixo + busca tolerante/fuzzy, mas **fuzzy match nunca cria/mescla Product automaticamente**. Só uma correspondência exata normalizada impede a criação.

Produtos realmente distintos devem ter nomes suficientemente distintos, por exemplo `Coca-Cola 350 ml` e `Coca-Cola 600 ml`.

### CAT-002 — Gerar ícone automaticamente

Ao criar um Product sem ícone manual, o Rodada gera o ícone automaticamente. Não existe toggle/botão de geração no fluxo primário.

Rodada deriva o contexto de geração de:

- nome;
- descrição;
- categoria;
- fulfillment station quando útil;
- style contract atual.

Se nome, descrição ou categoria mudarem materialmente depois:
- quando o ícone atual for `AI_GENERATED` ou `NONE`, o sistema pode gerar automaticamente um novo candidato;
- o asset publicado atual permanece visível até o novo ficar pronto;
- se o ícone atual for `UPLOADED`, a edição textual não o substitui automaticamente.

Exemplo conceitual:

```text
Omelete
+ comida / cozinha
+ Rodada menu icon style v1
→ ícone de omelete consistente com o restante do cardápio
```

### CAT-003 — Não bloquear operação

Se a geração demorar ou falhar:

- Product continua salvo;
- catálogo usa placeholder consistente;
- status mostra `GENERATING` ou `FAILED`;
- o sistema pode executar retries limitados; depois mantém placeholder/ícone anterior e registra falha para revisão.

### CAT-004 — Publicação e regeneração excepcional

A primeira geração bem-sucedida pode ser publicada automaticamente quando não existe ícone anterior.

Em edição, uma nova geração automática é tratada como candidato e só substitui o asset publicado quando estiver pronta.

Manager ou staff autorizado pode, numa ação secundária de edição, solicitar outra variação se o resultado estiver ruim. Essa ação não faz parte do fluxo rápido de criação.

Regenerar nunca deixa o produto temporariamente sem o ícone já publicado.

### CAT-005 — Upload manual

Usuário autorizado pode substituir imagem gerada por upload manual.

Upload passa pela mesma normalização visual de tamanho/formato quando possível.

### CAT-006 — Remover ícone

Usuário pode voltar ao placeholder padrão sem remover o Product.

### CAT-007 — Consistência visual

Todos os ícones gerados devem seguir o contrato visual do Rodada:

- composição centralizada;
- leitura clara em tamanhos pequenos;
- enquadramento 1:1;
- fundo transparente quando suportado;
- sem texto/logotipo dentro do ícone;
- iluminação, traço e nível de detalhe coerentes;
- safe area consistente para não cortar o alimento/bebida;
- sem estilos aleatórios por geração.

O contrato é versionado. Alterar o design system não exige regenerar automaticamente ícones existentes.

### CAT-008 — Superfícies e identidade visual

O mesmo ProductIcon/asset publicado aparece em:

- autocomplete;
- catálogo do staff;
- Bar/Cozinha;
- menu guest/QR;
- telas gerenciais que exibam Product.

Não manter cópias independentes por canal e não gerar ícone a partir do nome em cada render. O ícone é dado persistente do Product, não decoração calculada pela tela.

## Integração de IA

O domínio de Catalog não depende diretamente de um vendor.

Porta conceitual:

```text
CatalogIconGenerator
  generate(product_context, style_contract) -> GeneratedAsset
```

Adapter de provider fica em infraestrutura.

A requisição pode ser processada fora do request principal; persistir status permite polling/realtime sem bloquear criação do Product.

## Prompt contract

Prompt deve ser construído pelo sistema, não depender de o operador saber escrever prompt.

Exemplo v1:

```text
Create one clean restaurant menu icon for "{product_name}".
Use the Rodada icon style contract {style_version}.
Centered single subject, square composition, transparent background when supported,
clear silhouette, readable at small size, no text, no logo, no border.
Product context: {description/category}.
```

O prompt real pode mudar por provider sem mudar o comportamento de produto.

## API/concorrência

Portas/comandos conceituais:

```text
suggest_products(venue_id, query, station?) -> ProductSuggestion[]
resolve_or_create_product(venue_id, normalized_name, defaults) -> Product
CatalogIconGenerator.generate(product_context, style_contract) -> GeneratedAsset
```

`resolve_or_create_product` precisa de proteção transacional/constraint para evitar duplicatas por corrida.

## Segurança e custo

- geração exige autenticação e permissão;
- rate limit por Venue/Staff;
- deduplicar geração automática causada pelo mesmo conteúdo de Product;
- evitar regeneração acidental repetida;
- registrar custo/usage técnico quando provider fornecer;
- validar MIME/dimensões de uploads;
- servir assets por storage/CDN apropriado;
- não enviar dados de Customer/Tab/Order ao gerador.

## Fora de escopo inicial

- gerar fotografia realista de prato automaticamente;
- reconhecimento de foto para criar Product;
- geração de descrição/preço por IA;
- remoção automática de fundo de uploads se exigir pipeline complexo;
- regeneração em massa de todo catálogo;
- cobrança do cliente por geração.

## Runtime contract (implementation)

- Creation capabilities are `catalog.create.bar` and `catalog.create.kitchen`. Manager/Owner receive both; station operators require an explicit membership allow override. UI context never grants authorization.
- Quick-created products are active and AVAILABLE immediately; exact matches retain their existing price, station, activation and availability.
- A durable database outbox is created with Product + ProductIcon atomically. `process_icon_jobs` performs provider I/O outside the transaction, with leases, three bounded attempts and stable upstream idempotency keys.
- Automatic requests coalesce by catalog content + `rodada-icon-v1`; manager variations require an idempotency key. Manual upload/reset increments revision so an older worker cannot overwrite it.
- Rate limits: manager requests 20/operator/hour and 60/venue/hour; automatic jobs are queued and provider starts are capped at 60/venue/hour.
- Runtime uses a configurable HTTPS image-provider gateway (documented in Catalog README), with no fake adapter fallback. CI supplies an injected deterministic generator only.
- PNG/JPEG/WebP uploads: maximum 5 MB; square 128–2048 px; decoded and normalized to PNG. Only published assets are served publicly by opaque icon/asset identifiers.
- Migration stops on accent-normalization collisions for explicit operator reconciliation; it never merges existing products or rewrites historical order references.
