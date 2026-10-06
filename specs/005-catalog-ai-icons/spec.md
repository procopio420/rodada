# Spec 005 — Quick Catalog + AI Icons

**Status:** Draft for implementation after Catalog foundation

## Objetivo

Permitir que Bar, Cozinha e Manager criem rapidamente itens do cardápio durante a operação e tenham ícones visuais consistentes gerados por IA, sem tornar IA requisito para vender.

Caso principal:

> "Hoje tem omelete" → Cozinha toca **+ Item**, informa `Omelete` e preço, salva e o Rodada gera um ícone de omelete no padrão visual do produto.

## Usuários

- Bar/Cozinha: cria item rápido da própria estação quando autorizado e controla disponibilidade.
- Manager/Owner: cria/edita qualquer item, pode substituir o ícone e revisar/regenerar quando necessário.
- Guest/Staff: apenas consome o asset publicado no catálogo.

## Invariantes

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

Campos mínimos:

- `product_id`;
- `source`: `AI_GENERATED | UPLOADED | NONE`;
- `status`: `NONE | GENERATING | READY | FAILED`;
- `asset_url` ou referência de storage;
- `prompt` quando gerado;
- `style_version`;
- `provider` e `model` quando aplicável;
- `created_by`;
- `created_at`;
- `updated_at`.

Product mantém no máximo um ícone publicado por vez. Histórico de assets antigos pode ser preservado para auditoria/reuso sem aparecer no menu.

## Histórias

### CAT-001 — Adicionar item rápido

Bar/Cozinha autorizado toca **+ Item** na tela da estação.

Campos mínimos:

- nome;
- preço;
- estação preenchida automaticamente;
- categoria opcional;
- descrição opcional;
- disponibilidade inicial, default `AVAILABLE`.

Salvar cria Product imediatamente e, se não houver upload manual, enfileira automaticamente a geração do ProductIcon usando nome, descrição, categoria e style contract.

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

### CAT-008 — Superfícies

O mesmo asset publicado aparece em:

- catálogo do staff;
- Bar/Cozinha;
- menu guest/QR;
- telas gerenciais que exibam Product.

Não manter cópias independentes por canal.

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
