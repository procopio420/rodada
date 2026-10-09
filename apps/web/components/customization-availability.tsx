"use client";
import { useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import type { OrderingProduct } from "./product-customization";
export function CustomizationAvailability({ products, onChanged }: { products: OrderingProduct[]; onChanged: () => Promise<void> }) {
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);
  async function change(productId: string, kind: string, id: string, availability: string, version: number) {
    setPending(true);
    try {
      const result = await apiCall(`/api/pos/catalog/products/${productId}/customization/${kind}/${id}/availability/`, { method: "POST", body: JSON.stringify({ state: availability === "AVAILABLE" ? "UNAVAILABLE" : "AVAILABLE", expected_version: version }) });
      setMessage(result.response.ok ? "" : asApiError(result.body).message);
      await onChanged();
    } catch { setMessage("Não foi possível salvar. Atualize antes de tentar novamente."); }
    finally { setPending(false); }
  }
  if (!products.some(p => p.variants?.length || p.modifier_groups?.length)) return null;
  return <section className="panel"><h2>Variações e opções disponíveis</h2>{message && <p className="notice" data-state="danger" role="alert">{message}</p>}{products.map(p => <div key={p.id}>{(p.variants ?? []).map(v => <div className="dataRow" key={v.id}><span>{p.name} · {v.name}</span><button className="buttonSecondary" disabled={pending} onClick={() => void change(p.id, "variant", v.id, v.availability, v.version)}>{v.availability === "AVAILABLE" ? "Indisponibilizar" : "Reativar"} {v.name}</button></div>)}{(p.modifier_groups ?? []).map(g => <div key={g.id}>{g.options.map(o => <div className="dataRow" key={o.id}><span>{p.name} · {g.name} · {o.name}</span><button className="buttonSecondary" disabled={pending} onClick={() => void change(p.id, "option", o.id, o.availability, o.version)}>{o.availability === "AVAILABLE" ? "Indisponibilizar" : "Reativar"} {o.name}</button></div>)}</div>)}</div>)}</section>;
}
