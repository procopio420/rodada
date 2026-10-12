# Spec 025 — Coesão do piloto e equipe de desenvolvimento

## Comportamento
Gerência usa as cinco seções já especificadas, mas mostra uma seção por vez.
Agora conserva exceções financeiras, alertas e resumo atual; detalhes secundários
ficam em disclosures “Ver mais”. Operação, Vendas, Gestão e Mais oferecem ações
diretas para as telas existentes. Hash, voltar/avançar e acesso direto preservam
a seleção. Formulários de clientes/ícones saem da home e ficam em páginas próprias.
Páginas adjacentes sempre permitem voltar à Gerência.

`/dev/staff` administra equipe do Venue da sessão: lista (incluindo removidos),
criação com nome/login/PIN/função, edição de função/situação e remoção de acesso.
Só funciona quando RODADA_DEVELOPER_TOOLS está explicitamente habilitado no servidor
Web e API. A API exige staff.manage e PIN recente para mutations. Não cria papel
DEV nem bypass global. Remover revoga o vínculo/sessões; identidade e auditoria
persistem. Não permitir remover a própria sessão nem o último OWNER ativo.
Criar usa chave idempotente, login normalizado/único e PIN hash; nunca retorna ou
audita PIN. Resposta perdida conserva chave e payload até retry/consulta; conflitos
reconsultam a versão atual. Segredos não vão para URL ou armazenamento do navegador.

## Limpeza local solicitada
Apenas banco rodada_demo em localhost, após backup verificável, com manifest de
IDs anterior à execução. Encerrar todas as comandas abertas de teste com ajuste
explícito LOCAL_TEST_RESET (não pagamento), cancelar filas/itens antigos com motivo
auditado e revogar acessos guest antigos. Preservar lançamentos, snapshots de
pedidos, pagamentos e auditoria; liberar ocupações pelo ciclo canônico. Retirar
produtos QA da venda; padronizar unidades/grafia de Products sem alterar preço,
marca/receita ou snapshots confirmados. Histórico fechado fica sob “Ver histórico”
no PDV. A limpeza não é um endpoint remoto nem botão de produção. O seed do
cardápio fotografado reconhece somente os nomes antigos exatos com unidade sem
espaço (600ml/2L), preservando identidade, preço e nome já editados. Se coexistirem
as duas grafias, exigir revisão sem mesclar. Importação CSV genérica não usa aliases.

## Fora de escopo
Providers, maquininhas/impressoras físicas, ERP, novas métricas, alteração de
receitas, preços homologados, exclusão física de staff com fatos históricos,
reset de contas/PIN existentes, exposição pública de ferramentas DEV.

## Aceite
Ver acceptance.md. Este recorte não declara homologação de produção.

## Attendance catalog and bill hierarchy
Attendance presents the draft order first, then confirmed items and catalog, followed by the compact bill summary immediately above closing. Pedido atual uses the shared full-width operational heading, icon and typography; its item count stays readable. Closing remains the final action. Show canonical net Subtotal followed by a keyboard/touch disclosure Mais detalhes containing original subtotal and the unchanged financial breakdown. Cash/POS retains its full summary. Category navigation shows one category at a time, counts and global accent-insensitive name search; search spans categories without discarding cart/customization. Use published Product.category; an exact photographed-menu presentation mapping splits Bebidas and groups portions/cold board as Petiscos. Unknown items retain their published category or Outros; no fuzzy inference. Unavailable published products remain visible but disabled; inactive products are omitted in Attendance. Preserve prices, IDs, routes, monetary math, immutable orders and retry behavior. No API/database change or menu price transcription.

## Attendance removal and compact refinement

Catalog follow-up: replace the Outros navigation tab with Todos (last tab), which shows all active products grouped by existing category order and then Portuguese product name. Uncategorized products remain discoverable in Todos without a separate Outros tab. Brahma 600 ml (including the legacy exact name Brahma 600ml) belongs to Cervejas in Attendance regardless of a missing category. Todos supports the existing repeated-tap collapse, global search, availability checks and draft preservation. No product identity, price or database mutation.
NEW/ACCEPTED confirmed items offer Remover using Spec 017 canonical correction with explicit wrong-entry/customer-change reason and confirmation. Preserve cancelled history; no direct deletion or payment/refund routes. Pending/ambiguous cancellation freezes the same payload/key, locks switching and supports same-action retry. A paid request (202) is a manager/refund requirement, never removal success; later production/permission conflicts show server feedback and refresh. Collapsing the selected catalog category hides the product list while retaining search, category navigation and cart; another category or a nonempty search reveals products. Attendance selected Tab name is centered without a cart icon. Compact Subtotal uses server payable_cents (after discounts/courtesies/corrections/service, before payments); original subtotal is inside Mais detalhes. Missing canonical total is explicit, not inferred. Cash/POS unchanged.

