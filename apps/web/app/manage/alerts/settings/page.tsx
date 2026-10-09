"use client";

import { OperationalHeading } from "@/components/operational-heading";
import Link from "next/link";
import { FormEvent, useCallback, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { useRealtime } from "@/lib/client/use-realtime";
import { ConnectivityNotice } from "@/components/connectivity-notice";
type Policy = { version: number; fulfillment_warning_seconds: number; fulfillment_danger_seconds: number; payment_pending_seconds: number; guest_request_warning_seconds: number; guest_request_danger_seconds: number };
export default function AlertSettings() {
  const [policy, setPolicy] = useState<Policy>();
  const [pin, setPin] = useState("");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState<Policy>();
  const load = useCallback(async () => {
    const result = await apiCall<Policy>("/api/pos/management/alert-policy/");
    if (!result.response.ok) { setMessage(asApiError(result.body).message); throw new Error("Configuração indisponível."); }
    setPolicy(result.body as Policy);
    // Server refresh does not overwrite an editor's unsaved changes.
    setDraft(value => value ?? result.body as Policy);
  }, []);
  const connectivity = useRealtime(load, { onRevoked: () => { setPolicy(undefined); setDraft(undefined); setPin(""); setMessage("Entre novamente."); } });
  async function save(event: FormEvent) {
    event.preventDefault();
    if (!draft || saving || connectivity.state === "OFFLINE") return;
    setSaving(true); setMessage("");
    try {
      const reauth = await apiCall("/api/auth/reauthenticate", { method: "POST", body: JSON.stringify({ pin }) });
      setPin("");
      if (!reauth.response.ok) throw new Error(asApiError(reauth.body).message);
      const result = await apiCall<Policy & { current?: Policy }>("/api/pos/management/alert-policy/", { method: "PATCH", body: JSON.stringify({
        expected_version: draft.version, fulfillment_warning_seconds: draft.fulfillment_warning_seconds,
        fulfillment_danger_seconds: draft.fulfillment_danger_seconds, payment_pending_seconds: draft.payment_pending_seconds,
        guest_request_warning_seconds: draft.guest_request_warning_seconds, guest_request_danger_seconds: draft.guest_request_danger_seconds, reason,
      }) });
      if (result.response.status === 409) {
        const current = (result.body as { current: Policy }).current;
        setPolicy(current); setDraft(current);
        setMessage("Outra pessoa alterou a política. Estado atual carregado; revise antes de salvar novamente.");
        return;
      }
      if (!result.response.ok) throw new Error(asApiError(result.body).message);
      setPolicy(result.body as Policy); setDraft(result.body as Policy);
      setMessage("Política confirmada pelo servidor. Em vigor agora para avaliação de alertas.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Não foi possível salvar."); }
    finally { setSaving(false); }
  }
  return <main className="appShell managementShell">
    <header className="productHeader"><div className="eyebrow">RODADA / GESTÃO</div><OperationalHeading as="h1" icon="warning">Alertas e SLAs</OperationalHeading><Link className="backLink" href="/manage">Voltar à operação →</Link></header>
    <ConnectivityNotice {...connectivity} />
    {message && <p className="notice" role="status">{message}</p>}
    {policy && draft && <form className="panel" onSubmit={event => void save(event)}>
      <OperationalHeading as="h2" icon="warning">Limites operacionais</OperationalHeading><p className="muted">Versão {draft.version}. Entra em vigor agora após confirmação. Não altera estados ou timestamps dos pedidos.</p>
      {([
        ["fulfillment_warning_seconds", "Produção: atenção após (segundos)"],
        ["fulfillment_danger_seconds", "Produção: crítico após (segundos)"],
        ["payment_pending_seconds", "Pagamento sem confirmação após (segundos)"],
        ["guest_request_warning_seconds", "Atendimento: atenção após (segundos)"],
        ["guest_request_danger_seconds", "Atendimento: crítico após (segundos)"],
      ] as const).map(([key, label]) => <label className="field" key={key}><span>{label}</span><input type="number" min={1} max={key.endsWith("danger_seconds") ? 172800 : 86400} required value={draft[key]} disabled={saving} onChange={event => setDraft({ ...draft, [key]: Number(event.target.value) })} /></label>)}
      <label className="field"><span>Motivo da alteração</span><input maxLength={240} value={reason} disabled={saving} onChange={event => setReason(event.target.value)} /></label>
      <label className="field"><span>Confirme seu PIN</span><input type="password" inputMode="numeric" autoComplete="off" maxLength={12} value={pin} disabled={saving} onChange={event => setPin(event.target.value)} required /></label>
      <button className="buttonPrimary" type="submit" disabled={saving || connectivity.state === "OFFLINE"}>{saving ? "Confirmando…" : "Salvar política"}</button>
    </form>}
  </main>;
}
