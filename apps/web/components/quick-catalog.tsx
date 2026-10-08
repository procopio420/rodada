"use client";
import { useEffect, useId, useRef, useState } from "react";
import { apiCall, asApiError, StaffSessionView } from "@/lib/client/staff-auth";
import { IconReference, IconStatus, ProductIcon } from "./product-icon";

export type CatalogProduct = { id: string; name: string; normalized_name: string; price_cents: number; active: boolean; fulfillment_station: "BAR" | "KITCHEN"; availability: string; icon: IconReference };
const money = (value: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);
const normalize = (value: string) => value.normalize("NFKD").replace(/\p{M}/gu, "").toLocaleLowerCase().trim().replace(/\s+/g, " ");

export function QuickCatalog({ station, onResolved }: { station: "BAR" | "KITCHEN"; onResolved?: (product: CatalogProduct) => void }) {
  const id = useId();
  const [authorized, setAuthorized] = useState(false);
  const [open, setOpen] = useState(false), [name, setName] = useState(""), [price, setPrice] = useState("");
  const [results, setResults] = useState<CatalogProduct[]>([]), [searching, setSearching] = useState(false), [searchOk, setSearchOk] = useState(false);
  const [creating, setCreating] = useState(false), [saving, setSaving] = useState(false), [message, setMessage] = useState("");
  const [selected, setSelected] = useState<CatalogProduct | null>(null), [active, setActive] = useState(-1);
  const input = useRef<HTMLInputElement>(null), trigger = useRef<HTMLButtonElement>(null);
  useEffect(() => { let live = true; void apiCall<StaffSessionView>("/api/auth/me").then(({ response, body }) => { if (live && response.ok) setAuthorized((body as StaffSessionView).capabilities.includes(`catalog.create.${station.toLowerCase()}`)); }); return () => { live = false; }; }, [station]);
  useEffect(() => {
    if (!open || creating || selected) return;
    const abort = new AbortController();
    setSearching(true); setSearchOk(false); setActive(-1);
    const timer = setTimeout(async () => {
      try {
        const result = await apiCall<{ results: CatalogProduct[] }>(`/api/pos/catalog/suggestions/?q=${encodeURIComponent(name)}`, { signal: abort.signal });
        if (abort.signal.aborted) return;
        if (!result.response.ok) throw new Error(asApiError(result.body).message);
        setResults((result.body as { results: CatalogProduct[] }).results); setSearchOk(true); setMessage("");
      } catch (error) { if (!abort.signal.aborted) setMessage(error instanceof Error ? error.message : "Não foi possível buscar o catálogo."); }
      finally { if (!abort.signal.aborted) setSearching(false); }
    }, 180);
    return () => { clearTimeout(timer); abort.abort(); };
  }, [name, open, creating, selected]);
  useEffect(() => {
    if (!selected || selected.icon.status !== "GENERATING") return;
    let live = true;
    const timer = setInterval(() => { void apiCall<{ results: CatalogProduct[] }>("/api/pos/catalog/products/").then(({ response, body }) => { if (live && response.ok) { const fresh = (body as { results: CatalogProduct[] }).results.find(p => p.id === selected.id); if (fresh) setSelected(fresh); } }); }, 5000);
    return () => { live = false; clearInterval(timer); };
  }, [selected]);
  const exact = results.find(p => p.normalized_name === normalize(name));
  const canCreate = searchOk && !searching && !!name.trim() && !exact;
  const options = results.length + (canCreate ? 1 : 0);
  const resolve = (product: CatalogProduct) => { setSelected(product); setCreating(false); setMessage("Item disponível no catálogo existente."); onResolved?.(product); };
  const choose = (index: number) => { if (index < results.length) resolve(results[index]); else if (canCreate) { setCreating(true); setMessage(""); } };
  const close = () => { setOpen(false); setSelected(null); setCreating(false); setName(""); setPrice(""); setMessage(""); trigger.current?.focus(); };
  const save = async () => {
    if (!/^\d{1,8}([,.]\d{1,2})?$/.test(price)) { setMessage("Informe um preço válido, por exemplo 12,50."); return; }
    const [whole, fraction = ""] = price.replace(",", ".").split(".");
    const cents = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
    setSaving(true); setMessage("");
    try {
      const result = await apiCall<{ product: CatalogProduct; created: boolean }>("/api/pos/catalog/resolve-or-create/", { method: "POST", body: JSON.stringify({ name, price_cents: cents, fulfillment_station: station }) });
      if (!result.response.ok) throw new Error(asApiError(result.body).message);
      const body = result.body as { product: CatalogProduct; created: boolean };
      resolve(body.product); setMessage(body.created ? "Item criado e disponível para vender." : "Produto existente reutilizado.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Não foi possível salvar. Tente novamente."); }
    finally { setSaving(false); }
  };
  if (!authorized) return null;
  return <section className="quickCatalog" aria-label={`Catálogo rápido ${station === "BAR" ? "Bar" : "Cozinha"}`}>
    <button ref={trigger} className="buttonSecondary" onClick={() => { setOpen(true); setTimeout(() => input.current?.focus(), 0); }}>+ Item</button>
    {open && <div className="panel quickCatalogPanel"><div className="catalogHeading"><h2>{creating ? `Criar “${name.trim()}”` : "Item do catálogo"}</h2><button className="buttonQuiet" disabled={saving} onClick={close}>Fechar</button></div>
      <p className="muted">Estação: {station === "BAR" ? "Bar" : "Cozinha"}</p>
      {!selected && !creating && <><div className="field"><label htmlFor={id}>Nome do produto</label><input ref={input} id={id} maxLength={160} autoComplete="off" role="combobox" aria-expanded={searchOk} aria-controls={`${id}-list`} aria-autocomplete="list" aria-activedescendant={active >= 0 ? `${id}-option-${active}` : undefined} value={name} onChange={e => { setName(e.target.value); setSearchOk(false); }} onKeyDown={e => {
        if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); setActive(current => options ? (current + (e.key === "ArrowDown" ? 1 : options - 1) + options) % options : -1); }
        if (e.key === "Enter" && searchOk && !searching) { e.preventDefault(); if (active >= 0) choose(active); else if (exact) resolve(exact); }
        if (e.key === "Escape") close();
      }} /></div>
      {searching && <p role="status">Buscando catálogo…</p>}
      <div id={`${id}-list`} role="listbox" aria-label="Produtos existentes" className="catalogOptions">{searchOk && !searching && results.map((product, index) => <button type="button" role="option" aria-selected={active === index} id={`${id}-option-${index}`} className="catalogOption" key={product.id} onClick={() => resolve(product)}><ProductIcon icon={product.icon} /><span><strong>{product.name}</strong><small>{money(product.price_cents)} · {product.fulfillment_station === "BAR" ? "Bar" : "Cozinha"}</small><span className="statusBadge" data-state={product.active && product.availability === "AVAILABLE" ? "success" : "danger"}>{!product.active ? "Não publicado" : product.availability === "AVAILABLE" ? "Disponível" : "Indisponível"}</span></span></button>)}
      {canCreate && <button role="option" aria-selected={active === results.length} id={`${id}-option-${results.length}`} className="buttonSecondary" onClick={() => choose(results.length)}>Criar “{name.trim()}”</button>}</div>
      {searchOk && !searching && !results.length && <p className="muted">Nenhum produto encontrado.</p>}</>}
      {creating && <form onSubmit={e => { e.preventDefault(); void save(); }}><div className="field"><label htmlFor={`${id}-price`}>Preço (R$)</label><input id={`${id}-price`} autoFocus inputMode="decimal" value={price} onChange={e => setPrice(e.target.value)} disabled={saving} placeholder="12,50" /></div><div className="actions"><button type="button" className="buttonQuiet" disabled={saving} onClick={() => setCreating(false)}>Voltar</button><button className="buttonPrimary" disabled={saving}>{saving ? "Salvando…" : "Criar item"}</button></div></form>}
      {selected && <div className="catalogOption"><ProductIcon icon={selected.icon} /><span><strong>{selected.name}</strong><small>{money(selected.price_cents)}</small><IconStatus icon={selected.icon} /></span></div>}
      {message && <p className="notice" role="status">{message}</p>}
    </div>}
  </section>;
}
