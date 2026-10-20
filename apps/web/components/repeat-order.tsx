"use client";

import { ActionDialog } from "@/components/action-dialog";
import { useState } from "react";
import { CustomizationText, money, selectionError, unitPrice, type OrderingProduct, type Selection, type Snapshot } from "@/components/product-customization";

export type RepeatProduct = OrderingProduct & { active: boolean; availability: string };
export type HistoricalOrder = { id: string; status?: string; confirmed_at?: string | null; items: { id: string; product_id?: string; product_name: string; quantity: number; unit_price_cents?: number; state: string; fulfillment_station_snapshot?: string; customization_snapshot?: Snapshot }[] };
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
export type RepeatQuantities = Record<string, number>;

/** Historical OrderItem IDs are the only selectable identity; omitted IDs mean unchecked. */
export function selectedRepeatedLines<P extends RepeatProduct>(
  review: ReturnType<typeof reviewRepeatedOrder<P>>, quantities: RepeatQuantities,
) {
  if (!review.canAdd || Object.keys(quantities).some(id => !review.lines.some(line => line.original.id === id))) return null;
  const lines = review.lines.filter(line => (quantities[line.original.id] ?? 0) !== 0).map(line => ({
    product: line.product, selection: line.selection, quantity: quantities[line.original.id],
  }));
  if (!lines.length || lines.some(line => !Number.isSafeInteger(line.quantity) || line.quantity < 1 || line.quantity > 99 ||
    unitPrice(line.product, line.selection) < 0 || unitPrice(line.product, line.selection) * line.quantity > 2147483647)) return null;
  return lines;
}

