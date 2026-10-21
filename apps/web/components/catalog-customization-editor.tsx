"use client";
import Link from "next/link";
import { ManagementCatalogReturn } from "@/components/management-catalog-navigation";
import styles from "./catalog-customization-editor.module.css";

import { OperationalHeading } from "@/components/operational-heading";
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
  useEffect(() => {
    let active = true;
    void apiCall<{ results: OrderingProduct[] }>("/api/pos/catalog/products/?include_inactive=true").then(result => {
      if (!active) return;
      if (!result.response.ok) { setMessage(asApiError(result.body).message); return; }
      setProducts((result.body as { results: OrderingProduct[] }).results);
    }).catch(() => {
      if (active) setMessage("Não foi possível carregar o catálogo. Confira a conexão e atualize a página.");
    });
    return () => { active = false; };
  }, []);
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
  return <main className="appShell managementShell"><header className={`productHeader managementSubpageHeader ${styles.header}`}><ManagementCatalogReturn origin="customizations" /><div className="eyebrow">RODADA / CATÁLOGO</div><OperationalHeading as="h1" icon="settings">Variações e adicionais</OperationalHeading><p className="muted">Configure produtos existentes. Preços em centavos; pedidos confirmados preservam a configuração original.</p><Link className="buttonSecondary" href="/manage/products">Editar nomes do cardápio →</Link></header>{message && <p className="notice" data-state="danger" role="alert">{message}</p>}
    <section className={`panel ${styles.selection}`} aria-labelledby="custom-product-title"><OperationalHeading as="h2" icon="cart" id="custom-product-title">Escolha um produto</OperationalHeading><p className="muted" id="custom-product-help">Escolha o produto para consultar suas variações e grupos de opções.</p><div className="field"><label htmlFor="custom-product">Produto</label><select id="custom-product" aria-describedby="custom-product-help" value={productId} disabled={busy} onChange={e => { setProductId(e.target.value); setDraft(null); if (e.target.value) void select(e.target.value); }}><option value="">Selecione um produto</option>{products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></div></section>
    {product && <><section className={`panel ${styles.configuration}`} data-customization-lists><OperationalHeading as="h2" icon="settings">{product.name}</OperationalHeading><section className={styles.listSection} aria-labelledby="custom-variants-title"><h3 id="custom-variants-title">Variações</h3>{product.variants?.map(v => <div className={styles.itemRow} key={v.id}><span>{v.name} · {money(v.price_cents)}{v.is_default && " · Padrão"}{!v.active && " · Desativada"}</span><button className="buttonSecondary" disabled={busy} onClick={() => setDraft({ ...blank("variant"), id: v.id, version: v.version, name: v.name, cents: String(v.price_cents), active: v.active, isDefault: v.is_default, priority: String(v.sort_order) })}>Editar {v.name}</button></div>)}<button className="buttonSecondary" disabled={busy} onClick={() => setDraft(blank("variant"))}>Criar variação</button>
      </section><section className={styles.listSection} aria-labelledby="custom-groups-title"><h3 id="custom-groups-title">Grupos de opções</h3>{product.modifier_groups?.map(g => <section className={styles.optionGroup} key={g.id} aria-label={g.name}><div className={styles.itemRow}><strong>{g.name} · {g.min_selections}–{g.max_selections}{!g.active && " · Desativado"}</strong><button className="buttonSecondary" disabled={busy} onClick={() => setDraft({ ...blank("group"), id: g.id, version: g.version, name: g.name, active: g.active, mode: g.selection_mode, min: String(g.min_selections), max: String(g.max_selections), priority: String(g.sort_order) })}>Editar {g.name}</button></div>{g.options.map(o => <div className={styles.itemRow} key={o.id}><span>{o.name} · +{money(o.price_delta_cents)}{!o.active && " · Desativada"}</span><button className="buttonQuiet" disabled={busy} onClick={() => setDraft({ ...blank("option", g.id), id: o.id, version: o.version, name: o.name, cents: String(o.price_delta_cents), active: o.active, isDefault: o.default_selected, semantic: o.semantic_kind, priority: String(o.sort_order) })}>Editar {o.name}</button></div>)}<div className={styles.groupActions}><button className="buttonSecondary" disabled={busy} onClick={() => setDraft(blank("option", g.id))}>Criar opção em {g.name}</button><button className="buttonQuiet" disabled={busy} onClick={() => void command({ kind: "detach", group_id: g.id })}>Desassociar {g.name}</button></div></section>)}<button className="buttonSecondary" disabled={busy} onClick={() => setDraft(blank("group"))}>Criar grupo</button>
      </section><div className="field"><label htmlFor="attach-group">Reutilizar grupo do estabelecimento</label><select id="attach-group" value={attachId} onChange={e => setAttachId(e.target.value)}><option value="">Selecione um grupo</option>{library.filter(g => !product.modifier_groups?.some(existing => existing.id === g.id)).map(g => <option key={g.id} value={g.id}>{g.name}</option>)}</select><button className="buttonSecondary" disabled={!attachId || busy} onClick={() => void command({ kind: "attach", group_id: attachId })}>Associar grupo</button></div>
    </section>
    {draft && <form className={`panel ${styles.editor}`} aria-labelledby="custom-draft-title" onSubmit={e => { e.preventDefault(); save(); }}><OperationalHeading as="h2" icon="settings" id="custom-draft-title">{draft.id ? "Editar" : "Criar"} {draft.kind === "variant" ? "variação" : draft.kind === "group" ? "grupo" : "opção"}</OperationalHeading><fieldset className={styles.fields}><legend>Dados da configuração</legend><div className="field"><label htmlFor="config-name">Nome</label><input id="config-name" required maxLength={100} value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })} /></div>
      {draft.kind !== "group" ? <><div className="field"><label htmlFor="config-cents">{draft.kind === "variant" ? "Preço" : "Adicional"} em centavos</label><input id="config-cents" type="number" inputMode="numeric" min={0} max={2147483647} step={1} required value={draft.cents} onChange={e => setDraft({ ...draft, cents: e.target.value })} /></div><label className={`customizationChoice ${styles.choice}`}><input type="checkbox" checked={draft.isDefault} onChange={e => setDraft({ ...draft, isDefault: e.target.checked })} />Selecionar por padrão</label><div className="field"><label htmlFor="priority">Prioridade de exibição</label><input id="priority" type="number" min={0} value={draft.priority} onChange={e => setDraft({ ...draft, priority: e.target.value })} /></div></> : <><div className="field"><label htmlFor="mode">Seleção</label><select id="mode" value={draft.mode} onChange={e => setDraft({ ...draft, mode: e.target.value, max: e.target.value === "SINGLE" ? "1" : draft.max })}><option value="SINGLE">Uma opção</option><option value="MULTI">Várias opções</option></select></div><div className="field"><label htmlFor="minimum">Mínimo (1 ou mais = obrigatório)</label><input id="minimum" type="number" min={0} max={100} value={draft.min} onChange={e => setDraft({ ...draft, min: e.target.value })} /></div><div className="field"><label htmlFor="maximum">Máximo</label><input id="maximum" type="number" min={1} max={100} disabled={draft.mode === "SINGLE"} value={draft.max} onChange={e => setDraft({ ...draft, max: e.target.value })} /></div></>}
      {draft.kind === "option" && <div className="field"><label htmlFor="semantic">Tipo de opção</label><select id="semantic" value={draft.semantic} onChange={e => setDraft({ ...draft, semantic: e.target.value })}><option value="CHOICE">Escolha</option><option value="ADD">Adicional</option><option value="REMOVE">Remoção</option></select></div>}
      <div className="field"><label htmlFor="display-priority">Prioridade do grupo neste produto</label><input id="display-priority" type="number" min={0} disabled={draft.kind !== "group"} value={draft.priority} onChange={e => setDraft({ ...draft, priority: e.target.value })} /></div>
      <label className={`customizationChoice ${styles.choice}`}><input type="checkbox" checked={draft.active} onChange={e => setDraft({ ...draft, active: e.target.checked })} />Ativo no catálogo</label></fieldset><div className={styles.formActions}><button type="button" className="buttonSecondary" disabled={busy} onClick={() => setDraft(null)}>Voltar</button><button className="buttonPrimary" disabled={busy}>{busy ? "Salvando…" : "Salvar configuração"}</button></div></form>}
    <CustomizationAvailability managementLayout products={[product]} onChanged={() => select(productId)} /></>}
  </main>;
}
