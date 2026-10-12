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
Attendance prioritizes catalog, draft order and confirmed items before the bill at the end of the selected Tab. Show canonical net Subtotal followed by a keyboard/touch disclosure Mais detalhes containing original subtotal and the unchanged financial breakdown. Cash/POS retains its full summary. Category navigation shows one category at a time, counts and global accent-insensitive name search; search spans categories without discarding cart/customization. Use published Product.category; an exact photographed-menu presentation mapping splits Bebidas and groups portions/cold board as Petiscos. Unknown items retain their published category or Outros; no fuzzy inference. Unavailable published products remain visible but disabled; inactive products are omitted in Attendance. Preserve prices, IDs, routes, monetary math, immutable orders and retry behavior. No API/database change or menu price transcription.

## Attendance removal and compact refinement
NEW/ACCEPTED confirmed items offer Remover using Spec 017 canonical correction with explicit wrong-entry/customer-change reason and confirmation. Preserve cancelled history; no direct deletion or payment/refund routes. Pending/ambiguous cancellation freezes the same payload/key, locks switching and supports same-action retry. A paid request (202) is a manager/refund requirement, never removal success; later production/permission conflicts show server feedback and refresh. Collapsing the selected catalog category hides search/list while retaining category navigation and cart; another category reopens it. Attendance selected Tab name is centered without a cart icon. Compact Subtotal uses server payable_cents (after discounts/courtesies/corrections/service, before payments); original subtotal is inside Mais detalhes. Missing canonical total is explicit, not inferred. Cash/POS unchanged.

Confirmed-item removal uses a native modal dialog with a labelled title, trapped focus and focus restoration. Escape closes only before submission or after a resolved rejection; pending, ambiguous or applied-but-unrefreshed corrections cannot be dismissed. Existing cancellation rules remain unchanged. Dialog uses existing surface, border, spacing and radius tokens; backdrop uses the background token.

## Attendance action dialogs
Existing table location/Tab association fields move behind Organizar mesa. Release requires a labelled dialog explaining QR revocation and open Tabs. Occupy/clean/deliver remain direct quick actions. Product customization in Attendance opens a modal; POS remains inline. Close Tab requires confirmation in Attendance, retaining balance restrictions. Errors remain persistent alerts, successful orders use nonblocking status. No new transfer endpoint or domain behavior. Dialogs preserve keyboard focus, Escape and pending-action locks.
