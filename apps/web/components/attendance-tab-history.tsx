"use client";
import { useState, type ReactNode } from "react";
import { ActionDialog } from "@/components/action-dialog";
import { BillSummary, type Bill } from "@/components/bill-summary";
import { apiCall, asApiError } from "@/lib/client/staff-auth";

type HistoryTab = Bill & { id: string; display_label: string; state: string; orders?: { id: string; items: { id: string; product_name: string; quantity: number; state: string }[] }[] };
export function AttendanceTabHistory({ tabs, apiRoot, onClose, pagination, searchControls }: { tabs: HistoryTab[]; pagination: ReactNode; searchControls: ReactNode; apiRoot: string; onClose: () => void }) {
 const [detail, setDetail] = useState<HistoryTab | null>(null);
 const [loading, setLoading] = useState(false);
 const [error, setError] = useState("");
 async function inspect(tab: HistoryTab) {
  setLoading(true); setError(""); setDetail(null);
  try {
   const result = await apiCall<HistoryTab>(`${apiRoot}/tabs/${tab.id}/`);
   if (result.response.ok) setDetail(result.body as HistoryTab);
   else setError(asApiError(result.body).message);
  } catch { setError("Não foi possível consultar o histórico. Tente novamente."); }
  finally { setLoading(false); }
 }
 return <ActionDialog title="Histórico de comandas" onClose={onClose} closeButtonClassName="buttonSecondary dialogReturn">
  <p className="muted">Comandas encerradas nesta página · somente consulta.</p>
  {searchControls}
  {pagination}
  {!tabs.length && <p className="muted">Nenhuma comanda encerrada.</p>}
  {tabs.map(tab => <button key={tab.id} className="buttonQuiet" disabled={loading} onClick={() => void inspect(tab)} aria-pressed={detail?.id === tab.id}>{tab.display_label || "Sem identificação"} · {tab.state === "CANCELLED" ? "Cancelada" : "Encerrada"}</button>)}
  {loading && <p role="status">Carregando comanda…</p>}
  {error && <p className="notice" data-state="danger" role="alert">{error}</p>}
  {detail && <section aria-label="Detalhes da comanda encerrada"><h3>{detail.display_label || "Sem identificação"}</h3><BillSummary bill={detail} />{detail.orders?.flatMap(order => order.items.map(item => <div className="dataRow" key={item.id}><span>{item.quantity}× {item.product_name}</span>{item.state === "CANCELLED" && <span className="muted">Cancelado</span>}</div>))}</section>}
 </ActionDialog>;
}
