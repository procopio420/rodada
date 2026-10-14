# Spec 010 — Product Modifiers & Variants

**Status:** Implemented; verification recorded in acceptance.md
**Owner capability:** Catalog + Ordering snapshot semantics

## Objective

Define hospitality-native customization for menu items while preserving fast ordering, canonical availability and immutable confirmed-order snapshots.

## Product problem

Real bar/restaurant orders need choices such as size, flavor, “sem cebola”, cheese/add-ons and required selections. Free-text notes alone are too ambiguous for pricing, availability, production and guest ordering, but generic ecommerce variant modeling would add unnecessary complexity.

## Scope

- Product variants;
- modifier groups/options;
- required/optional and min/max selection;
- single/multi-select;
- zero/additional price;
- removals/add-ons/flavors/sizes;
- defaults;
- variant/modifier availability;
- snapshot into confirmed OrderItem;
- ordering/editing rules;
- staff/guest production display and ergonomics.

## Explicitly out of scope

- inventory BOM/ingredient depletion;
- arbitrary ecommerce SKU matrix;
- modifier-level tax/fiscal rules;
- automated recipe costing;
- separately fulfilled add-on as a modifier when it is actually another sellable Product;
- retroactive mutation of confirmed item customization.

## Domain distinction

### Product

The menu identity and default sellable item defined by existing Catalog.

Examples:
- Caipirinha;
- Hambúrguer;
- Pizza Margherita.

### ProductVariant

A **single base choice** that materially changes the sellable form before modifiers and may have its own price delta/availability.

Examples:
- Hambúrguer: normal / duplo;
- Pizza: pequena / média / grande;
- Chopp: 300 ml / 500 ml.

Use variants when exactly one base form must be chosen.

Do not create variants for every combination of toppings/removals.

Conceptual fields:
- id;
- product_id;
- name;
- active;
- price_delta_cents or explicit effective price policy;
- sort_order;
- is_default;
- operational availability;
- version.

If a Product has no variants, its current Product price is the base price.

### ModifierGroup

Reusable or product-scoped structured choice:
- id;
- venue_id;
- name;
- selection_mode: SINGLE | MULTI;
- min_selections;
- max_selections;
- required derived from min > 0;
- sort_order;
- allow_duplicates=false by default.

Examples:
- Ponto da carne;
- Adicionais;
- Remover;
- Sabores;
- Molho.

### ModifierOption

Choice inside a group:
- id;
- group_id;
- name;
- price_delta_cents;
- active;
- operational availability;
- default_selected;
- semantic_kind optional: ADD | REMOVE | CHOICE;
- sort_order.

“Sem cebola” should normally be a zero-price REMOVE option, not a negative-price hack.

### ProductModifierGroup

Associates a group with a Product and may override display/order/min/max only when needed.

Avoid copying a group just to change ordering on one Product.

## Variant vs modifier rule

Use **variant** when the customer chooses the base sellable form and exactly one choice defines the starting price/form.

Use **modifier** when the choice customizes that base form.

Examples:
- Chopp size 300/500 ml: variant.
- Pizza size P/M/G: variant.
- Pizza flavor: modifier group, because multi-flavor rules may allow 1–N choices.
- “Sem cebola”: modifier.
- Bacon extra: modifier.
- Drink ice/no ice: modifier.

If two choices must route/fulfill as separate products, create linked OrderItems rather than hiding that production work inside a modifier.

## Invariants

1. Confirmed OrderItem stores an immutable snapshot of Product, selected variant, modifier selections, labels and exact cents.
2. Catalog edits never reprice/relabel a confirmed OrderItem.
3. ProductAvailability UNAVAILABLE blocks every variant/option from new confirmation.
4. A variant/option marked operationally unavailable cannot be newly confirmed even when the UI is stale.
5. Modifier min/max constraints are validated server-side.
6. SINGLE groups allow at most one selection.
7. A default selection is convenience only; confirmation still validates availability and cardinality.
8. Sum of base/variant/modifier cents uses integer arithmetic.
9. Structured modifier exists => staff/guest should use it rather than encode the same request in notes.
10. Notes remain allowed for exceptional, non-priced requests and never override validation or price.
11. Modifier availability changes do not mutate already confirmed items.
12. Fulfillment routing stays owned by Product/OrderItem. A modifier may add preparation text but cannot silently create cross-station work.

## Pricing model

Effective unit price at confirmation:

effective_unit_price_cents =
  product_base_price_cents
  + selected_variant_price_delta_cents
  + sum(selected_modifier_option_price_delta_cents)