Confirmed-item removal uses a native modal dialog with a labelled title, trapped focus and focus restoration. Escape closes only before submission or after a resolved rejection; pending, ambiguous or applied-but-unrefreshed corrections cannot be dismissed. Existing cancellation rules remain unchanged. Dialog uses existing surface, border, spacing and radius tokens; backdrop uses the background token.

## Attendance action dialogs

Attendance visual refinement: section headings use restrained accent surfaces and existing tokens, confirmed items use clearly separated compact rows with readable name/customization/status, and Fechar comanda uses a bordered accent action consistent with the surface. Eligible item removal uses a minimal danger-colored trash icon, a product-specific accessible label and a 44px touch target; retain the existing dialog and all cancellation/financial/pending-state guards. POS remains unchanged. Validate mobile sizes, removal focus/retry and adjacent surfaces without baseline relaxation.

Catalog search remains visible even when no category is expanded. Typing searches all active products and reveals grouped results without requiring a category selection. Clearing the query restores the prior collapsed state; collapsed categories have no selected highlight. Preserve draft, availability and confirmation locks.
Existing table location/Tab association fields move behind Organizar mesa. Release requires a labelled dialog explaining QR revocation and open Tabs. Occupy/clean/deliver remain direct quick actions. Product customization in Attendance opens a modal; POS remains inline. Close Tab requires confirmation in Attendance, retaining balance restrictions. Errors remain persistent alerts, successful orders use nonblocking status. No new transfer endpoint or domain behavior. Dialogs preserve keyboard focus, Escape and pending-action locks.

Attendance confirmed-item list excludes CANCELLED items after canonical refresh. Historical orders/corrections remain persisted; POS/history and monetary calculations are unchanged.

## Attendance selected Tab and draft controls

Confirmed removal with multiple remaining units asks quantity, initially1, using centered minus/output/plus controls bounded1..remaining units. Freeze quantity/reason/key during submit and ambiguous retry. Applied partial cancellation refreshes canonical remaining units; remove the row only when all remaining units are cancelled. Fechar comanda is the final visible action after the bill/details, keeping existing close restrictions until a separately specified payment navigation flow is implemented.
Repeat tap on the active Tab in the list or its centered heading collapses/reopens its contents without clearing drafts or issuing mutations. Switching to another Tab retains the existing deliberate draft reset. Pending/ambiguous orders and corrections lock collapse/switch. Draft appears directly below the selected Tab heading, before confirmed history and catalog. Each line shows product/customization, line price and 44px minus/plus controls. Minus at one removes only the unconfirmed draft line; plus caps at 99. Repeated identical Attendance selections reuse the same draft line up to the cap; distinct variants/modifiers/instructions remain separate. Confirmation still uses immutable payload/key and canonical API. POS quantity/ordering remains unchanged. Active Tab and selected catalog category use restrained accent-derived surfaces; no arbitrary colors or ornamental dashboard components.

Attendance bill disclosure omits applied pre-fulfillment WRONG_ITEM_ENTERED removals entirely, excluding their signed value from the displayed Correções line without adding a removal row. Hide the Correções row when its remaining value is zero. Keep canonical original subtotal, payable, payments, adjustments and audit unchanged; POS retains its original complete correction aggregate.

Attendance history opens from a discreet right-aligned Histórico button inside the Abrir comanda heading, aligned at its right edge. A separate read-only dialog lists only CLOSED/CANCELLED Tabs and reveals canonical details on request. History must not mix with open Tabs, switch the active Tab, clear drafts or offer operational mutations. Preserve POS history behavior, focus restoration, 44px touch target and pending-order/correction locks.

The history dialog Voltar action uses a full-width bordered secondary button with a restrained accent surface and spacing, clearly distinct from history entries. Preserve close/focus behavior.
