"use client";

import { OperationalHeading } from "@/components/operational-heading";
import { useEffect, useState } from "react";
import Link from "next/link";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
type Policy = { version: number; service_treatment: string; [key: string]: number | boolean | string };
type Approval = { id: string; label: string; requester: string; command: { kind: string; reason_code: string }; preview: { before_payable_cents: number; after_payable_cents: number } };
const labels: Record<string, string> = { service_enabled: "Cobrar serviço", service_basis_points: "Serviço padrão (%)", service_max_basis_points: "Serviço máximo (%)", service_opt_out: "Permitir retirada por pedido do cliente", service_removal_requires_manager: "Exigir gerência para retirada fora do opt-out", service_refundable: "Incluir serviço na ajuda de estorno", staff_discount_basis_points: "Desconto máximo do atendimento (%)", cashier_discount_basis_points: "Desconto máximo do caixa (%)", maximum_discount_basis_points: "Desconto máximo da gerência (%)", allow_post_payment: "Permitir ajustes após pagamento parcial" };
export default function PricingManagement() {
  const [policy, setPolicy] = useState<Policy | null>(null), [approvals, setApprovals] = useState<Approval[]>([]), [pin, setPin] = useState(""), [message, setMessage] = useState(""), [busy, setBusy] = useState(false);
  const load = async () => { const [p, a] = await Promise.all([apiCall<Policy>("/api/pos/pricing/policy/"), apiCall<{ results: Approval[] }>("/api/pos/pricing/approvals/")]); if (p.response.ok) setPolicy(p.body as Policy); else setMessage(asApiError(p.body).message); if (a.response.ok) setApprovals((a.body as { results: Approval[] }).results); };
  useEffect(() => { void load(); }, []);
  const perform = async (url: string, data: unknown, method = "POST") => {
    setBusy(true); setMessage("");
    try {
      const auth = await apiCall("/api/auth/reauthenticate", { method: "POST", body: JSON.stringify({ pin }) }); setPin("");
      if (!auth.response.ok) { setMessage(asApiError(auth.body).message); return; }
      const result = await apiCall(url, { method, body: JSON.stringify(data) });
      setMessage(result.response.ok ? "Confirmado." : asApiError(result.body).message); await load();
    } catch { setMessage("Sem confirmação. Atualize antes de continuar."); } finally { setBusy(false); }
  };
  return <main className="appShell"><header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div><OperationalHeading as="h1" icon="settings">Preços e serviço</OperationalHeading><Link className="backLink" href="/manage">Voltar à gerência</Link></header>{message && <p className="notice" role="status">{message}</p>}
    <section className="panel"><OperationalHeading as="h2" icon="settings">Política do estabelecimento</OperationalHeading><p>Alterações valem para novos ajustes. Avaliações já aplicadas preservam a política original.</p>{policy && <>{Object.entries(labels).map(([key, label]) => <div className="field" key={key}><label htmlFor={`policy-${key}`}>{label}</label>{typeof policy[key] === "boolean" ? <input id={`policy-${key}`} type="checkbox" checked={policy[key] as boolean} onChange={e => setPolicy({ ...policy, [key]: e.target.checked })} /> : <input id={`policy-${key}`} type="number" min={0} max={100} step="0.01" value={(policy[key] as number) / 100} onChange={e => { const [whole, fraction = ""] = e.target.value.split("."); setPolicy({ ...policy, [key]: Number(whole || "0") * 100 + Number(fraction.padEnd(2, "0").slice(0, 2)) }); }} />}</div>)}<div className="field"><label htmlFor="service-treatment">Tratamento operacional do serviço</label><select id="service-treatment" value={policy.service_treatment} onChange={e => setPolicy({ ...policy, service_treatment: e.target.value })}><option value="PASS_THROUGH">Valor a repassar</option><option value="REVENUE">Receita do estabelecimento</option></select></div></>}
      <div className="field"><label htmlFor="manager-pin">PIN da gerência</label><input id="manager-pin" type="password" inputMode="numeric" autoComplete="off" value={pin} onChange={e => setPin(e.target.value)} /></div><button className="buttonPrimary" disabled={busy || !policy || !pin} onClick={() => { if (policy) { const { version, ...values } = policy; void perform("/api/pos/pricing/policy/", { ...values, expected_version: version }, "PUT"); } }}>Salvar política</button></section>
    <section className="panel"><OperationalHeading as="h2" icon="settings">Solicitações de ajuste</OperationalHeading><button className="buttonQuiet" onClick={() => void load()}>Atualizar solicitações</button>{!approvals.length && <p>Nenhuma solicitação pendente.</p>}{approvals.map(a => <div className="panel" key={a.id}><h3>{a.label || "Comanda"}</h3><p>{a.requester} · {a.command.kind} · {a.command.reason_code}</p><p>Antes R$ {(a.preview.before_payable_cents / 100).toFixed(2)} → depois R$ {(a.preview.after_payable_cents / 100).toFixed(2)}</p><button className="buttonPrimary" disabled={busy || !pin} onClick={() => void perform(`/api/pos/pricing/approvals/${a.id}/approve/`, {})}>Aprovar com PIN</button></div>)}</section>
  </main>;
}