All values are integer cents.

Quantity multiplies after unit customization price is resolved unless a future pricing spec explicitly defines otherwise.

Zero-price options are valid and common.

Negative modifier price is disallowed in P0; discounts belong to Spec 011.

## Availability

### Product
Existing ProductAvailability remains top-level gate.

### Variant availability
Variant has operational state AVAILABLE | UNAVAILABLE when variants exist.

### Modifier option availability
ModifierOption has operational state AVAILABLE | UNAVAILABLE.

Operational state is distinct from administrative active/publication, matching ADR 0005.

Authorized station staff may change availability for variants/options whose parent Product routes to their station; MANAGER can manage all.

Every change records actor/time/old/new/reason optional and propagates to all surfaces.

## Confirmation flow

Cart configuration is mutable client state until Order confirmation.

At confirmation, backend:
1. loads Product and operational availability;
2. validates chosen variant belongs to Product and is active/available;
3. validates each group belongs to Product;
4. validates selected options belong to group and are active/available;
5. validates min/max/single/multi;
6. computes cents server-side;
7. persists immutable OrderItemCustomizationSnapshot;
8. creates Charge from the computed snapshot exactly once.

Client-submitted price is never authoritative.

## Snapshot

Conceptual OrderItem snapshot includes:
- product_id + product_name_snapshot;
- base_price_cents_snapshot;
- variant_id nullable;
- variant_name_snapshot;
- variant_delta_cents_snapshot;
- modifier selections:
  - group_id/name;
  - option_id/name;
  - price_delta_cents;
  - semantic_kind;
- unit_price_cents;
- quantity;
- exceptional_note optional;
- routing snapshot required by existing Ordering/Fulfillment.

## Order editing rules

Before confirmation:
- freely change variant/modifiers;
- stale availability may be discovered at submit.

After confirmation:
- do not mutate snapshot in place;
- customer/staff change goes through Spec 017 cancellation/correction/replacement semantics;
- if only a production note can still be safely added, that must be an explicit audited exception defined by Spec 017, not silent snapshot mutation.

## Production semantics

Bar/Kitchen display:
- Product name first;
- variant immediately after product when selected;
- modifiers grouped, concise and ordered;
- removals visually clear (“SEM cebola”);
- exceptional note separated from structured choices.

Example:

Hambúrguer · Duplo
+ bacon
SEM cebola
Molho: barbecue
Obs.: cortar ao meio

Production state remains on OrderItem.

## Guest ordering

- required choices block Add/Confirm until satisfied;
- zero-price choices still show selection state;
- unavailable options remain visible when useful but disabled and labeled;
- price delta is visible before selection/confirmation;
- defaults may be preselected but never hidden;
- notes are secondary under “Pedido especial” or equivalent.

## Quick staff ordering ergonomics

- products with no required choice can quick-add in one tap;
- if all required choices have one valid default, quick-add may use defaults and expose undo/edit immediately;
- otherwise tap opens compact modifier sheet;
- staff should not traverse optional groups unless needed;
- previous configuration may be repeatable only after revalidating current availability.

## API / commands / queries

Queries:
- product_ordering_schema(product_id);
- catalog with variant/option availability;
- modifier group management queries.

Commands:
- configure_product_variants(...);
- configure_modifier_group(...);
- attach_modifier_group(...);
- set_variant_availability(...);
- set_modifier_option_availability(...);
- confirm_order(... selections ...).

Ordering API returns normalized errors:
- VARIANT_REQUIRED;
- VARIANT_UNAVAILABLE;
- MODIFIER_REQUIRED;
- TOO_MANY_MODIFIERS;
- MODIFIER_UNAVAILABLE;
- INVALID_MODIFIER_SELECTION;
- CATALOG_VERSION_STALE where useful.

## Permissions

- STAFF/CASHIER/GUEST: select allowed customization;
- station staff: operational availability for parent station if granted;
- MANAGER: configure variants/groups/options and all operational availability;
- OWNER: same plus venue catalog policy.

Guest never configures catalog.

## Realtime behavior

Variant/option availability changes invalidate:
- Atendimento catalog;
- Bar/Kitchen catalog;
- Guest menu;
- carts containing affected choice show stale status.

Confirmation remains final authority even if realtime is delayed.

## Concurrency / idempotency

