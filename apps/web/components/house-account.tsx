"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiCall, asApiError, StaffSessionView } from "@/lib/client/staff-auth";

type Tab = { id: string; display_label: string; state: string; exposure_cents: number;
  effective_limit_cents: number; remaining_capacity_cents: number; action_reasons: string[];
  override_expires_at: string | null; customer_id: string | null; approval_requested: boolean };
type Customer = { id: string; display_name: string; phone: string; kind: string };
type Audit = { id: string; event_type: string; actor: string | null; actor_name: string; reason: string;
  occurred_at: string; metadata: Record<string, unknown> };
type Policy = { kind: string; limit_cents: number; version: number };
const money = (cents: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);
const kinds = ["VISITOR", "KNOWN", "REGULAR", "HOUSE", "RESTRICTED"];
const labels: Record<string, string> = { VISITOR: "Visitante", KNOWN: "Conhecido", REGULAR: "Regular", HOUSE: "Da casa", RESTRICTED: "Restrito",
  SPENDING_LIMIT: "Limite de consumo atingido", REFUND_REQUIRED: "Estorno pendente", OTHER_ACTION_REQUIRED: "Outra ação pendente" };

class ApiFailure extends Error {
  constructor(message: string, readonly status: number) { super(message); }
}

const eventLabels: Record<string, string> = {
  "tab.limit_overridden": "Limite temporário aprovado", "tab.policy_reassessed": "Política reavaliada",
  "tab.limit_approval_requested": "Aprovação solicitada", "tab.customer_associated": "Cliente associado",
  "tab.attention_changed": "Atenção atualizada", "guest_tab.created": "Comanda aberta pelo cliente",
  "tab.opened": "Comanda aberta", "tab.house_policy_migrated": "Política inicial aplicada",
  "tab.closed": "Comanda fechada",
};

function decisionDetails(metadata: Record<string, unknown>): string {
  const parts: string[] = [];
  if (typeof metadata.previous_limit_cents === "number" && typeof metadata.limit_cents === "number") {
    parts.push(`${money(metadata.previous_limit_cents)} → ${money(metadata.limit_cents)}`);
  }
  if (typeof metadata.expires_at === "string") parts.push(`Válido até ${new Date(metadata.expires_at).toLocaleString("pt-BR")}`);
  if (typeof metadata.exposure_cents === "number") parts.push(`Em aberto ${money(metadata.exposure_cents)}`);
  const before = metadata.before as { kind?: string; limit_cents?: number } | undefined;
  const after = metadata.after as { kind?: string; limit_cents?: number } | undefined;
  if (before?.kind && after?.kind && typeof before.limit_cents === "number" && typeof after.limit_cents === "number") {
    parts.push(`${labels[before.kind] || before.kind} ${money(before.limit_cents)} → ${labels[after.kind] || after.kind} ${money(after.limit_cents)}`);
  }
  return parts.join(" · ");
}

async function call<T>(path: string, body?: unknown, method = "POST"): Promise<T> {
  const result = await apiCall<T>(path, body === undefined ? undefined : { method, body: JSON.stringify(body) });
  if (!result.response.ok) throw new ApiFailure(asApiError(result.body).message, result.response.status);
  return result.body as T;
}

async function activeTabs(): Promise<Tab[]> {
  const tabs: Tab[] = [];
  let offset: number | null = 0;
  while (offset !== null) {
    const page: { results: Tab[]; next_offset: number | null } = await call(`/api/pos/tabs/?active=true&offset=${offset}`);
    tabs.push(...page.results); offset = page.next_offset;
  }
  return [...new Map(tabs.map(tab => [tab.id, tab])).values()];
}

