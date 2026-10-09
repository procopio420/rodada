"use client";
import { useCallback, useEffect, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { money, type OrderingProduct } from "./product-customization";
import { CustomizationAvailability } from "./customization-availability";

type Draft = { kind: "variant" | "group" | "option"; id?: string; version?: number; groupId?: string; name: string; cents: string; active: boolean; isDefault: boolean; mode: string; min: string; max: string; semantic: string; priority: string };
const blank = (kind: Draft["kind"], groupId?: string): Draft => ({ kind, groupId, name: "", cents: "0", active: true, isDefault: false, mode: "SINGLE", min: "0", max: "1", semantic: "CHOICE", priority: "0" });
export function CatalogCustomizationEditor() {
  const [products, setProducts] = useState<OrderingProduct[]>([]);
  const [productId, setProductId] = useState("");
  const [draft, setDraft] = useState<Draft | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [library, setLibrary] = useState<{ id: string; name: string }[]>([]);
  const [attachId, setAttachId] = useState("");
  const load = useCallback(async () => {
    const result = await apiCall<{ results: OrderingProduct[] }>("/api/pos/catalog/products/?include_inactive=true");
    if (!result.response.ok) { setMessage(asApiError(result.body).message); return; }
    setProducts((result.body as { results: OrderingProduct[] }).results);
  }, []);
  useEffect(() => { void load(); }, [load]);
  const select = useCallback(async (id: string) => {
    const result = await apiCall<OrderingProduct & { reusable_groups: { id: string; name: string }[] }>(`/api/pos/catalog/products/${id}/customization/`);
    if (!result.response.ok) { setMessage(asApiError(result.body).message); return; }
    const schema = result.body as OrderingProduct & { reusable_groups: { id: string; name: string }[] };
    setProducts(current => current.map(p => p.id === id ? { ...p, ...schema, id } : p));
    setLibrary(schema.reusable_groups ?? []);
  }, []);
  const product = products.find(p => p.id === productId);
  async function command(payload: object) {
    setBusy(true); setMessage("");
    try {
      const result = await apiCall(`/api/pos/catalog/products/${productId}/customization/`, { method: "POST", body: JSON.stringify(payload) });
      if (!result.response.ok) { setMessage(asApiError(result.body).message); await select(productId); return; }
      setDraft(null); await select(productId);
    } catch { setMessage("Não foi possível salvar. Atualize a configuração antes de repetir."); }
    finally { setBusy(false); }
  }
  function save() {
    if (!draft) return;
    const common = { name: draft.name, active: draft.active };
    const values = draft.kind === "variant" ? { ...common, price_cents: Number(draft.cents), is_default: draft.isDefault, sort_order: Number(draft.priority) } : draft.kind === "group" ? { ...common, selection_mode: draft.mode, min_selections: Number(draft.min), max_selections: Number(draft.max) } : { ...common, price_delta_cents: Number(draft.cents), default_selected: draft.isDefault, semantic_kind: draft.semantic, sort_order: Number(draft.priority) };
    void command({ kind: draft.kind, id: draft.id, expected_version: draft.version, group_id: draft.groupId, display_order: draft.kind === "group" ? Number(draft.priority) : undefined, values });
  }
  return <main className="appShell"><header className="productHeader"><div className="eyebrow">RODADA / CATÁLOGO</div><h1>Variações e adicionais</h1><p className="muted">Configure produtos existentes. Preços em centavos; pedidos confirmados preservam a configuração original.</p></header>{message && <p className="notice" data-state="danger" role="alert">{message}</p>}
    <div className="field"><label htmlFor="custom-product">Produto</label><select id="custom-product" value={productId} disabled={busy} onChange={e => { setProductId(e.target.value); setDraft(null); if (e.target.value) void select(e.target.value); }}><option value="">Selecione um produto</option>{products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></div>
    {product && <><section className="panel"><h2>{product.name}</h2><h3>Variações</h3>{product.variants?.map(v => <div className="dataRow" key={v.id}><span>{v.name} · {money(v.price_cents)}{v.is_default && " · Padrão"}{!v.active && " · Desativada"}</span><button className="buttonSecondary" disabled={busy} onClick={() => setDraft({ ...blank("variant"), id: v.id, version: v.version, name: v.name, cents: String(v.price_cents), active: v.active, isDefault: v.is_default, priority: String(v.sort_order) })}>Editar {v.name}</button></div>)}<button className="buttonSecondary" disabled={busy} onClick={() => setDraft(blank("variant"))}>Criar variação</button>
      <h3>Grupos de opções</h3>{product.modifier_groups?.map(g => <section key={g.id}><div className="dataRow"><strong>{g.name} · {g.min_selections}–{g.max_selections}{!g.active && " · Desativado"}</strong><button className="buttonSecondary" disabled={busy} onClick={() => setDraft({ ...blank("group"), id: g.id, version: g.version, name: g.name, active: g.active, mode: g.selection_mode, min: String(g.min_selections), max: String(g.max_selections), priority: String(g.sort_order) })}>Editar {g.name}</button></div>{g.options.map(o => <div className="dataRow" key={o.id}><span>{o.name} · +{money(o.price_delta_cents)}{!o.active && " · Desativada"}</span><button className="buttonQuiet" disabled={busy} onClick={() => setDraft({ ...blank("option", g.id), id: o.id, version: o.version, name: o.name, cents: String(o.price_delta_cents), active: o.active, isDefault: o.default_selected, semantic: o.semantic_kind, priority: String(o.sort_order) })}>Editar {o.name}</button></div>)}<div className="actions"><button className="buttonSecondary" disabled={busy} onClick={() => setDraft(blank("option", g.id))}>Criar opção em {g.name}</button><button className="buttonQuiet" disabled={busy} onClick={() => void command({ kind: "detach", group_id: g.id })}>Desassociar {g.name}</button></div></section>)}<button className="buttonSecondary" disabled={busy} onClick={() => setDraft(blank("group"))}>Criar grupo</button>
      <div className="field"><label htmlFor="attach-group">Reutilizar grupo do estabelecimento</label><select id="attach-group" value={attachId} onChange={e => setAttachId(e.target.value)}><option value="">Selecione um grupo</option>{library.filter(g => !product.modifier_groups?.some(existing => existing.id === g.id)).map(g => <option key={g.id} value={g.id}>{g.name}</option>)}</select><button className="buttonSecondary" disabled={!attachId || busy} onClick={() => void command({ kind: "attach", group_id: attachId })}>Associar grupo</button></div>
    </section>
    {draft && <form className="panel" onSubmit={e => { e.preventDefault(); save(); }}><h2>{draft.id ? "Editar" : "Criar"} {draft.kind === "variant" ? "variação" : draft.kind === "group" ? "grupo" : "opção"}</h2><div className="field"><label htmlFor="config-name">Nome</label><input id="config-name" required maxLength={100} value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })} /></div>
      {draft.kind !== "group" ? <><div className="field"><label htmlFor="config-cents">{draft.kind === "variant" ? "Preço" : "Adicional"} em centavos</label><input id="config-cents" type="number" inputMode="numeric" min={0} max={2147483647} step={1} required value={draft.cents} onChange={e => setDraft({ ...draft, cents: e.target.value })} /></div><label className="customizationChoice"><input type="checkbox" checked={draft.isDefault} onChange={e => setDraft({ ...draft, isDefault: e.target.checked })} />Selecionar por padrão</label><div className="field"><label htmlFor="priority">Prioridade de exibição</label><input id="priority" type="number" min={0} value={draft.priority} onChange={e => setDraft({ ...draft, priority: e.target.value })} /></div></> : <><div className="field"><label htmlFor="mode">Seleção</label><select id="mode" value={draft.mode} onChange={e => setDraft({ ...draft, mode: e.target.value, max: e.target.value === "SINGLE" ? "1" : draft.max })}><option value="SINGLE">Uma opção</option><option value="MULTI">Várias opções</option></select></div><div className="field"><label htmlFor="minimum">Mínimo (1 ou mais = obrigatório)</label><input id="minimum" type="number" min={0} max={100} value={draft.min} onChange={e => setDraft({ ...draft, min: e.target.value })} /></div><div className="field"><label htmlFor="maximum">Máximo</label><input id="maximum" type="number" min={1} max={100} disabled={draft.mode === "SINGLE"} value={draft.max} onChange={e => setDraft({ ...draft, max: e.target.value })} /></div></>}
      {draft.kind === "option" && <div className="field"><label htmlFor="semantic">Tipo de opção</label><select id="semantic" value={draft.semantic} onChange={e => setDraft({ ...draft, semantic: e.target.value })}><option value="CHOICE">Escolha</option><option value="ADD">Adicional</option><option value="REMOVE">Remoção</option></select></div>}
      <div className="field"><label htmlFor="display-priority">Prioridade do grupo neste produto</label><input id="display-priority" type="number" min={0} disabled={draft.kind !== "group"} value={draft.priority} onChange={e => setDraft({ ...draft, priority: e.target.value })} /></div>
      <label className="customizationChoice"><input type="checkbox" checked={draft.active} onChange={e => setDraft({ ...draft, active: e.target.checked })} />Ativo no catálogo</label><div className="actions"><button type="button" className="buttonSecondary" disabled={busy} onClick={() => setDraft(null)}>Voltar</button><button className="buttonPrimary" disabled={busy}>{busy ? "Salvando…" : "Salvar configuração"}</button></div></form>}
    <CustomizationAvailability products={[product]} onChanged={() => select(productId)} /></>}
  </main>;
}
