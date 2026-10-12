"use client";

import { OperationalHeading } from "@/components/operational-heading";
import { useEffect, useState } from "react";
import { apiCall, asApiError, StaffSessionView } from "@/lib/client/staff-auth";
import { CatalogProduct, QuickCatalog } from "./quick-catalog";
import { IconStatus, ProductIcon } from "./product-icon";

export function CatalogIconEditor() {
  const [allowed, setAllowed] = useState(false), [products, setProducts] = useState<CatalogProduct[]>([]);
  const [selected, setSelected] = useState(""), [busy, setBusy] = useState(false), [message, setMessage] = useState("");
  const load = async () => { const result = await apiCall<{ results: CatalogProduct[] }>("/api/pos/catalog/products/"); if (result.response.ok) setProducts((result.body as { results: CatalogProduct[] }).results); else setMessage(asApiError(result.body).message); };
  useEffect(() => { void apiCall<StaffSessionView>("/api/auth/me").then(({ response, body }) => { if (response.ok) setAllowed((body as StaffSessionView).capabilities.includes("catalog.icon.manage")); }); void load(); }, []);
  useEffect(() => { if (!allowed) return; const timer = setInterval(() => void load(), 5000); return () => clearInterval(timer); }, [allowed]);
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
    const reader = new FileReader();
    reader.onload = () => void mutate("upload", { image_base64: String(reader.result).split(",")[1], mime: file.type });
    reader.onerror = () => setMessage("Não foi possível ler a imagem.");
    reader.readAsDataURL(file);
  };
  const [editedName, setEditedName] = useState("");
  useEffect(() => { setEditedName(product?.name ?? ""); }, [product?.id, product?.name]);
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
  return <section className="panel"><OperationalHeading as="h2" icon="cart">Cardápio</OperationalHeading><div className="actions"><QuickCatalog station="BAR" onResolved={() => void load()} /><QuickCatalog station="KITCHEN" onResolved={() => void load()} /></div>
    <details><summary>Editar produto e ícone</summary><div className="field"><label htmlFor="icon-product">Produto</label><select id="icon-product" value={selected} onChange={e => setSelected(e.target.value)}><option value="">Selecionar produto</option>{products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></div>
    {product && <><div className="field"><label htmlFor="product-edit-name">Nome do produto</label><input id="product-edit-name" maxLength={160} value={editedName} disabled={busy} onChange={event => setEditedName(event.target.value)} /></div><button className="buttonSecondary" disabled={busy || !editedName.trim() || editedName.trim()===product.name} onClick={() => void rename()}>Salvar nome</button><div className="catalogOption"><ProductIcon icon={product.icon} /><strong>{product.name}</strong><IconStatus icon={product.icon} /></div><div className="actions"><button className="buttonSecondary" disabled={busy} onClick={() => void mutate("regenerate", { idempotency_key: crypto.randomUUID() })}>Regenerar ícone</button><button className="buttonQuiet" disabled={busy} onClick={() => void mutate("remove")}>Voltar ao placeholder</button></div><div className="field"><label htmlFor="icon-upload">Substituir por imagem · quadrada, 128–2048 px, até 5 MB</label><input id="icon-upload" type="file" accept="image/png,image/jpeg,image/webp" disabled={busy} onChange={e => { void upload(e.target.files?.[0]); e.target.value = ""; }} /></div></>}
    {message && <p className="notice" role="status">{message}</p>}</details>
  </section>;
}