export function HouseAccount() {
  const [tabs, setTabs] = useState<Tab[]>([]);
  const [session, setSession] = useState<StaffSessionView | null>(null);
  const [selected, setSelected] = useState<Tab | null>(null);
  const [history, setHistory] = useState<Audit[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [query, setQuery] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [kind, setKind] = useState("KNOWN");
  const [amount, setAmount] = useState("");
  const [policyAmount, setPolicyAmount] = useState("");
  const [reason, setReason] = useState("");
  const [pin, setPin] = useState("");
  const [minutes, setMinutes] = useState("60");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [stale, setStale] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [visits, setVisits] = useState<Tab[]>([]);
  const overrideIntent = useRef<{ key: string; limit_cents: number; expires_at: string; reason: string } | null>(null);
  const actorContext = useRef("");
  const canApprove = session?.capabilities.includes("tab.limit.override");
  const canManage = session?.capabilities.includes("customer.manage");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [me, data] = await Promise.all([call<StaffSessionView>("/api/auth/me"), activeTabs()]);
      const key = `${me.venue.id}:${me.staff.id}:${me.session.id}`;
      if (actorContext.current && actorContext.current !== key) {
        setPin(""); setSelected(null); setHistory([]); setCustomers([]); setVisits([]);
        overrideIntent.current = null;
      }
      actorContext.current = key;
      setSession(me); setTabs(data); setStale(false); setError("");
    } catch (failure) { setStale(true); setError(failure instanceof Error ? failure.message : "Falha ao atualizar comandas."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => {
    void load();
    const offline = () => setStale(true);
    const timer = window.setInterval(() => { if (document.visibilityState === "visible") void load(); }, 15000);
    window.addEventListener("online", load); window.addEventListener("focus", load); window.addEventListener("offline", offline);
    return () => { clearInterval(timer); window.removeEventListener("online", load); window.removeEventListener("focus", load); window.removeEventListener("offline", offline); };
  }, [load]);
  useEffect(() => {
    if (selected) setSelected(tabs.find(t => t.id === selected.id) ?? null);
  }, [tabs, selected]);

  async function action(work: () => Promise<void>) {
    setBusy(true); setError(""); setNotice("");
    try { await work(); setNotice("Alteração confirmada. Estado atualizado."); await load(); }
    catch (failure) { setError(failure instanceof Error ? failure.message : "Falha na operação. Atualize antes de repetir."); }
    finally { setBusy(false); setPin(""); }
  }
  async function reauth() { await call("/api/auth/reauthenticate", { pin }); }
  async function inspect(tab: Tab) {
    setSelected(tab); setHistory([]); setReason(""); setAmount(""); overrideIntent.current = null;
    await action(async () => { const data = await call<{ results: Audit[] }>(`/api/pos/tabs/${tab.id}/house-history/`); setHistory(data.results); });
  }
  async function approve() {
    if (!selected) return;
    await action(async () => {
      await reauth();
      const cents = Number(amount);
      if (!Number.isSafeInteger(cents) || cents <= 0 || !Number.isFinite(Number(minutes))) throw new Error("Informe limite em centavos e validade.");
      const intent = overrideIntent.current ?? { key: crypto.randomUUID(), limit_cents: cents,
        reason, expires_at: new Date(Date.now() + Number(minutes) * 60000).toISOString() };
      overrideIntent.current = intent;
      try {
        await call(`/api/pos/tabs/${selected.id}/limit-override/`, { ...intent, idempotency_key: intent.key });
      } catch (failure) {
        if (failure instanceof ApiFailure && failure.status < 500) overrideIntent.current = null;
        throw failure;
      }
      overrideIntent.current = null;
      const data = await call<{ results: Audit[] }>(`/api/pos/tabs/${selected.id}/house-history/`); setHistory(data.results);
    });
  }

  return <section className="panel" aria-label="Conta da casa">
    <h2>Conta da casa</h2>
    {loading && <p role="status">Atualizando limites…</p>}
    {stale && <div className="notice" data-state="warning">Dados desatualizados. Atualize a conexão antes de aprovar consumo.</div>}
    {error && <div className="notice" data-state="danger" role="alert">{error}</div>}
    {notice && <p role="status">{notice}</p>}
    <button className="buttonQuiet" disabled={loading || busy} onClick={() => void load()}>Atualizar comandas</button>
    {tabs.filter(t => t.state === "REQUIRES_ACTION" || t.approval_requested).map(tab => <div className="movement" key={tab.id}>
      <div><strong>{tab.display_label || "Comanda sem nome"}</strong><small>{tab.action_reasons.map(r => labels[r] || r).join(" · ")}</small>
        <small>Em aberto {money(tab.exposure_cents)} · limite {money(tab.effective_limit_cents)} · disponível {money(tab.remaining_capacity_cents)}</small></div>
      {tab.approval_requested && <span className="muted">Aprovação solicitada</span>}
      {canApprove && <button className="buttonQuiet" disabled={busy || stale} onClick={() => void inspect(tab)}>Resolver</button>}
    </div>)}
    {canApprove && <div className="field"><label htmlFor="house-tab">Inspecionar comanda</label><select id="house-tab" disabled={stale || busy} value={selected?.id || ""} onChange={e => { const tab = tabs.find(t => t.id === e.target.value); if (tab) void inspect(tab); }}>
      <option value="">Selecione</option>{tabs.filter(t => ["OPEN", "REQUIRES_ACTION"].includes(t.state)).map(t => <option value={t.id} key={t.id}>{t.display_label || t.id}</option>)}</select></div>}
    {selected && canApprove && <>
      <h3>{selected.display_label || "Comanda sem nome"}</h3>
      <div className="dataRow"><span>Limite efetivo</span><strong>{money(selected.effective_limit_cents)}</strong></div>
      <div className="dataRow"><span>Capacidade disponível</span><strong>{money(selected.remaining_capacity_cents)}</strong></div>
      {selected.override_expires_at && <p>Válido até {new Date(selected.override_expires_at).toLocaleString("pt-BR")}</p>}
      <p className="muted">Receba um pagamento parcial no Atendimento ou aprove um limite temporário. A aprovação operacional não registra pagamento ou garantia financeira.</p>
      <div className="field"><label htmlFor="house-limit">Novo limite total (centavos)</label><input id="house-limit" type="number" min="1" value={amount} disabled={busy || stale || !!overrideIntent.current} onChange={e => setAmount(e.target.value)} /></div>
      <div className="field"><label htmlFor="house-minutes">Validade (minutos, até 1440)</label><input id="house-minutes" type="number" min="1" max="1440" value={minutes} disabled={busy || stale || !!overrideIntent.current} onChange={e => setMinutes(e.target.value)} /></div>
      <div className="field"><label htmlFor="house-reason">Motivo</label><input id="house-reason" maxLength={240} value={reason} disabled={busy || stale || !!overrideIntent.current} onChange={e => setReason(e.target.value)} /></div>
      <div className="field"><label htmlFor="house-pin">Seu PIN de aprovação</label><input id="house-pin" type="password" autoComplete="off" value={pin} disabled={busy || stale} onChange={e => setPin(e.target.value)} /></div>
      <div className="actions"><button className="buttonPrimary" disabled={busy || stale || !pin || !reason || !amount} onClick={() => void approve()}>{busy ? "Confirmando…" : "Aprovar limite temporário"}</button>
      <button className="buttonQuiet" disabled={busy || stale || !pin || !reason || !!overrideIntent.current} onClick={() => void action(async () => { await reauth(); await call(`/api/pos/tabs/${selected.id}/reassess-policy/`, { reason }); })}>Reavaliar com política atual</button></div>
      <h3>Histórico de decisões</h3>{history.map(event => <div className="movement" key={event.id}><div><strong>{eventLabels[event.event_type] || "Decisão registrada"}</strong><small>{event.reason} · {event.actor_name}</small><small>{decisionDetails(event.metadata)}</small></div><time>{new Date(event.occurred_at).toLocaleString("pt-BR")}</time></div>)}
    </>}
    {canManage && <>
      <h3>Clientes e relacionamento</h3>
      <div className="field"><label htmlFor="house-search">Buscar nome ou telefone</label><input id="house-search" value={query} onChange={e => setQuery(e.target.value)} /></div>
      <button className="buttonQuiet" disabled={busy || stale} onClick={() => void action(async () => { const data = await call<{ results: Customer[] }>(`/api/pos/customers/?q=${encodeURIComponent(query)}`); setCustomers(data.results); })}>Buscar</button>
      <div className="field"><label htmlFor="house-name">Nome do novo cliente</label><input id="house-name" value={customerName} onChange={e => setCustomerName(e.target.value)} /></div>
      <div className="field"><label htmlFor="house-kind">Relacionamento</label><select id="house-kind" value={kind} onChange={e => setKind(e.target.value)}>{kinds.map(k => <option value={k} key={k}>{labels[k]}</option>)}</select></div>
      <div className="field"><label htmlFor="house-customer-pin">Seu PIN para alterar relacionamento/política</label><input id="house-customer-pin" type="password" autoComplete="off" value={pin} disabled={busy || stale} onChange={e => setPin(e.target.value)} /></div>
      <button className="buttonPrimary" disabled={busy || stale || !customerName} onClick={() => void action(async () => { const customer = await call<Customer>("/api/pos/customers/", { display_name: customerName, kind }); setCustomers([...customers, customer]); setCustomerName(""); })}>Criar cliente</button>
      {customers.map(customer => <div className="movement" key={customer.id}><div><strong>{customer.display_name}</strong><small>{labels[customer.kind]} · {customer.phone}</small></div><div className="actions">
        <button className="buttonQuiet" disabled={busy || stale || !pin} onClick={() => void action(async () => { await reauth(); const updated = await call<Customer>(`/api/pos/customers/${customer.id}/`, { kind }, "PATCH"); setCustomers(customers.map(c => c.id === updated.id ? updated : c)); })}>Aplicar {labels[kind]}</button>
        {selected && <button className="buttonQuiet" disabled={busy || stale} onClick={() => void action(async () => { await call(`/api/pos/tabs/${selected.id}/customer/`, { customer_id: customer.id }); })}>Associar à comanda</button>}
        <button className="buttonQuiet" disabled={busy || stale} onClick={() => void action(async () => { const detail = await call<Customer & { tabs: Tab[] }>(`/api/pos/customers/${customer.id}/`); setVisits(detail.tabs); })}>Ver visitas</button>
      </div></div>)}
      {visits.map(t => <div className="dataRow" key={t.id}><span>{t.display_label || t.id} · {t.state}</span><strong>{money(t.exposure_cents)}</strong></div>)}
      <p className="muted">Alterar relacionamento afeta novas comandas. Reavalie uma comanda aberta explicitamente para aplicar a nova política.</p>
      <h3>Políticas do estabelecimento</h3>
      <div className="field"><label htmlFor="house-policy-limit">Limite da categoria (centavos)</label><input id="house-policy-limit" type="number" min="0" value={policyAmount} disabled={busy || stale} onChange={e => setPolicyAmount(e.target.value)} /></div>
      <button className="buttonQuiet" disabled={busy || stale} onClick={() => void action(async () => { const data = await call<{ results: Policy[] }>("/api/pos/house-account/policies/"); setPolicies(data.results); })}>Ver políticas</button>
      {policies.map(p => <div className="dataRow" key={p.kind}><span>{labels[p.kind]} · versão {p.version}</span><strong>{money(p.limit_cents)}</strong></div>)}
      {session?.capabilities.includes("venue.configure") && <button className="buttonQuiet" disabled={busy || stale || !pin || !policyAmount} onClick={() => void action(async () => { await reauth(); await call("/api/pos/house-account/policies/", { kind, limit_cents: Number(policyAmount) }, "PUT"); const data = await call<{ results: Policy[] }>("/api/pos/house-account/policies/"); setPolicies(data.results); })}>Salvar limite em centavos para {labels[kind]}</button>}
    </>}
  </section>;
}
