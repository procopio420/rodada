"use client";
import { useEffect, useRef, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
export function ConfirmedItemRemoval({ item, onRefresh, onClose, onPendingChange }: {
 item: { id: string; product_name: string; quantity: number };
 onRefresh: () => Promise<void>; onClose: () => void; onPendingChange: (pending: boolean) => void;
}) {
 const [reason, setReason] = useState("WRONG_ITEM_ENTERED");
 const [busy, setBusy] = useState(false), [message, setMessage] = useState("");
 const [uncertain, setUncertain] = useState(false), [applied, setApplied] = useState(false);
 const intent = useRef<{ kind: string; reason_code: string; idempotency_key: string } | null>(null);
 const sending = useRef(false);
 const dialog = useRef<HTMLDialogElement>(null);
 useEffect(() => {
  const element = dialog.current;
  const previous = document.activeElement as HTMLElement | null;
  element?.showModal();
  return () => { element?.close(); requestAnimationFrame(() => previous?.focus()); };
 }, []);
 useEffect(() => { onPendingChange(true); return () => onPendingChange(false); }, [onPendingChange]);
 async function refresh() { await onRefresh(); onClose(); }
 async function remove() {
  if (sending.current) return;
  sending.current = true; setBusy(true); setMessage("");
  if (!intent.current) intent.current = { kind: reason, reason_code: reason, idempotency_key: crypto.randomUUID() };
  let committed = applied, resolved = false;
  try {
   if (committed) { await refresh(); return; }
   const result = await apiCall<{ status: string; financial_disposition: string; order_item_state: string }>(`/api/attendance/order-items/${item.id}/corrections/cancel/`, { method: "POST", body: JSON.stringify(intent.current) });
   if (result.response.ok && result.body && "order_item_state" in result.body && result.body.order_item_state === "CANCELLED" && result.body.status === "APPLIED") {
    committed = true; setApplied(true); setUncertain(false); await refresh();
   } else if (result.response.status === 202 || (result.response.ok && result.body && "financial_disposition" in result.body && result.body.financial_disposition === "REFUND_REQUIRED")) {
    resolved = true; setUncertain(false); intent.current = null; setMessage("Este item envolve pagamento. A gerência precisa resolver o estorno; ele ainda não foi removido."); await onRefresh();
   } else if (result.response.status >= 500 || result.response.ok) {
    setUncertain(true); setMessage("Resultado não confirmado. Verifique a mesma remoção antes de continuar.");
   } else {
    resolved = true; setUncertain(false); intent.current = null; setMessage(asApiError(result.body).message); await onRefresh();
   }
  } catch { if (committed) setMessage("Item removido. Atualize a comanda para conferir os valores."); else if (resolved) setMessage(current => `${current} Não foi possível atualizar a comanda.`); else { setUncertain(true); setMessage("Resultado não confirmado. Verifique a mesma remoção antes de continuar."); } }
  finally { sending.current = false; setBusy(false); }
 }
 return <dialog ref={dialog} className="removalDialog" aria-labelledby="removal-title" onCancel={event => { event.preventDefault(); if (!sending.current && !uncertain && !applied) onClose(); }}>
  <h3 id="removal-title">Remover {item.quantity}× {item.product_name}?</h3>
  <p className="muted">Remove toda esta linha do pedido. O histórico e o motivo ficam registrados.</p>
  <div className="field"><label htmlFor="removal-reason">Motivo da remoção</label><select id="removal-reason" value={reason} disabled={busy || uncertain || applied} onChange={event => setReason(event.target.value)}><option value="WRONG_ITEM_ENTERED">Item escolhido por engano</option><option value="CUSTOMER_CHANGED_MIND">Cliente desistiu do item</option></select></div>
  {message && <p className="notice" data-state="warning" role="status">{message}</p>}
  <div className="actions"><button className="buttonSecondary" disabled={busy} onClick={() => void remove()}>{busy ? "Verificando…" : applied ? "Atualizar comanda" : uncertain ? "Verificar mesma remoção" : "Confirmar remoção"}</button><button className="buttonQuiet" disabled={busy || uncertain || applied} onClick={onClose}>Voltar</button></div>
 </dialog>;
}
