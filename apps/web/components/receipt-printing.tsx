"use client";
import { useEffect, useRef, useState } from "react";
import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";

type Endpoint = { id: string; label: string; adapter: string; enabled: boolean; width_mm: number; stations: string[] };
type Document = { id: string; html: string; text: string; kind: string };
type Job = { id: string; document_id: string; endpoint_id: string; state: string; last_error: string; reprint_of: string | null; output?: Document };
export const printState: Record<string, string> = { QUEUED: "Na fila", SENDING: "Enviando", FAILED_RETRYABLE: "Falha antes do envio · nova tentativa programada", FAILED_FINAL: "Falha · revisar configuração", DELIVERY_UNCERTAIN: "Pode ter impresso · confira o papel", SPOOL_ACCEPTED: "Envio aceito · papel não confirmado", OUTPUT_READY: "Documento disponível · papel não confirmado", PRINTED: "Papel confirmado pelo operador", CANCELLED: "Cancelado" };

async function call<T>(path: string, data?: object): Promise<T> {
  const result = await apiCall<T>(`/api/pos/printing/${path}`, data ? { method: "POST", body: JSON.stringify(data) } : undefined);
  if (!result.response.ok) throw new Error(asApiError(result.body).message);
  return result.body as T;
}

export function ReceiptPrinting({ tabId, closed = false, orderId, station }: { tabId: string; closed?: boolean; orderId?: string; station?: "BAR" | "KITCHEN" }) {
  const [allowed, setAllowed] = useState(false), [open, setOpen] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const [document, setDocument] = useState<Document | null>(null), [job, setJob] = useState<Job | null>(null), [endpoints, setEndpoints] = useState<Endpoint[]>([]), [endpointId, setEndpointId] = useState("");
  const [payments, setPayments] = useState<{ id: string; amount_cents: number }[]>([]), [paymentId, setPaymentId] = useState(""), [reason, setReason] = useState("");
  const [share, setShare] = useState<{ id: string; documentId: string; url: string } | null>(null);
  const intent = useRef<string | null>(null), copyIntent = useRef<string | null>(null), frame = useRef<HTMLIFrameElement>(null);
  useEffect(() => {
    void apiCall<StaffSessionView>("/api/auth/me").then(result => {
      if (result.response.ok) setAllowed((result.body as StaffSessionView).capabilities.includes(station ? `print.production.${station.toLowerCase()}` : "print.customer"));
    }).catch(() => {});
  }, [station]);
  useEffect(() => {
    if (!job || ["PRINTED", "CANCELLED", "FAILED_FINAL"].includes(job.state)) return;
    const timer = window.setInterval(() => {
      void call<Job>(`jobs/${job.id}/`).then(next => { setJob(next); setError(""); if (next.output) setDocument(next.output); }).catch(() => setError("Estado de impressão indisponível. Confira a conexão antes de reimprimir."));
    }, 5000);
    return () => window.clearInterval(timer);
  }, [job?.id, job?.state]); // eslint-disable-line react-hooks/exhaustive-deps
  async function act(operation: () => Promise<void>) {
    if (busy) return;
    setBusy(true); setError("");
    try { await operation(); } catch (failure) { setError(failure instanceof Error ? failure.message : "Impressão indisponível."); } finally { setBusy(false); }
  }
  async function preview() {
    const destinations = await call<{ results: Endpoint[] }>("endpoints/");
    const eligible = destinations.results.filter(e => e.enabled && (!station || e.stations.includes(station)));
    setEndpoints(eligible); setEndpointId(eligible[0]?.id ?? "");
    const next = await call<Document>("documents/", { tab_id: tabId, kind: orderId ? "PRODUCTION_TICKET" : closed ? "CLOSED_TAB_RECEIPT" : "CUSTOMER_CHECK", ...(orderId ? { source_id: orderId, station } : {}) });
    setDocument(next); setJob(null); intent.current = null;
    if (!orderId) {
      const tab = await apiCall<{ payments: { id: string; amount_cents: number; status: string }[] }>(`/api/pos/tabs/${tabId}/`);
      if (tab.response.ok) setPayments((tab.body as { payments: { id: string; amount_cents: number; status: string }[] }).payments.filter(p => ["CONFIRMED", "PARTIALLY_REFUNDED", "REFUNDED"].includes(p.status)));
    }
    setOpen(true);
  }
  async function queue(copy = false) {
    if (!document || !endpointId) return;
    const keyRef = copy ? copyIntent : intent;
    keyRef.current ??= crypto.randomUUID();
    const next = copy && job ? await call<Job>(`jobs/${job.id}/`, { action: "reprint", idempotency_key: keyRef.current, reason, endpoint_id: endpointId }) : await call<Job>("jobs/", { document_id: document.id, endpoint_id: endpointId, idempotency_key: keyRef.current });
    keyRef.current = null;
    setJob(next); setEndpointId(next.endpoint_id);
    const detail = await call<Job>(`jobs/${next.id}/`);
    if (detail.output) setDocument(detail.output);
  }
  if (!allowed) return null;
  return <section className="receiptPrinting">
    <button className="buttonSecondary" disabled={busy} onClick={() => void act(preview)}>{orderId ? "Ver / imprimir ticket" : "Ver conta / recibos"}</button>
    {error && <p className="notice" data-state="danger" role="alert">{error} A venda e a fila digital continuam independentes da impressão.</p>}
    {open && document && <div className="panel">
      <h3>{orderId ? "Ticket de produção" : "Conta não fiscal"}</h3>
      <p className="muted">Documento histórico. Gere uma nova conta para conferir alterações posteriores.</p>
      {!!payments.length && <div className="field"><label>Pagamento confirmado<select value={paymentId} onChange={e => setPaymentId(e.target.value)}><option value="">Selecione</option>{payments.map(p => <option key={p.id} value={p.id}>{p.id.slice(0, 8)} · R$ {(p.amount_cents / 100).toFixed(2)}</option>)}</select></label><button className="buttonSecondary" disabled={!paymentId || busy} onClick={() => void act(async () => { setDocument(await call<Document>("documents/", { tab_id: tabId, kind: closed ? "PAYMENT_RECEIPT" : "PARTIAL_PAYMENT_RECEIPT", source_id: paymentId })); setJob(null); intent.current = null; })}>Ver recibo do pagamento</button></div>}
      <iframe ref={frame} className="receiptPreview" title="Documento não fiscal" sandbox="allow-same-origin allow-modals" srcDoc={document.html.replace(/<button[^>]*>.*?<\/button>/, "")} />
      {!orderId && <><button className="buttonSecondary" disabled={busy} onClick={() => void act(async () => { const token = await call<{ id: string; token: string }>(`documents/${document.id}/share/`, {}); setShare({ id: token.id, documentId: document.id, url: `${window.location.origin}/receipt/${token.token}` }); })}>Criar link do recibo (24 horas)</button>{share && <div className="field"><label>Link de leitura<input readOnly value={share.url} /></label><button className="buttonSecondary" disabled={busy} onClick={() => void act(async () => { await call(`documents/${share.documentId}/share/`, { revoke_id: share.id }); setShare(null); })}>Revogar link</button></div>}</>}
      <a className="backLink" download={`rodada-${document.id}.txt`} href={`data:text/plain;charset=utf-8,${encodeURIComponent(document.text)}`}>Baixar texto</a>
      <div className="field"><label>Destino<select value={endpointId} disabled={busy} onChange={e => setEndpointId(e.target.value)}><option value="">Selecione a impressora</option>{endpoints.map(e => <option key={e.id} value={e.id}>{e.label} · {e.width_mm} mm</option>)}</select></label></div>
      {!endpoints.length && <p className="notice" data-state="warning">Nenhuma impressora configurada. Documento digital disponível; configure um destino de navegador na Gerência.</p>}
      {!job && <button className="buttonPrimary" disabled={!endpointId || busy} onClick={() => void act(() => queue())}>Imprimir</button>}
      {job && <><p role="status">{printState[job.state] ?? job.state} {job.last_error}</p>
        {endpoints.find(e => e.id === endpointId)?.adapter === "BROWSER" && job.state === "OUTPUT_READY" && <button className="buttonPrimary" disabled={busy} onClick={() => void act(async () => { setJob(await call<Job>(`jobs/${job.id}/`, { action: "browser_open" })); frame.current?.contentWindow?.print(); })}>Abrir impressão / Salvar PDF</button>}
        {["OUTPUT_READY", "SPOOL_ACCEPTED", "DELIVERY_UNCERTAIN"].includes(job.state) && <button className="buttonSecondary" disabled={busy} onClick={() => void act(async () => { setJob(await call<Job>(`jobs/${job.id}/`, { action: "confirm" })); })}>Confirmar que vi o papel</button>}
        <div className="field"><label>Motivo da cópia<input value={reason} maxLength={240} onChange={e => setReason(e.target.value)} /></label></div>
        <button className="buttonSecondary" disabled={busy || !reason.trim() || job.state === "SENDING"} onClick={() => void act(() => queue(true))}>Reimprimir cópia</button></>}
      <button className="buttonSecondary" onClick={() => setOpen(false)}>Fechar documento</button>
    </div>}
  </section>;
}
