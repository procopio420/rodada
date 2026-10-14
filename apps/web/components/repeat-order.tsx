"use client";

import { ActionDialog } from "@/components/action-dialog";
import { CustomizationText, money, selectionError, unitPrice, type OrderingProduct, type Selection, type Snapshot } from "@/components/product-customization";

export type RepeatProduct = OrderingProduct & { active: boolean; availability: string };
export type HistoricalOrder = { id: string; items: { id: string; product_id?: string; product_name: string; quantity: number; unit_price_cents?: number; state: string; customization_snapshot?: Snapshot }[] };
export function currentSnapshot(product: OrderingProduct, selection: Selection): Snapshot {
  return { variant: product.variants?.find(v => v.id === selection.variant_id) ?? null,
    modifiers: (product.modifier_groups ?? []).flatMap(g => g.options.filter(o => selection.modifier_option_ids.includes(o.id)).map(o => ({ ...o, group_name: g.name }))), special_instructions: selection.special_instructions };
}
function description(snapshot: Snapshot): string {
  return JSON.stringify([snapshot.variant?.name ?? null, snapshot.modifiers?.map(o => [o.name, o.group_name, o.semantic_kind]) ?? [], snapshot.special_instructions ?? ""]);
}
export function reviewRepeatedOrder<P extends RepeatProduct>(order: HistoricalOrder, products: P[]) {
  const lines: { original: HistoricalOrder["items"][number]; product: P; quantity: number; selection: Selection; changed: boolean }[] = [];
  const problems: string[] = [];
  let excluded = 0;
  for (const item of order.items) {
    if (item.state === "CANCELLED" || item.quantity === 0) { excluded++; continue; }
    const product = products.find(p => p.id === item.product_id);
    const snapshot = item.customization_snapshot;
    const verifiable = snapshot && (snapshot.variant === null || (typeof snapshot.variant?.id === "string" && !!snapshot.variant.id)) &&
      Array.isArray(snapshot.modifiers) && snapshot.modifiers.every(o => typeof o.option_id === "string" && !!o.option_id) && typeof snapshot.special_instructions === "string";
    const selection: Selection = { variant_id: snapshot?.variant?.id ?? null, modifier_option_ids: snapshot?.modifiers?.map(o => o.option_id ?? "") ?? [], special_instructions: snapshot?.special_instructions ?? "" };
    const problem = !product ? "Produto ausente do catálogo atual." : !product.active || product.availability !== "AVAILABLE" ? "Produto inativo ou indisponível." :
      !verifiable || !Number.isSafeInteger(item.unit_price_cents) ? "Histórico sem configuração ou preço verificável. Escolha o item no catálogo." :
      !Number.isInteger(item.quantity) || item.quantity < 1 || item.quantity > 99 ? "Quantidade fora do limite de 1 a 99." :
      selection.variant_id && !product.variants?.some(v => v.id === selection.variant_id) ? "Variação removida." :
      new Set(selection.modifier_option_ids).size !== selection.modifier_option_ids.length || selection.special_instructions.length > 500 ? "Configuração inválida." :
      selectionError(product, selection) || ((product.modifier_groups ?? []).some(g => !g.active || (g.selection_mode === "SINGLE" && g.options.filter(o => selection.modifier_option_ids.includes(o.id)).length > 1)) ? "Configuração alterada. Revise no catálogo." : "") ||
      (!Number.isSafeInteger(unitPrice(product, selection)) || unitPrice(product, selection) < 0 || unitPrice(product, selection) * item.quantity > 2147483647 ? "Valor fora do limite." : "");
    if (problem || !product || !snapshot) problems.push(`${item.product_name}: ${problem}`);
    else lines.push({ original: item, product, quantity: item.quantity, selection,
      changed: item.product_name !== product.name || item.unit_price_cents !== unitPrice(product, selection) || description(snapshot) !== description(currentSnapshot(product, selection)) });
  }
  return { lines, problems, excluded, canAdd: lines.length > 0 && !problems.length };
}
export function RepeatOrderDialog({ review, enabled, busy = false, message, onAdd, onClose }: { review: ReturnType<typeof reviewRepeatedOrder>; enabled: boolean; busy?: boolean; message?: string; onAdd: () => void; onClose: () => void }) {
  return <ActionDialog title="Conferir rodada" onClose={onClose} locked={busy}>
    <p>Adicionar ao carrinho não envia o pedido. Confira os valores e a configuração atuais.</p>
    {(message || !enabled) && <p role="alert" className="notice" data-state="warning">{message || "O contexto mudou ou está ocupado. Feche e revise novamente."}</p>}
    {!!review.excluded && <p>{review.excluded} linha(s) canceladas ou sem unidades restantes não serão repetidas.</p>}
    {review.problems.map((problem, index) => <p key={index} className="notice" data-state="danger">{problem}</p>)}
    {!review.lines.length && !review.problems.length && <p>Nenhum item para repetir.</p>}
    {review.lines.map(line => <section key={line.original.id} className="panel">
      <h3>{line.quantity}× {line.product.name}</h3>
      <p>Anterior: {line.original.product_name} · {money(line.original.unit_price_cents!)} por unidade</p>
      <CustomizationText snapshot={line.original.customization_snapshot} />
      <p>Atual: {money(unitPrice(line.product, line.selection))} por unidade</p>
      <CustomizationText snapshot={currentSnapshot(line.product, line.selection)} />
      {line.changed && <p className="notice" data-state="warning">Preço ou descrição mudou. Confira os valores atuais.</p>}
    </section>)}
    <p>Total a adicionar: {money(review.lines.reduce((sum, line) => sum + unitPrice(line.product, line.selection) * line.quantity, 0))}</p>
    <button className="buttonPrimary" disabled={!enabled || !review.canAdd} onClick={onAdd}>Adicionar ao carrinho</button>
  </ActionDialog>;
}
