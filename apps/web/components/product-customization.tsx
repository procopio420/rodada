"use client";
import { useEffect, useRef, useState } from "react";

export type Variant = { id: string; name: string; price_cents: number; active: boolean; is_default: boolean; availability: string; version: number; sort_order: number };
export type Option = { id: string; name: string; price_delta_cents: number; active: boolean; availability: string; default_selected: boolean; semantic_kind: string; version: number; sort_order: number };
export type Group = { id: string; name: string; active: boolean; selection_mode: string; min_selections: number; max_selections: number; options: Option[]; version: number; sort_order: number };
export type OrderingProduct = { id: string; name: string; price_cents: number; variants?: Variant[]; modifier_groups?: Group[] };
export type Selection = { variant_id: string | null; modifier_option_ids: string[]; special_instructions: string };
export type Snapshot = { variant?: { name: string } | null; modifiers?: { name: string; group_name: string; semantic_kind: string }[]; special_instructions?: string };
export const money = (cents: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);
export const defaults = (product: OrderingProduct): Selection => ({ variant_id: product.variants?.find(v => v.is_default && v.active && v.availability === "AVAILABLE")?.id ?? null, modifier_option_ids: (product.modifier_groups ?? []).flatMap(g => g.options.filter(o => o.default_selected && o.active && o.availability === "AVAILABLE").slice(0, g.max_selections).map(o => o.id)), special_instructions: "" });
export function selectionError(product: OrderingProduct, selection: Selection): string {
  if (product.variants?.length && !product.variants.some(v => v.id === selection.variant_id && v.active && v.availability === "AVAILABLE")) return "Escolha uma variação disponível.";
  const options = (product.modifier_groups ?? []).flatMap(g => g.options);
  if (selection.modifier_option_ids.some(id => !options.some(o => o.id === id && o.active && o.availability === "AVAILABLE"))) return "Uma opção ficou indisponível. Revise o item.";
  for (const group of product.modifier_groups ?? []) {
    const count = group.options.filter(o => selection.modifier_option_ids.includes(o.id)).length;
    if (count < group.min_selections || count > group.max_selections) return `${group.name}: selecione de ${group.min_selections} a ${group.max_selections}.`;
  }
  return "";
}
export function unitPrice(product: OrderingProduct, selection: Selection): number {
  return (product.variants?.find(v => v.id === selection.variant_id)?.price_cents ?? product.price_cents) + (product.modifier_groups ?? []).flatMap(g => g.options).filter(o => selection.modifier_option_ids.includes(o.id)).reduce((sum, o) => sum + o.price_delta_cents, 0);
}
export function CustomizationText({ snapshot }: { snapshot?: Snapshot }) {
  if (!snapshot) return null;
  return <div className="customizationText">{snapshot.variant && <strong>Variação: {snapshot.variant.name}</strong>}{snapshot.modifiers?.map((option, index) => <div key={index}>{option.semantic_kind === "ADD" ? "+ " : option.semantic_kind === "REMOVE" ? "− " : `${option.group_name}: `}{option.name}</div>)}{snapshot.special_instructions && <p className="muted">Observação: {snapshot.special_instructions}</p>}</div>;
}
export function ProductCustomization({ product, initial, onAdd, onCancel }: { product: OrderingProduct; initial?: Selection; onAdd: (selection: Selection) => void; onCancel: () => void }) {
  const [selection, setSelection] = useState(initial ?? defaults(product));
  const error = selectionError(product, selection);
  const panel = useRef<HTMLElement>(null);
  useEffect(() => { panel.current?.scrollIntoView({ block: "start" }); panel.current?.querySelector<HTMLHeadingElement>("h2")?.focus(); }, [product.id]);
  const unavailableIds = selection.modifier_option_ids.filter(id => !(product.modifier_groups ?? []).flatMap(g => g.options).some(o => o.id === id && o.active && o.availability === "AVAILABLE"));
  function toggle(group: Group, option: Option) {
    setSelection(current => ({ ...current, modifier_option_ids: current.modifier_option_ids.includes(option.id) ? current.modifier_option_ids.filter(id => id !== option.id) : group.selection_mode === "SINGLE" ? [...current.modifier_option_ids.filter(id => !group.options.some(o => o.id === id)), option.id] : [...current.modifier_option_ids, option.id] }));
  }
  return <section ref={panel} className="panel customizationPanel" role="region" aria-label={`Configurar ${product.name}`}><h2 tabIndex={-1}>{product.name}</h2>
    {!!product.variants?.length && <fieldset><legend>Variação · obrigatória</legend>{product.variants.map(v => <label className="customizationChoice" key={v.id}><input type="radio" name={`variant-${product.id}`} checked={selection.variant_id === v.id} disabled={!v.active || v.availability !== "AVAILABLE"} onChange={() => setSelection(s => ({ ...s, variant_id: v.id }))} /><span>{v.name} · {money(v.price_cents)}{v.availability !== "AVAILABLE" && " · Indisponível"}</span></label>)}</fieldset>}
    {product.modifier_groups?.map(g => <fieldset key={g.id}><legend>{g.name} · {g.min_selections ? "obrigatório" : "opcional"} ({g.min_selections}–{g.max_selections})</legend>{g.options.map(o => <label className="customizationChoice" key={o.id}><input type={g.selection_mode === "SINGLE" ? "radio" : "checkbox"} name={`group-${g.id}`} checked={selection.modifier_option_ids.includes(o.id)} disabled={!o.active || o.availability !== "AVAILABLE"} onChange={() => toggle(g, o)} /><span>{o.name}{o.price_delta_cents > 0 && ` + ${money(o.price_delta_cents)}`}{o.availability !== "AVAILABLE" && " · Indisponível"}</span></label>)}</fieldset>)}
    {!!unavailableIds.length && <button className="buttonSecondary" onClick={() => setSelection(s => ({ ...s, modifier_option_ids: s.modifier_option_ids.filter(id => !unavailableIds.includes(id)) }))}>Remover escolhas indisponíveis</button>}
    <div className="field"><label htmlFor="special-note">Pedido especial (opcional)</label><textarea className="fieldControl" id="special-note" maxLength={500} value={selection.special_instructions} onChange={e => setSelection(s => ({ ...s, special_instructions: e.target.value }))} placeholder="Ex.: molho separado" /></div>
    {error && <p className="notice" data-state="warning" role="status">{error}</p>}<div className="actions"><button className="buttonSecondary" onClick={onCancel}>Voltar</button><button className="buttonPrimary" disabled={!!error} onClick={() => onAdd(selection)}>Adicionar · {money(unitPrice(product, selection))}</button></div>
  </section>;
}
