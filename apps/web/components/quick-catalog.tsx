"use client";

import { useEffect, useId, useRef, useState } from "react";
import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";
import { ProductIcon, type IconData } from "./product-icon";

type Product = { id: string; name: string; price_cents: number; fulfillment_station: string; active: boolean; availability: string; icon?: IconData };
const normalize = (name: string) => name.normalize("NFKC").toLocaleLowerCase().trim().replace(/\s+/g, " ");
const money = (cents: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);

export function QuickCatalog({ station, onChanged }: { station: "BAR" | "KITCHEN"; onChanged: () => Promise<void> }) {
  const id = useId();
  const [canCreate, setCanCreate] = useState(false), [name, setName] = useState(""), [price, setPrice] = useState("");
  const [results, setResults] = useState<Product[]>([]), [selected, setSelected] = useState<Product | null>(null);
  const [creating, setCreating] = useState(false), [busy, setBusy] = useState(false), [searching, setSearching] = useState(false);
  const [error, setError] = useState(""), [notice, setNotice] = useState("");
  const intent = useRef(false);
  useEffect(() => { void apiCall<StaffSessionView>("/api/auth/me").then(r => {
    if (r.response.ok) setCanCreate((r.body as StaffSessionView).capabilities.includes("catalog.product.create"));
  }).catch(() => setCanCreate(false)); }, []);
  useEffect(() => {
    let cancelled = false;
    setSelected(null); setCreating(false); setError(""); setNotice("");
    if (!name.trim()) { setResults([]); setSearching(false); return; }
    setSearching(true);
    const timer = setTimeout(async () => {
      try {
        const r = await apiCall<{ results: Product[] }>(`/api/pos/catalog/products/?q=${encodeURIComponent(name)}&include_inactive=true`);
        if (cancelled) return;
        if (!r.response.ok) { setError(asApiError(r.body).message); setResults([]); }
        else setResults((r.body as { results: Product[] }).results);
      } catch { if (!cancelled) setError("Não foi possível buscar o catálogo. Tente novamente."); }
      finally { if (!cancelled) setSearching(false); }
    }, 250);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [name]);
  const exact = results.some(p => normalize(p.name) === normalize(name));
  async function save() {
    if (intent.current || !creating || searching || error) return;
    const normalizedPrice = price.trim().replace(/\./g, "").replace(",", ".");
    if (!/^\d+(\.\d{1,2})?$/.test(normalizedPrice)) { setError("Informe o preço em reais, com até duas casas decimais."); return; }
    intent.current = true; setBusy(true); setError("");
    try {
      const r = await apiCall<{ product: Product; created: boolean }>("/api/pos/catalog/products/resolve/", { method: "POST", body: JSON.stringify({ name: name.trim(), price_cents: Math.round(Number(normalizedPrice) * 100), fulfillment_station: station }) });
      if (!r.response.ok) { setError(asApiError(r.body).message); return; }
      const result = r.body as { product: Product; created: boolean };
      setSelected(result.product); setCreating(false);
      setNotice(result.created ? "Produto criado. Ícone de fallback disponível; IA não configurada." : "Produto existente reutilizado; preço e estação preservados.");
      await onChanged();
    } catch { setError("Não foi possível confirmar. Tente novamente com o mesmo nome; produtos não serão duplicados."); }
    finally { intent.current = false; setBusy(false); }
  }
  return <section className="panel" aria-label="Quick Catalog">
    <h2>Adicionar item ao catálogo</h2>
    <div className="field"><label htmlFor={id}>Buscar produto por nome</label><input id={id} maxLength={160} value={name} disabled={busy} onChange={e => setName(e.target.value)} role="combobox" aria-autocomplete="list" aria-expanded={results.length > 0} aria-controls={`${id}-results`} /></div>
    {searching && <p role="status">Buscando catálogo…</p>}
    {error && <div className="notice" data-state="danger" role="alert">{error}</div>}
    {notice && <p role="status">{notice}</p>}
    <div id={`${id}-results`} role="listbox" aria-label="Produtos encontrados">
      {!searching && results.map(p => <button className="catalogOption" key={p.id} role="option" aria-selected={selected?.id === p.id} disabled={busy} onClick={() => { setSelected(p); setCreating(false); setNotice("Produto existente selecionado. Nenhuma cópia foi criada."); }}>
        <ProductIcon name={p.name} icon={p.icon} /><span><strong>{p.name}</strong><small>{money(p.price_cents)} · {p.fulfillment_station === "BAR" ? "Bar" : "Cozinha"} · {!p.active ? "Desativado" : p.availability === "AVAILABLE" ? "Disponível" : "Indisponível"}</small></span>
      </button>)}
    </div>
    {name.trim() && !searching && !error && !exact && canCreate && <button className="buttonSecondary" disabled={busy} onClick={() => { setCreating(true); setSelected(null); }}>Criar "{name.trim()}"</button>}
    {selected && <div className="notice" data-state="info"><strong>{selected.name}</strong> · {money(selected.price_cents)}<p className="inlineNote">{selected.active ? "Já está no catálogo da estação indicada." : "Item desativado; sua seleção não o publica nem altera sua disponibilidade."}</p></div>}
    {creating && <><div className="field"><label htmlFor={`${id}-price`}>Preço do novo produto (R$)</label><input id={`${id}-price`} inputMode="decimal" value={price} disabled={busy} onChange={e => { setPrice(e.target.value); setError(""); }} /></div><p className="muted">Destino: {station === "BAR" ? "Bar" : "Cozinha"}. Ícone de fallback; geração por IA será configurada depois.</p><button className="buttonPrimary" disabled={busy || searching} onClick={() => void save()}>{busy ? "Salvando…" : "Salvar novo produto"}</button></>}
    {!canCreate && <p className="muted">Você pode buscar produtos. A criação exige permissão do gerente.</p>}
  </section>;
}
