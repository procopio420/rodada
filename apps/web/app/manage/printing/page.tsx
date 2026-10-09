"use client";

import { OperationalHeading } from "@/components/operational-heading";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { printState } from "@/components/receipt-printing";
type Endpoint = { id: string; label: string; adapter: string; width_mm: number; connection_ref: string; cut_supported: boolean; stations: string[]; enabled: boolean; health: string; health_at: string | null; bridge_status: string };
type Job = { id: string; state: string; last_error: string; reason: string; reprint_of: string | null; document_id: string; attempts: { number: number; outcome: string; detail: string }[] };
export default function PrintingManagement() {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]), [jobs, setJobs] = useState<Job[]>([]), [message, setMessage] = useState(""), [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState(""), [label, setLabel] = useState(""), [adapter, setAdapter] = useState("BROWSER"), [width, setWidth] = useState(80), [reference, setReference] = useState(""), [stations, setStations] = useState<string[]>([]), [enabled, setEnabled] = useState(true), [cut, setCut] = useState(false), [reason, setReason] = useState("");
  const [failedOnly, setFailedOnly] = useState(false), [offset, setOffset] = useState(0), [nextOffset, setNextOffset] = useState<number | null>(null);
  const copyIntent = useRef<{ jobId: string; key: string } | null>(null);
  const load = useCallback(async () => {
    const results = await Promise.all([apiCall<{ results: Endpoint[] }>("/api/pos/printing/endpoints/"), apiCall<{ results: Job[]; next_offset: number | null }>(`/api/pos/printing/jobs/?failed_only=${failedOnly}&offset=${offset}`)]);
    if (!results[0].response.ok || !results[1].response.ok) { setMessage(asApiError(!results[0].response.ok ? results[0].body : results[1].body).message); return; }
    setEndpoints((results[0].body as { results: Endpoint[] }).results); setJobs((results[1].body as { results: Job[] }).results); setNextOffset((results[1].body as { next_offset?: number | null }).next_offset ?? null);
  }, [failedOnly, offset]);
  useEffect(() => { void load().catch(() => setMessage("Impressão indisponível. Confira a conexão.")); const timer = window.setInterval(() => { void load().catch(() => setMessage("Não foi possível atualizar os trabalhos.")); }, 5000); return () => window.clearInterval(timer); }, [load]);
  async function mutate(path: string, data: object) {
    if (busy) return;
    setBusy(true); setMessage("");
    try { const result = await apiCall(`/api/pos/printing/${path}`, { method: "POST", body: JSON.stringify(data) }); if (!result.response.ok) { setMessage(asApiError(result.body).message); return; } copyIntent.current = null; await load(); }
    catch { setMessage("Resultado indisponível. Atualize antes de tentar novamente."); } finally { setBusy(false); }
  }
  function edit(endpoint?: Endpoint) {
    setEditing(endpoint?.id ?? ""); setLabel(endpoint?.label ?? ""); setAdapter(endpoint?.adapter ?? "BROWSER"); setWidth(endpoint?.width_mm ?? 80); setReference(endpoint?.connection_ref ?? ""); setStations(endpoint?.stations ?? []); setEnabled(endpoint?.enabled ?? true); setCut(endpoint?.cut_supported ?? false);
  }
  return <main className="appShell"><header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div><OperationalHeading as="h1" icon="printer">Impressoras e trabalhos</OperationalHeading><Link className="backLink" href="/manage">Voltar à Gerência</Link></header>
    {message && <p className="notice" data-state="danger" role="alert">{message}</p>}
    <section className="panel"><OperationalHeading as="h2" icon="printer">Destinos</OperationalHeading><p className="muted">Estado desconhecido é válido. Envio aceito não confirma papel.</p>{endpoints.map(endpoint => <div className="dataRow" key={endpoint.id}><div><strong>{endpoint.label}</strong><p>{endpoint.adapter} · {endpoint.width_mm} mm · {endpoint.enabled ? "Ativo" : "Desativado"} · {endpoint.health}{endpoint.health_at ? ` · ${new Date(endpoint.health_at).toLocaleString("pt-BR")}` : " · sem leitura de hardware"}</p><p>Bridge: {endpoint.bridge_status}</p><p>{endpoint.stations.join(" / ") || "Documentos de cliente"}</p></div><button className="buttonSecondary" onClick={() => edit(endpoint)}>Configurar</button></div>)}<button className="buttonSecondary" onClick={() => edit()}>Novo destino</button></section>
    <form className="panel" onSubmit={event => { event.preventDefault(); void mutate("endpoints/", { ...(editing ? { id: editing } : {}), label, adapter, width_mm: width, connection_ref: reference, stations, enabled, cut_supported: cut }); }}>
      <OperationalHeading as="h2" icon="printer">{editing ? "Configurar destino" : "Novo destino"}</OperationalHeading><div className="field"><label>Nome<input required value={label} maxLength={120} onChange={e => setLabel(e.target.value)} /></label></div>
      <div className="field"><label>Saída<select value={adapter} onChange={e => setAdapter(e.target.value)}><option value="BROWSER">Navegador / Salvar PDF</option><option value="FILE">Arquivo HTML (sem papel)</option><option value="NETWORK">ESC/POS pela rede local</option><option value="SPOOL">USB / fila do computador</option></select></label></div>
      <div className="field"><label>Papel<select value={width} onChange={e => setWidth(Number(e.target.value))}><option value={58}>58 mm</option><option value={80}>80 mm</option></select></label></div>
      {adapter !== "BROWSER" && <div className="field"><label>Referência da conexão local<input value={reference} maxLength={80} onChange={e => setReference(e.target.value)} /></label><p className="muted">Use a mesma referência na configuração do bridge do computador.</p></div>}
      <div className="actions">{["BAR", "KITCHEN"].map(station => <button type="button" className="buttonSecondary" aria-pressed={stations.includes(station)} key={station} onClick={() => setStations(current => current.includes(station) ? current.filter(s => s !== station) : [...current, station])}>{station === "BAR" ? "Bar" : "Cozinha"}</button>)}<button type="button" className="buttonSecondary" aria-pressed={enabled} onClick={() => setEnabled(!enabled)}>{enabled ? "Ativo" : "Desativado"}</button><button type="button" className="buttonSecondary" aria-pressed={cut} onClick={() => setCut(!cut)}>{cut ? "Corte habilitado" : "Sem corte"}</button></div>
      <button className="buttonPrimary" disabled={busy || !label.trim()}>Salvar destino</button>
    </form>
    <section className="panel"><OperationalHeading as="h2" icon="printer">Trabalhos recentes / falhas</OperationalHeading><div className="actions"><button className="buttonSecondary" aria-pressed={failedOnly} onClick={() => { setFailedOnly(!failedOnly); setOffset(0); }}>{failedOnly ? "Mostrar todos" : "Somente falhas"}</button>{offset > 0 && <button className="buttonSecondary" onClick={() => setOffset(Math.max(0, offset - 100))}>Página anterior</button>}{nextOffset !== null && <button className="buttonSecondary" onClick={() => setOffset(nextOffset)}>Próxima página</button>}</div><div className="field"><label>Motivo para reimpressão<input value={reason} maxLength={240} onChange={e => setReason(e.target.value)} /></label></div>{jobs.map(job => <article className="panel" key={job.id}><strong>{printState[job.state] ?? job.state}</strong><p>{job.id}</p>{job.last_error && <p>{job.last_error}</p>}{job.reprint_of && <p>REIMPRESSÃO de {job.reprint_of} · {job.reason}</p>}{job.attempts.map(attempt => <p key={attempt.number}>Tentativa {attempt.number}: {printState[attempt.outcome] ?? attempt.outcome} · {attempt.detail}</p>)}<div className="actions">
      <Link className="backLink" href={`/printing/jobs/${job.id}`}>Ver documento</Link>
      {job.state === "FAILED_RETRYABLE" && <button className="buttonSecondary" disabled={busy} onClick={() => void mutate(`jobs/${job.id}/`, { action: "retry" })}>Tentar agora</button>}
      {["OUTPUT_READY", "SPOOL_ACCEPTED", "DELIVERY_UNCERTAIN"].includes(job.state) && <button className="buttonSecondary" disabled={busy} onClick={() => void mutate(`jobs/${job.id}/`, { action: "confirm" })}>Confirmar que vi o papel</button>}
      {!["SENDING", "PRINTED", "CANCELLED"].includes(job.state) && <button className="buttonSecondary" disabled={busy} onClick={() => void mutate(`jobs/${job.id}/`, { action: "cancel" })}>Cancelar trabalho</button>}
      <button className="buttonSecondary" disabled={busy || !reason.trim() || job.state === "SENDING"} onClick={() => { if (copyIntent.current?.jobId !== job.id) copyIntent.current = { jobId: job.id, key: crypto.randomUUID() }; void mutate(`jobs/${job.id}/`, { action: "reprint", reason, idempotency_key: copyIntent.current.key }); }}>Reimprimir cópia</button>
    </div></article>)}</section>
  </main>;
}