- availability mutation uses version/optimistic concurrency;
- confirmed Order idempotency covers full customization payload;
- repeated confirm with same idempotency key creates no duplicate OrderItem/Charge;
- catalog edits concurrent with confirmation resolve by transactional validation of current active/availability state.

## Error/degraded behavior

Offline/degraded ordering follows Spec 014.

For queued safe orders, the server must revalidate Product, variant and modifier availability at replay. A rejected stale customization returns exact affected choices; it is never silently substituted.

## Audit requirements

Audit:
- variant/group/option create/edit/archive;
- availability changes;
- manager configuration changes;
- exceptional post-confirm correction via Spec 017.

Ordinary customer/staff selection of modifiers is persisted in OrderItem snapshot, not duplicated as noisy AuditEvents.

## Metrics/events

Facts:
- order_item.confirmed includes variant/modifier snapshots;
- catalog.variant_availability_changed;
- catalog.modifier_availability_changed.

Metrics may include:
- selection mix;
- modifier attach rate;
- option unavailable time;
- cancellation/remake relation to customization errors via Spec 017.

Avoid inferring inventory usage from modifier counts unless inventory spec exists.

## Security/privacy

- server validates IDs belong to same Venue/Product/group;
- price computed server-side;
- notes are length-limited and treated as untrusted text;
- no HTML execution in production displays;
- guest sees only published ordering schema.

## Migration / backward compatibility

Existing Product without variants/groups remains valid and behaves exactly as today.

Existing OrderItems require no rewrite. New snapshot fields are nullable/empty for historical items.

## Depends on

- Spec 001 Catalog/Ordering/price snapshot.
- Spec 004 Guest Ordering.
- Spec 005 Catalog identity/quick create.
- Spec 008 permissions.

## Enables

- Spec 017 modifier-specific corrections/remakes;
- richer guest ordering;
- future inventory/costing integration without making it a dependency.

## Deliberately deferred

- ingredient-level stock;
- combinatorial SKU matrix;
- negative-priced modifier discounts;
- modifier-specific tax;
- automatic cross-station child item generation.

## Implementation contract

### Independent selection-mix read contract

Availability changes publish the existing catalog fact names through the existing
transactional realtime outbox, once per affected Product (`aggregate_type=Product`).
This reuses guest/staff Catalog routing and never exposes operator or note data.
Polling remains the native fallback; no shared delivery infrastructure is changed.

`ordering.customization_mix.selection_mix(venue_id, start, end)` reads confirmed
OrderItem snapshots in the explicit timezone-aware interval [start, end). It groups
Product/variant and Product/group/option identities with their original labels and
cents; quantities weight counts. Archived/deleted catalog choices remain readable.
It returns gross confirmed selection facts, including cancelled originals, with
cancelled units separately identified. Operational remake/replacement children are
excluded to avoid counting the same sale again. Legacy empty snapshots contribute
to simple Product units. Modifier attach-rate inputs are selected units and total
Product units, not a guessed percentage or inventory consumption. Price/delta
totals are snapshot facts, never net revenue, ledger balances or financial reports.
Management owns business-date/cutoff conversion, authorization, endpoint and UI
integration. This isolated internal read service adds no migrations or mutations.

Variants store an explicit nonnegative `price_cents`, replacing the Product base price. Snapshots also record the difference from the Product price. Confirmation accepts additive `variant_id`, `modifier_option_ids` and `special_instructions` (500 characters); no submitted price is authoritative. Products with active variants require an explicit selected ID; defaults are visibly selected by clients. Groups are reusable within a Venue; association sets display priority, with cardinality owned by the group. Archival uses active=false and historical snapshots contain IDs as plain values, never mutable joins. Configuration and confirmation lock Products before child rows; reusable group edits lock all attached Products in ID order. Availability commands require expected_version and audit old/new state and reason. Polling existing catalogs supplies invalidation without adding SSE infrastructure.

### T08a / UX-13 — repetir rodada no Android
A ação por pedido confirmado prepara uma revisão local na mesma Tab aberta.
Copia somente unidades restantes de linhas não canceladas; exclusões são informadas.
Identidades de Product, variante e opções vêm do payload/snapshot, nunca dos nomes.
Ausência de snapshot estruturado bloqueia a rodada, inclusive legado vazio.
Preço, nome e texto da configuração históricos são comparados com o catálogo atual
na revisão. Produto inativo/ausente/indisponível, seleção inválida, quantidade ou
valor fora do contrato bloqueiam toda a inclusão; não substituir por defaults.
Adicionar ao carrinho exige confirmação explícita e revalidação do mesmo conteúdo
revisado; alteração de catálogo/histórico exige nova revisão. Preserva draft existente,
com linhas novas separadas por configuração, e bloqueia busy, leitura em andamento,
catálogo não online e intenção de pedido pendente. Não recebe nem envia automaticamente.
Confirmar pedido usa o fluxo autorizado e a nova chave da intenção existente; repetir
não reutiliza IDs/chaves históricos nem altera snapshots, Payments ou ledger.
A API revalida catálogo/limite/permissão na confirmação. Fora de escopo: Web,
repetir entre Tabs, substituir itens bloqueados e afirmar ergonomia em aparelho físico.

