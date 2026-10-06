# Spec 005 — Quick Catalog + AI Icons

**Status:** Draft for implementation after Catalog foundation

## Objetivo

Permitir que Bar, Cozinha e Manager criem rapidamente itens do cardápio durante a operação e tenham ícones visuais consistentes gerados por IA, sem tornar IA requisito para vender.

Caso principal:

> "Hoje tem omelete" → Cozinha toca **+ Item**, informa `Omelete` e preço, salva e o Rodada gera um ícone de omelete no padrão visual do produto.

## Usuários

- Bar/Cozinha: cria item rápido da própria estação quando autorizado e controla disponibilidade.
- Manager/Owner: cria/edita qualquer item, revisa/regenera ícones e faz upload manual.
- Guest/Staff: apenas consome o asset publicado no catálogo.

## Invariantes

- geração de imagem nunca bloqueia criação/edição do Product;
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

Salvar cria Product mesmo sem asset.

### CAT-002 — Gerar ícone automaticamente

Na criação/edição, usuário pode habilitar **Gerar ícone com IA**.

Rodada deriva prompt de:

- nome;
- descrição;
- categoria;
- style contract atual.

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
- usuário pode tentar novamente.

### CAT-004 — Preview e regeneração

Manager ou staff autorizado pode:

- visualizar asset;
- regenerar outra variação;
- aceitar/publicar a nova imagem;
- manter a atual enquanto uma nova é gerada.

Regenerar não deixa o produto temporariamente sem o ícone já publicado.

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
