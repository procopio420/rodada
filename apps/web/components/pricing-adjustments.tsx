"use client";

import { OperationalHeading } from "@/components/operational-heading";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";

type History = { id: string; kind: string; amount_cents: number; reason_code: string };
type Pricing = { version: number; policy: { service_basis_points: number }; history: History[]; charges: { charge_id: string; product_name?: string; gross: number }[] };
type Preview = { before_payable_cents: number; after_payable_cents: number; after_remaining_cents: number; approval_required: boolean };
const labels: Record<string, string> = { TAB_DISCOUNT: "Desconto na comanda", ITEM_DISCOUNT: "Desconto no item", COURTESY: "Cortesia", SERVICE_CHARGE: "Calcular / atualizar serviço", SERVICE_CHARGE_REDUCTION: "Reduzir / remover serviço", REVERSAL: "Reverter ajuste" };
const money = (v: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v / 100);
export function PricingAdjustments({ tabId, version, onChanged }: { tabId: string; version: number; onChanged: () => Promise<void> }) {
  const [pricing, setPricing] = useState<Pricing | null>(null), [kind, setKind] = useState("TAB_DISCOUNT"), [calculation, setCalculation] = useState("FIXED"), [value, setValue] = useState(""), [charge, setCharge] = useState(""), [adjustment, setAdjustment] = useState(""), [reason, setReason] = useState(""), [pin, setPin] = useState(""), [message, setMessage] = useState(""), [preview, setPreview] = useState<Preview | null>(null), [busy, setBusy] = useState(false), [awaiting, setAwaiting] = useState(false);
  const intent = useRef<Record<string, unknown> | null>(null);
  const recoveryKey = useRef<string | null>(null);
  const load = useCallback(async () => { const r = await apiCall<Pricing>(`/api/pos/tabs/${tabId}/pricing/`); if (r.response.ok) {
      setPricing(r.body as Pricing);
      if (!recoveryKey.current) {
        const me = await apiCall<{ staff: { id: string }; venue: { id: string } }>("/api/auth/me");
        if (me.response.ok) {
          const actor = me.body as { staff: { id: string }; venue: { id: string } };
          recoveryKey.current = `rodada-pricing:${actor.venue.id}:${actor.staff.id}:${tabId}`;
          try { const saved = sessionStorage.getItem(recoveryKey.current); if (saved) { const recovered = JSON.parse(saved) as { command: Record<string, unknown>; preview: Preview }; intent.current = recovered.command; setAwaiting(true); setPreview(recovered.preview); setMessage("Há um ajuste aguardando confirmação. Verifique esta mesma operação."); } } catch { setMessage("Confira os ajustes anteriores antes de continuar."); }
        }
      }
    } else setMessage(asApiError(r.body).message); }, [tabId]);
  useEffect(() => { void load(); }, [load, version]);
  const clear = () => { setAwaiting(false); setPreview(null); intent.current = null; if (recoveryKey.current) sessionStorage.removeItem(recoveryKey.current); };
  const prepare = async () => {
    if (!pricing || busy) return;
    const isService = kind === "SERVICE_CHARGE", isReversal = kind === "REVERSAL";
    const raw = value.trim().replace(",", ".");
    if (!isReversal && !isService && !/^\d+(\.\d{1,2})?$/.test(raw)) { setMessage("Informe um valor com até duas casas decimais."); return; }
    // Parse decimal text into cents / basis points without binary floating point.
    const [whole, fraction = ""] = raw.split(".");
    const parsed = Number(whole || "0") * 100 + Number(fraction.padEnd(2, "0"));
    const data = { kind, expected_version: pricing.version, idempotency_key: crypto.randomUUID(), reason_code: reason,
      ...(isReversal ? { adjustment_id: adjustment } : { value: isService && !raw ? pricing.policy.service_basis_points : parsed, calculation_type: isService ? "PERCENTAGE" : kind === "SERVICE_CHARGE_REDUCTION" ? "FIXED" : calculation }),
      ...(charge && (kind === "ITEM_DISCOUNT" || kind === "COURTESY") ? { charge_id: charge } : {}) };
    setBusy(true); setMessage("");
    try { const r = await apiCall<Preview>(`/api/pos/tabs/${tabId}/pricing/preview/`, { method: "POST", body: JSON.stringify(data) }); if (r.response.ok) { intent.current = data; setPreview(r.body as Preview); } else { setMessage(asApiError(r.body).message); await load(); } }
    catch { setMessage("Sem conexão. Confira a conta antes de ajustar."); } finally { setBusy(false); }
  };
  const commit = async () => {
    if (!intent.current || busy) return;
    setBusy(true);
    try {
      if (recoveryKey.current) sessionStorage.setItem(recoveryKey.current, JSON.stringify({ command: intent.current, preview }));
      if (pin) { const auth = await apiCall("/api/auth/reauthenticate", { method: "POST", body: JSON.stringify({ pin }) }); setPin(""); if (!auth.response.ok) { setMessage(asApiError(auth.body).message); return; } }
      setAwaiting(true);
      const r = await apiCall(`/api/pos/tabs/${tabId}/pricing/${preview?.approval_required ? "approval-request/" : ""}`, { method: "POST", body: JSON.stringify(intent.current) });
      if (r.response.ok) { setMessage(preview?.approval_required ? "Solicitação enviada à gerência." : "Ajuste aplicado."); clear(); await onChanged(); await load(); }
      else { if (r.response.status >= 400 && r.response.status < 500) setAwaiting(false); setMessage(asApiError(r.body).message); if (asApiError(r.body).code === "VERSION_CONFLICT") { clear(); await load(); } }
    } catch { setMessage("Resposta não confirmada. Tente novamente para verificar o mesmo ajuste."); } finally { setBusy(false); }
  };
  return <section className="panel"><OperationalHeading as="h2" icon="wallet">Ajustar conta</OperationalHeading>{message && <p role="status" className="notice">{message}</p>}<div className="field"><label htmlFor="pricing-kind">Ação</label><select id="pricing-kind" value={kind} disabled={busy || !!preview} onChange={e => { setKind(e.target.value); clear(); }}>{Object.entries(labels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></div>
    {(kind === "ITEM_DISCOUNT" || kind === "COURTESY") && <div className="field"><label htmlFor="pricing-item">Item / consumo</label><select id="pricing-item" value={charge} disabled={!!preview} onChange={e => setCharge(e.target.value)}><option value="">Comanda inteira (cortesia)</option>{pricing?.charges.map(row => <option key={row.charge_id} value={row.charge_id}>{row.product_name || row.charge_id.slice(0, 8)} · {money(row.gross)}</option>)}</select></div>}
    {kind === "REVERSAL" ? <div className="field"><label htmlFor="pricing-reversal">Ajuste original</label><select id="pricing-reversal" value={adjustment} disabled={!!preview} onChange={e => setAdjustment(e.target.value)}><option value="">Selecione</option>{pricing?.history.filter(row => !["REVERSAL", "SERVICE_CHARGE"].includes(row.kind)).map(row => <option key={row.id} value={row.id}>{labels[row.kind] || row.kind} · {money(row.amount_cents)}</option>)}</select></div> : <><div className="field"><label htmlFor="pricing-calculation">Tipo de valor</label><select id="pricing-calculation" value={kind === "SERVICE_CHARGE" ? "PERCENTAGE" : kind === "SERVICE_CHARGE_REDUCTION" ? "FIXED" : calculation} disabled={!!preview || kind.startsWith("SERVICE")} onChange={e => setCalculation(e.target.value)}><option value="FIXED">Valor em reais</option><option value="PERCENTAGE">Percentual</option></select></div><div className="field"><label htmlFor="pricing-value">{kind === "SERVICE_CHARGE" || (kind !== "SERVICE_CHARGE_REDUCTION" && calculation === "PERCENTAGE") ? "Percentual (%)" : "Valor (R$)"}</label><input id="pricing-value" inputMode="decimal" value={value} disabled={!!preview} placeholder={kind === "SERVICE_CHARGE" ? `Padrão: ${(pricing?.policy.service_basis_points ?? 0) / 100}%` : "0,00"} onChange={e => setValue(e.target.value)} /></div></>}
    <div className="field"><label htmlFor="pricing-reason">Motivo</label><input id="pricing-reason" value={reason} maxLength={80} disabled={!!preview} onChange={e => setReason(e.target.value)} /></div>
    {preview ? <><p>Antes {money(preview.before_payable_cents)} → depois {money(preview.after_payable_cents)}. Saldo {money(preview.after_remaining_cents)}.</p>{!preview.approval_required && <div className="field"><label htmlFor="pricing-pin">PIN para ação gerencial</label><input id="pricing-pin" type="password" inputMode="numeric" autoComplete="off" value={pin} onChange={e => setPin(e.target.value)} /></div>}<button className="buttonPrimary" disabled={busy} onClick={() => void commit()}>{preview.approval_required ? "Solicitar aprovação" : "Confirmar ajuste"}</button><button className="buttonQuiet" disabled={busy || awaiting} onClick={clear}>Voltar</button></> : <button className="buttonSecondary" disabled={busy || !pricing} onClick={() => void prepare()}>Conferir antes de aplicar</button>}
    {pricing?.history.map(row => <div className="dataRow" key={row.id}><span>{labels[row.kind] || row.kind} {row.reason_code}</span><strong>{money(row.amount_cents)}</strong></div>)}
  </section>;
}