### T08b / UX-13 — repetir rodada no Atendimento Web
No histórico da Tab aberta, Repetir rodada lê detalhe autorizado e catálogo atuais
antes da revisão. Somente unidades restantes de linhas não canceladas são copiadas;
exclusões são informadas. IDs de Product/variante/opções vêm do snapshot canônico,
nunca de nomes. Legado sem snapshot completo, produto ausente/inativo/indisponível,
seleção removida/inválida e quantidade fora de 1–99 bloqueiam a inclusão inteira.
A revisão mostra preços e configuração anteriores/atuais e destaca diferenças.
Adicionar ao carrinho é explícito, preserva o draft da Tab e não envia pedido.
Conteúdo alterado durante revisão exige reabrir a revisão. Busy, leitura, fechamento,
correção, recebimento ou intenção pendente bloqueiam repetição/navegação no contexto.
Falha de leitura preserva draft e histórico. Confirmar pedido usa a recuperação
existente e cria nova chave, sem reutilizar a intenção histórica. A API revalida
catálogo/limite/autorização e preserva snapshots/ledger/Payments. Repetir só atende
à mesma Tab; Web POS e guest, persistência de drafts e ganhos humanos ficam fora.

### T08c / UX-13 — repetir rodada guest
Repetir rodada por pedido histórico lê contexto e catálogo autorizados com o token
já ativo. Não resolve QR, cria sessão/comanda ou troca destino para repetir.
Venue/session/table/occupancy/generation e Tab devem coincidir com o contexto e
token originais; exigir ocupação ativa, Tab aberta, leitura saudável, ausência de
limite/bloqueio emergencial e de envio/recuperação/configuração em andamento.
Reutilizar revisão de T08b com IDs, configuração e centavos anteriores/atuais,
exclusões explícitas e inclusão inteira bloqueada por item inválido/legado.
Catálogo guest fornece só Products ativos: ausência bloqueia; available é a fonte
operacional. Não inferir produto por nome nem substituir seleção por defaults.
Adicionar ao carrinho relê contexto/catálogo da mesma visita; mudança de conteúdo
exige nova revisão, bloqueio/revogação/falha preservam draft e não enviam pedido.
Inclusão única preserva draft/configurações distintos; Enviar é ação separada com
nova intenção e recuperação T05b. API revalida política/disponibilidade/limite.
Nenhum snapshot, Payment ou ledger histórico é alterado. Sem reserva entre GETs
e envio, persistência de drafts, novo pagamento, Web POS ou ganho humano medido.

### T08d / UX-13 — repetição no PDV Web
O PDV reutiliza a revisão canônica de rodada implementada no Atendimento Web.
Histórico permanece imutável: copiar IDs/configuração/quantidades para um novo
rascunho com preço e disponibilidade atuais, diferenças explícitas e bloqueio
integral se houver configuração inválida ou legado não verificável. Cancelar
preserva o rascunho; incluir é único e não confirma pedido. Mesma Tab aberta,
dados atuais e ausência de operação pendente são obrigatórios. Pendências de
pedido, recebimento ou correção bloqueiam repetição; revisão bloqueia recebimento
e troca de Tab. Confirmação explícita cria nova intenção pelo fluxo existente;
resposta perdida reutiliza payload/chave originais. Não alterar Payments, ledger
ou snapshots confirmados. Testar mobile, mudança de catálogo, replay e histórico
em PostgreSQL descartável. Não ampliar catálogo, pagamentos ou navegação.

