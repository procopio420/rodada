"use client";
import { useCallback, useEffect, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { OperationalHeading } from "@/components/operational-heading";

type Printer = { driver_name: string; id: string; label: string; agent_id: string; queue_name: string; transport: string; health: string; last_seen_at: string; config_fingerprint: string };
type Route = { id: string; endpoint_id: string; printer_id: string; transport: string; profile_id: string; destination: string; port: number; enabled: boolean; version: number; raw_escpos_verified: boolean };
type Inventory = { printers: Printer[]; routes: Route[] };
type Endpoint = { id: string; label: string; adapter: string };
const path = "/api/pos/printing/agents/v1/routes/";
export function PrintAgentRoutes({ endpoints }: { endpoints: Endpoint[] }) {
  const [data, setData] = useState<Inventory>({ printers: [], routes: [] });
  const [inspected, setInspected] = useState("");
  const [editing, setEditing] = useState<Route | null>(null);
  const [endpoint, setEndpoint] = useState(""), [printer, setPrinter] = useState("");
  const [profile, setProfile] = useState("escpos-ascii-v1");
  const [raw, setRaw] = useState(false), [verified, setVerified] = useState(false), [enabled, setEnabled] = useState(false);
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [message, setMessage] = useState("");
  const load = useCallback(async () => {
    const response = await apiCall<Inventory>(path);
    if (!response.response.ok) throw new Error(asApiError(response.body).message);
    setData(response.body as Inventory);
  }, []);
  useEffect(() => {
    const refresh = () => { void load().catch(() => setError("Não foi possível consultar impressoras e rotas.")); };
    refresh(); const timer = window.setInterval(refresh, 10000);
    return () => window.clearInterval(timer);
  }, [load]);
  const selected = data.printers.find(row => row.id === printer);
  const changed = !!selected && inspected !== selected.config_fingerprint;
  function inspectPrinter() {
    if (editing) edit(data.routes.find(row => row.id === editing.id) ?? null);
    else { setInspected(selected?.config_fingerprint ?? ""); setVerified(false); }
    setMessage(""); setError("");
  }
  function edit(route: Route | null) {
    setInspected(data.printers.find(row => row.id === route?.printer_id)?.config_fingerprint ?? "");
    setEditing(route); setEndpoint(route?.endpoint_id ?? ""); setPrinter(route?.printer_id ?? "");
    setProfile(route?.profile_id.startsWith("escpos-") ? route.profile_id : "escpos-ascii-v1"); setRaw(route?.profile_id.startsWith("escpos-") ?? false); setVerified(route?.raw_escpos_verified ?? false); setEnabled(route?.enabled ?? false);
  }
  async function save() {
    if (!selected || busy || changed) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const tcp = selected.transport === "TCP_LAN";
      const response = await apiCall<Route>(path, { method: "POST", body: JSON.stringify({
        ...(editing ? { id: editing.id } : {}), expected_version: editing?.version ?? 0,
        endpoint_id: endpoint, printer_id: printer, printer_fingerprint: inspected, enabled,
        transport: tcp ? "TCP_LAN" : raw ? "WINDOWS_RAW" : "WINDOWS_DRIVER",
        profile_id: raw || tcp ? profile : "windows-driver-v1",
        destination: selected.queue_name, port: 9100, raw_escpos_verified: verified,
      }) });
      if (!response.response.ok) throw new Error(asApiError(response.body).message);
      await load(); edit(response.body as Route); setMessage("Rota salva. Envio aceito não confirma papel impresso.");
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Confirmação indisponível. Confira as rotas antes de repetir.");
      await load().catch(() => {});
    } finally { setBusy(false); }
  }
  return <section className="panel" aria-label="Rotas dos computadores">
    <OperationalHeading as="h2" icon="printer">Impressoras dos computadores</OperationalHeading>
    <p>As filas são descobertas pelo serviço. Computador conectado, fila acessível e papel impresso são estados diferentes.</p>
    {error && <p className="notice" role="alert" data-state="danger">{error}</p>}
    {message && <p className="notice" role="status">{message}</p>}
    {data.printers.length === 0 && <p>Nenhuma fila descoberta. Confira o serviço e as permissões da impressora no Windows.</p>}
    {data.routes.map(route => <div className="dataRow" key={route.id}><span>{endpoints.find(row => row.id === route.endpoint_id)?.label} · {route.enabled ? "Rota habilitada" : "Rota desabilitada"} · versão {route.version}</span><button className="buttonSecondary" disabled={busy} onClick={() => edit(route)}>Editar rota</button></div>)}
    <form onSubmit={event => { event.preventDefault(); void save(); }}>
      <div className="field"><label>Destino lógico<select value={endpoint} disabled={busy || !!editing} required onChange={event => setEndpoint(event.target.value)}><option value="">Selecione</option>{endpoints.filter(row => row.adapter === "AGENT").map(row => <option key={row.id} value={row.id}>{row.label}</option>)}</select></label></div>
      <div className="field"><label>Fila descoberta<select value={printer} disabled={busy || !!editing} required onChange={event => { setPrinter(event.target.value); setInspected(data.printers.find(row => row.id === event.target.value)?.config_fingerprint ?? ""); setVerified(false); }}><option value="">Selecione</option>{data.printers.map(row => <option key={row.id} value={row.id}>{row.label} · {row.health === "UNKNOWN" ? "estado não confirmado" : row.health}</option>)}</select></label></div>
      {selected && <p>Fila: {selected.queue_name} · Driver: {selected.driver_name || "não informado"}</p>}
      {changed && <><p role="alert" className="notice" data-state="warning">A fila ou o driver mudou. Revise os dados e confirme a compatibilidade novamente.</p><button className="buttonSecondary" type="button" disabled={busy} onClick={inspectPrinter}>Revisar dados da impressora</button></>}
      <label className="printingRouteChoice"><input type="checkbox" checked={raw} disabled={busy || selected?.transport === "TCP_LAN"} onChange={event => { setRaw(event.target.checked); setVerified(false); }} /> Usar ESC/POS RAW em vez do driver Windows</label>
      {(raw || selected?.transport === "TCP_LAN") && <div className="field"><label>Perfil ESC/POS<select value={profile} disabled={busy || changed} onChange={event => { setProfile(event.target.value); setVerified(false); }}><option value="escpos-ascii-v1">ASCII sem acentos · sem corte</option><option value="escpos-pc860-v1">Português PC860 · sem corte</option><option value="escpos-pc860-cut-v1">Português PC860 · corte completo</option></select></label><p>PC860 requer agente 0.5.0. Caracteres sem representação viram ?. Bematech MP-4200 TH: validar este perfil na impressora real.</p></div>}
      {(raw || selected?.transport === "TCP_LAN") && <label className="printingRouteChoice"><input type="checkbox" checked={verified && !changed} disabled={busy || changed} onChange={event => setVerified(event.target.checked)} /> Confirmei em teste físico que esta conexão aceita o perfil ESC/POS RAW selecionado, seus acentos e a opção de corte. QR e status permanecem desativados.</label>}
      <label className="printingRouteChoice"><input type="checkbox" checked={enabled} disabled={busy} onChange={event => setEnabled(event.target.checked)} /> Habilitar esta rota</label>
      <button className="buttonPrimary" disabled={busy || changed || !endpoint || !selected || ((raw || selected.transport === "TCP_LAN") && !verified)}>Salvar rota</button>
      {editing && <button className="buttonQuiet" type="button" disabled={busy} onClick={() => edit(null)}>Nova rota</button>}
    </form>
  </section>;
}