export function RepeatOrderDialog({ review, enabled, busy = false, message, presentation = "legacy", onAdd, onClose }: {
  review: ReturnType<typeof reviewRepeatedOrder>; enabled: boolean; busy?: boolean; message?: string; presentation?: "legacy" | "ux2";
  onAdd: (quantities: RepeatQuantities) => void; onClose: () => void;
}) {
  const [checked, setChecked] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(review.lines.map(line => [line.original.id, true])));
  const [inputs, setInputs] = useState<Record<string, string>>(() =>
    Object.fromEntries(review.lines.map(line => [line.original.id, String(line.quantity)])));
  const quantities = Object.fromEntries(review.lines.filter(line => checked[line.original.id]).map(line => {
    const raw = inputs[line.original.id] ?? "";
    return [line.original.id, /^[1-9][0-9]*$/.test(raw) ? Number(raw) : -1];
  }));
  const selected = selectedRepeatedLines(review, quantities);
  const total = selected?.reduce((sum, line) => sum + unitPrice(line.product, line.selection) * line.quantity, 0) ?? 0;
  const units = selected?.reduce((sum, line) => sum + line.quantity, 0) ?? 0;
  const canEdit = enabled && !busy;
  function adjust(id: string, delta: number) {
    const current = Number(inputs[id]);
    if (Number.isSafeInteger(current) && current + delta >= 1 && current + delta <= 99)
      setInputs(values => ({ ...values, [id]: String(current + delta) }));
  }

  if (presentation === "ux2") return <section className="ux2Workspace" aria-label="Repetir rodada">
    <button className="ux2Back" disabled={busy} onClick={onClose}><span aria-hidden="true">‹</span> Voltar</button>
    <div className="ux2Eyebrow">Repetir com escolha</div><h1>Mais uma rodada.</h1>
    <p className="ux2Lede">Ajuste os itens e quantidades. Um toque confirma a nova rodada.</p>
    {(message || !enabled) && <p role="alert" className="ux2Notice">{message || "O contexto mudou ou está ocupado. Volte e revise novamente."}</p>}
    {!!review.excluded && <p>{review.excluded} linha(s) canceladas ou sem unidades restantes não serão repetidas.</p>}
    {review.problems.map((problem, index) => <p key={index} role="alert" className="ux2Notice">{problem}</p>)}
    {review.lines.map(line => {
      const id = line.original.id, quantity = checked[id] ? Number(inputs[id]) : 0;
      const change = (delta: number) => {
        const next = quantity + delta;
        if (!canEdit || !Number.isSafeInteger(next) || next < 0 || next > 99) return;
        setChecked(values => ({...values, [id]:next > 0}));
        setInputs(values => ({...values,[id]:String(Math.max(1,next))}));
      };
      return <div className="ux2ReviewRow" key={id}><div><strong>{line.product.name}</strong><small>{money(unitPrice(line.product,line.selection))} por unidade</small><CustomizationText snapshot={currentSnapshot(line.product,line.selection)} />{line.changed && <p className="ux2Notice">Preço ou descrição mudou. Anterior: {money(line.original.unit_price_cents!)} por unidade. Confira os valores atuais.</p>}</div>
        <div className="ux2Quantity"><button aria-label={`Reduzir ${line.product.name}`} disabled={!canEdit || quantity === 0} onClick={() => change(-1)}>−</button><output aria-label={`Quantidade de ${line.product.name}`}>{quantity}</output><button aria-label={`Aumentar ${line.product.name}`} disabled={!canEdit || quantity >= 99} onClick={() => change(1)}>+</button></div>
      </div>;
    })}
    {!review.lines.length && <p className="ux2Empty">Nenhum item para repetir.</p>}
    <p className="ux2Notice">Repetir <strong>prepara um novo pedido</strong>; nunca reaproveita a confirmação anterior. Disponibilidade e preços são revalidados.</p>
    <div className="ux2AmountLine"><small>Total da nova rodada · {units} unidade(s)</small><strong>{money(total)}</strong></div>
    <div className="ux2TaskFoot"><button className="ux2Button primary block" disabled={!canEdit || !selected} onClick={() => {if(selected)onAdd(quantities);}}>{busy ? "Enviando rodada…" : "Repetir rodada · enviar"}</button></div>
  </section>;

  return <ActionDialog title="Conferir rodada" onClose={onClose} locked={busy}>
    <p className="muted">Marque os itens e ajuste as quantidades. Ao confirmar, a rodada será enviada diretamente ao bar e à cozinha.</p>
    {(message || !enabled) && <p role="alert" className="notice" data-state="warning">{message || "O contexto mudou ou está ocupado. Feche e revise novamente."}</p>}
    {!!review.excluded && <p>{review.excluded} linha(s) canceladas ou sem unidades restantes não serão repetidas.</p>}
    {review.problems.map((problem, index) => <p key={index} className="notice" data-state="danger">{problem}</p>)}
    {!review.lines.length && !review.problems.length && <p>Nenhum item para repetir.</p>}
    <div className="repeatOrderList">
      {review.lines.map(line => {
        const id = line.original.id;
        const quantity = Number(inputs[id]);
        const picked = checked[id] === true;
        const price = unitPrice(line.product, line.selection);
        return <section key={id} className="repeatOrderLine">
          <label className="repeatOrderChoice">
            <input type="checkbox" checked={picked} disabled={!canEdit}
              onChange={event => setChecked(current => ({ ...current, [id]: event.target.checked }))} />
            <span><strong>{line.product.name}</strong>
              <small className="muted">{money(price)} / un.</small></span>
          </label>
          <CustomizationText snapshot={currentSnapshot(line.product, line.selection)} />
          <div className="repeatOrderQuantity" aria-label={`Quantidade de ${line.product.name}`}>
            <button type="button" className="buttonSecondary" aria-label={`Diminuir quantidade de ${line.product.name}`}
              disabled={!canEdit || !picked || !Number.isInteger(quantity) || quantity <= 1} onClick={() => adjust(id, -1)}>−</button>
            <div className="field">
              <label htmlFor={`repeat-quantity-${id}`}>Qtd.</label>
              <input id={`repeat-quantity-${id}`} type="number" inputMode="numeric" min="1" max="99"
                aria-label={`Quantidade de ${line.product.name}`} value={inputs[id] ?? ""}
                disabled={!canEdit || !picked} onChange={event => {
                  if (/^[0-9]{0,2}$/.test(event.target.value)) setInputs(current => ({ ...current, [id]: event.target.value }));
                }} />
            </div>
            <button type="button" className="buttonSecondary" aria-label={`Aumentar quantidade de ${line.product.name}`}
              disabled={!canEdit || !picked || !Number.isInteger(quantity) || quantity < 1 || quantity >= 99} onClick={() => adjust(id, 1)}>+</button>
          </div>
          {line.changed && <div className="notice" data-state="warning">
            <p>Anterior: {line.original.product_name} · {money(line.original.unit_price_cents!)} por unidade</p>
            <CustomizationText snapshot={line.original.customization_snapshot} />
            <p>Atual: {money(price)} por unidade</p>
            <p>Preço ou descrição mudou. Confira os valores atuais.</p>
          </div>}
        </section>;
      })}
    </div>
    {review.canAdd && !selected && <p role="alert" className="notice" data-state="warning">Selecione pelo menos um item com quantidade entre 1 e 99.</p>}
    <p className="repeatOrderTotal" role="status">{units} unidade(s) · Total da rodada: {money(total)}</p>
    <button className="buttonPrimary" disabled={!canEdit || !selected} onClick={() => { if (selected) onAdd(quantities); }}>{busy ? "Enviando rodada…" : "Confirmar e enviar rodada"}</button>
  </ActionDialog>;
}