### T09a / UX-14 — quantidade no rascunho guest
Toques repetidos e inclusão de rodada agrupam somente Product ID, variant ID,
conjunto de option IDs e observação exatamente iguais. A ordem dos IDs de opções
não muda a configuração; a nota não é normalizada. Edição preserva quantidade e
reagrupa somente a configuração idêntica. Limite por linha agrupada: 1–99;
excedê-lo rejeita toda a inclusão/edição, preserva o draft e informa o problema,
sem truncar, descartar unidades ou confirmar automaticamente.
Controles +/− acessíveis ajustam quantidade; zero remove a linha. Aumento exige
catálogo atual/disponível, configuração válida e visita aberta sem bloqueio de
mesa/Venue/consumo. Diminuição/remoção permitem corrigir item indisponível ou
rascunho obsoleto, mas ficam bloqueadas durante intenção pendente/envio/revisão.
Nenhum controle altera o payload pendente: replay usa a intenção original T05b.
API segue revalidando catálogo, autorização e limite no envio. Histórico,
Payments e ledger não são editados. Fora de escopo: busca/categorias de T09b,
criação automática de comanda, persistência de draft e ganhos humanos medidos.

### T09b / UX-15 — descoberta no catálogo guest
API guest projeta Product.category já persistida, sem inferir categorias pelo
routing nem alterar catálogo/domínio. UI reutiliza a apresentação de categorias
do Atendimento; ausência de categoria pertence a Outros. Todos inicia selecionado,
para preservar descoberta de qualquer produto. Categoria filtra por apresentação;
busca por nome ignora acentos/caixa e espaços nas bordas, pesquisando o catálogo
inteiro. Limpar busca volta à categoria selecionada; selecionar categoria limpa
busca. Categoria removida após atualização retorna a Todos. Resultado vazio tem
feedback e contagem acessível; filtros não mudam Product IDs, configurações,
quantidades, draft, histórico ou intenções pendentes.
Acesso explícito ao Pedido atual no catálogo leva ao draft existente sem enviar,
criando comanda nem resolver QR novamente. Nenhum item se torna vendável pela
busca: indisponibilidade, dados obsoletos, bloqueios de mesa/Venue/consumo, visita
revogada e intenção pendente conservam os guards T05b/T09a. Catálogo vazio tem
mensagem própria. Fora de escopo: recomendação/fuzzy matching, categorias novas
no banco, criação automática da comanda, persistência de draft e medição humana.

Descoberta T09b: Pedido atual permanece visível, desativado com carrinho vazio,
para que a primeira inclusão não desloque os produtos durante toques repetidos.


### Spec 026 T10b — resumo por configuração confirmada
O resumo de produção agrupa apenas Product com snapshot operacional equivalente
na mesma estação. Renderiza variação, modificadores e observação do snapshot,
sem reconstruir pelo catálogo atual. Identidade inclui IDs e nomes/semântica
confirmados, observação exata e campos operacionais adicionais. Ordem dos
modificadores e campos JSON não diferencia preparo; preço, quantidade e total
não são configuração operacional. Estados NEW/ACCEPTED/PREPARING podem aparecer
no mesmo resumo com contagens separadas: o resumo não é seleção nem lote.
Ausência/incompletude de snapshot ou identidade/routing divergentes conserva
linha independente e aviso Configuração não registrada; nunca inferir padrão
pelo catálogo. Item sem Product ID permanece independente. Não alterar snapshots,
Payments, ledger, auditoria, estado nem permissões.

Contrato para lote futuro (pendente): seleção explícita de linhas inteiras com
mesmo produto/configuração/estação e estados de origem compatíveis; revisão do escopo/quantidade
e destino PREPARING ou READY, sempre autoria humana. Comando canônico deve
registrar chave e fingerprint imutável, autorizar todas as linhas no Venue,
validar estado/snapshot/quantidade restante sob locks em ordem determinística,
responder resultado por linha e replay do resultado. Conflito em qualquer linha
rejeita integralmente sem efeito parcial. READY deriva Dispatch por linha na
mesma transação. Não usar fan-out de transições individuais: o endpoint atual
não oferece replay idempotente nem precondições suficientes. Indisponibilidade
posterior do catálogo não cancela preparo confirmado. Nenhum botão/lote, comando
novo ou concorrência independente é implementado em T10b.


