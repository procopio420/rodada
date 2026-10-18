"use client";

import { OperationalHeading } from "@/components/operational-heading";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiCall, asApiError, StaffSessionView } from "@/lib/client/staff-auth";
import { CatalogProduct, QuickCatalog } from "./quick-catalog";
import { IconStatus, ProductIcon } from "./product-icon";
import { ActionDialog } from "./action-dialog";
import styles from "./catalog-icon-editor.module.css";
import { attendanceCategory, compareAttendanceCategories, normalizeCatalogSearch } from "@/lib/client/attendance-catalog";

export function CatalogIconEditor() {
  const [allowed, setAllowed] = useState(false), [products, setProducts] = useState<CatalogProduct[]>([]);
  const [selected, setSelected] = useState(""), [busy, setBusy] = useState(false), [message, setMessage] = useState("");
  const [lastPicked, setLastPicked] = useState("");
  const [open, setOpen] = useState(false), [category, setCategory] = useState<string | null>(null), [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true), [loadError, setLoadError] = useState("");
  const generation = useRef(0);
  const denied = useRef(false);
  const load = useCallback(async () => {
    const request = ++generation.current;
    try {
      const result = await apiCall<{ results: CatalogProduct[] }>("/api/pos/catalog/products/");
      if (request !== generation.current) return;
      if (!result.response.ok) {
        if ([401, 403].includes(result.response.status)) { denied.current = true; setAllowed(false); setOpen(false); setProducts([]); setSelected(""); }
        throw new Error(asApiError(result.body).message);
      }
      setProducts((result.body as { results: CatalogProduct[] }).results); setLoadError("");
    } catch (error) { if (request === generation.current) setLoadError(error instanceof Error ? error.message : "Não foi possível consultar o cardápio."); }
    finally { if (request === generation.current) setLoading(false); }
  }, []);
  useEffect(() => {
    let live = true;
    void apiCall<StaffSessionView>("/api/auth/me").then(({ response, body }) => { if (live && response.ok) setAllowed(!denied.current && (body as StaffSessionView).capabilities.includes("catalog.icon.manage")); }).catch(() => {});
    void Promise.resolve().then(load);
    return () => { live = false; generation.current += 1; };
  }, [load]);
  useEffect(() => { if (!allowed || busy) return; const timer = setInterval(() => void load(), 5000); return () => clearInterval(timer); }, [allowed, busy, load]);
  const product = products.find(p => p.id === selected);
  const mutate = async (action: string, extra = {}) => {
    if (!product) return;
    setBusy(true); setMessage("");
    try { const result = await apiCall(`/api/pos/catalog/products/${product.id}/icon/`, { method: "POST", body: JSON.stringify({ action, ...extra }) }); if (!result.response.ok) throw new Error(asApiError(result.body).message); setMessage(action === "regenerate" ? "Geração solicitada. O ícone atual permanece visível." : "Ícone atualizado."); await load(); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Falha ao atualizar ícone."); }
    finally { setBusy(false); }
  };
  const upload = async (file?: File) => {
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { setMessage("Use uma imagem até 5 MB."); return; }
    setBusy(true);
    const reader = new FileReader();
    reader.onload = () => void mutate("upload", { image_base64: String(reader.result).split(",")[1], mime: file.type });
    reader.onerror = () => { setMessage("Não foi possível ler a imagem."); setBusy(false); };
    reader.readAsDataURL(file);
  };
  const [editedName, setEditedName] = useState("");
  const filtered = products.filter(item => normalizeCatalogSearch(item.name).includes(normalizeCatalogSearch(query)));
  const categories = [...new Set(filtered.map(attendanceCategory))].sort(compareAttendanceCategories);
  const visible = filtered.filter(item => category === "" || attendanceCategory(item) === category);
  const focusProduct = visible.find(item => item.id === lastPicked)?.id ?? visible[0]?.id;
  const closeLayer = () => {
    if (busy) return;
    setMessage("");
    if (selected) setSelected("");
    else if (category !== null) setCategory(null);
    else setOpen(false);
  };
  async function rename() {
    if (!product || busy || !editedName.trim()) return;
    setBusy(true); setMessage("");
    try {
      const result = await apiCall(`/api/pos/catalog/products/${product.id}/`, { method: "PATCH", body: JSON.stringify({ name: editedName.trim() }) });
      if (!result.response.ok) throw new Error(asApiError(result.body).message);
      setMessage("Nome confirmado. Pedidos anteriores conservam seu histórico.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Resultado não confirmado; consulte o produto antes de tentar novamente."); }
    finally {
      try { await load(); }
      catch { setMessage("Resultado não confirmado; não foi possível consultar o produto. Atualize antes de tentar novamente."); }
      finally { setBusy(false); }
    }
  }
  if (!allowed) return null;
  return <section className="panel managementCatalog"><OperationalHeading as="h2" icon="cart">Gerenciar cardápio</OperationalHeading>
    <div className="actions"><QuickCatalog station="BAR" chooseStation onResolved={() => void load()} /><button className="buttonSecondary" aria-haspopup="dialog" onClick={() => { setSelected(""); setLastPicked(""); setCategory(null); setQuery(""); setMessage(""); setOpen(true); }}>Editar produto e ícone</button></div>
    {open && <ActionDialog title={product ? `Editar ${product.name}` : category === null ? "Escolha uma categoria" : category || "Todos"} dialogClassName={styles.dialog} locked={busy} onClose={closeLayer} dismissOnBackdrop>
      {loading && <p role="status">Carregando cardápio…</p>}
      {loadError && <div className="notice" role="alert">{loadError}<button className="buttonQuiet" disabled={busy} onClick={() => void load()}>Tentar novamente</button></div>}
    {product && <><div className="field"><label htmlFor="product-edit-name">Nome do produto</label><input id="product-edit-name" autoFocus maxLength={160} value={editedName} disabled={busy} onChange={event => setEditedName(event.target.value)} /></div><button className="buttonSecondary" disabled={busy || !editedName.trim() || editedName.trim()===product.name} onClick={() => void rename()}>Salvar nome</button><div className="catalogOption"><ProductIcon icon={product.icon} /><strong>{product.name}</strong><IconStatus icon={product.icon} /></div><div className="actions"><button className="buttonSecondary" disabled={busy} onClick={() => void mutate("regenerate", { idempotency_key: crypto.randomUUID() })}>Regenerar ícone</button><button className="buttonQuiet" disabled={busy} onClick={() => void mutate("remove")}>Voltar ao placeholder</button></div><div className="field"><label htmlFor="icon-upload">Substituir por imagem · quadrada, 128–2048 px, até 5 MB</label><input id="icon-upload" type="file" accept="image/png,image/jpeg,image/webp" disabled={busy} onChange={e => { void upload(e.target.files?.[0]); e.target.value = ""; }} /></div></>}

    {!product && !loading && !loadError && <>
      <div className="field"><label htmlFor="catalog-edit-search">Buscar produto</label><input id="catalog-edit-search" autoFocus type="search" value={query} onChange={event => setQuery(event.target.value)} /></div>
      {category === null ? <nav className={styles.categories} aria-label="Categorias do cardápio">
        {!!filtered.length && <button className="buttonSecondary" onClick={() => setCategory("")}><strong>Todos</strong><small>{filtered.length} itens</small></button>}
        {categories.map(name => <button className="buttonSecondary" key={name} onClick={() => setCategory(name)}><strong>{name}</strong><small>{filtered.filter(item => attendanceCategory(item) === name).length} itens</small></button>)}
      </nav> : <div className={`posProducts ${styles.products}`}>{visible.map(item => <button autoFocus={item.id === focusProduct} className="buttonSecondary posProduct attendanceProductPick" key={item.id} aria-label={`Editar ${item.name}`} onClick={() => { setSelected(item.id); setLastPicked(item.id); setEditedName(item.name); setMessage(""); }}><ProductIcon icon={item.icon} /><strong>{item.name}</strong></button>)}</div>}
      {(category === null ? !filtered.length : !visible.length) && <p role="status">{query.trim() ? "Nenhum produto encontrado." : "Nenhum produto nesta categoria."}</p>}
    </>}
    {message && <p className="notice" role="status">{message}</p>}
    </ActionDialog>}
  </section>;
}