### Spec026 T10c.1 — comando canônico de produção
POST /production/batches/ exige order.confirm, sessão ativa e Venue autorizado.
Payload: idempotency_key (até 120), station BAR/KITCHEN, target_state PREPARING/READY,
e lines (1–50 IDs distintos) com item_id, expected_state, quantity restante positiva
e snapshot_fingerprint SHA256 retornado na fila. Linhas inteiras do mesmo produto,
configuração confirmada e estação. NEW/ACCEPTED são origens compatíveis para
PREPARING; READY exige PREPARING em todas. O estado esperado de cada linha é exato.
Legado incompleto não admite lote; permanece operável individualmente.
Locks: sessão original, Tabs por ID, OrderItems por ID. Validar tudo antes de
aplicar. Resposta APPLIED ou REJECTED contém ID do comando e resultado de cada
linha; rejeição persistida não aplica nenhuma. Repetir chave/payload na mesma
sessão devolve recibo original, mesmo após mudança de estado; payload diferente
retorna IDEMPOTENCY_CONFLICT. Outra sessão não adota comando antigo.
Auditoria associa comando e transições ao ator. READY deriva Dispatch na mesma
transação; falha inesperada reverte comando, transições, auditoria e Dispatch.
Preço/disponibilidade atuais não substituem snapshots; ledger e Payments intactos.
T10c.1 entrega API, não seleção/revisão Web nem recuperação de intenção no browser.
T10c.2 deve persistir chave/payload vinculados à sessão antes do envio, revisar
seleção explícita, recuperar resposta perdida e validar mobile 360/390/430.


### T10c.2 — revisão e recuperação Web do lote
Resumo verificável oferece Selecionar preparo / Selecionar prontos por grupo.
Dialog exige seleção humana (inicialmente vazia), linhas inteiras, até 50, e
exibe estação, configuração confirmada, destinos, estados e total de unidades.
Revisão não altera domínio. Confirmar exige snapshot atual compatível; mudança
de estado/quantidade/fingerprint exige nova revisão, sem substituir seleção.
Persistir envelope estrito em sessionStorage antes do POST, com chave/payload
originais e vínculo Venue/staff/session. Nenhuma credencial ou nome de cliente
é persistido. Falha de armazenamento impede envio; resposta perdida/5xx/recibo
inconsistente preserva pendência. Verificar mesmo lote repete payload/chave;
nunca monta lote novo. Sessão diferente bloqueia adoção. Estação diferente
orienta retorno à original. Recibo terminal válido exige leitura atual da fila
antes de remover intenção. Rejeição integral libera nova revisão após leitura.
Resultado discrimina cada linha, sem afirmar sucesso parcial. Durante revisão,
envio ou pendência, bloquear mutations da produção; navegação permanece disponível.
Usar ActionDialog, tokens existentes, foco/44px e estados acessíveis. Legado
sem fingerprint/configuração não oferece lote. UX23 de ações independentes
permanece fora desta slice; não afirmar medição humana, aparelho ou publicação.


### T10d.1 — ações individuais verificáveis independentes
Item com configuração confirmada e fingerprint usa o comando canônico de produção
com uma linha, conservando seleção humana por Iniciar preparo/Pronto. Intenção
individual persistida antes do POST, por item e sessão; múltiplos itens distintos
podem aguardar resposta sem bloquear uns aos outros. Mesmo item não aceita outro
comando enquanto houver envio/pendência. Repetição usa payload/chave originais.
Ler/validar todas as intenções ao montar a tela, inclusive itens ausentes da fila
ou já READY; recuperação não depende de o botão original continuar renderizado.
Não adotar sessão/Venue/ator diferentes; dados inválidos/storage falho bloqueiam
novos envios. Recibo por linha e leitura atual exigidos antes de remover intenção.
Rejeição afeta somente aquela linha; nunca inferir sucesso parcial. Leitura
pós-comando é serializada; eventos recebidos durante ela são relidos depois.
Enquanto houver intenção individual, lote/legado/disponibilidade/QuickCatalog
seguem bloqueados. Revisão ou pendência de lote bloqueia todos os itens. Fila
indisponível/sessão revogada bloqueia globalmente. Não alterar finanças, snapshots,
autorização, inferir preparo ou tornar disponibilidade concorrente nesta slice.
UX23 permanece parcial até investigar os demais escopos em T10d.2.

### T10d.2 — item independente de lote pendente
Após persistir lote, somente seus IDs ficam bloqueados para ações individuais
verificáveis. Outro item pode usar seu comando canônico independente, conservando
journal próprio e readback serializado. Antes de persistir lote e durante revisão,
bloqueio global permanece. Lote inválido/adulterado ou pertencente a outra sessão
impede novo envio individual. Não liberar novo lote enquanto houver pendência,
nem legado/disponibilidade/QuickCatalog; não mudar snapshots, autorização ou finanças.
Replay original do lote convive com intenção individual disjunta. Testar resposta
perdida, sessão/storage, conflitos e mobile Web/API PostgreSQL.
