"use client";

import { useEffect, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { OperationalHeading } from "@/components/operational-heading";

type Policy = { enabled: boolean; version: number };
type Command = { enabled: boolean; expected_version: number; idempotency_key: string };
export function TableServiceRollout({ scope }: { scope: string }) {
  const key = `rodada:table-service-rollout:${scope}`;
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [pending, setPending] = useState<Command | null>(null);
  const [busy, setBusy] = useState(false), [blocked, setBlocked] = useState(false), [message, setMessage] = useState("");
  const path = "/api/pos/management/table-service-rollout/";
  async function refresh() {
    const result = await apiCall<Policy>(path);
    if (!result.response.ok) throw new Error(asApiError(result.body).message);
    setPolicy(result.body as Policy);
  }
  useEffect(() => {
    try { const raw = localStorage.getItem(key); if (raw) setPending(JSON.parse(raw)); }
    catch { setBlocked(true); setMessage("Configuração pendente indisponível. Confira o histórico antes de alterar."); }
    void refresh().catch(error => setMessage(error.message));
  }, [key]);
  async function apply() {
    if (busy || blocked || !policy) return;
    const command = pending ?? { enabled: !policy.enabled, expected_version: policy.version, idempotency_key: crypto.randomUUID() };
    setBusy(true);
    try {
      localStorage.setItem(key, JSON.stringify(command)); setPending(command);
      const result = await apiCall<Policy>(path, { method: "POST", body: JSON.stringify(command) });
      if (!result.response.ok) {
        if ([400, 404, 409, 422].includes(result.response.status)) { localStorage.removeItem(key); setPending(null); await refresh(); }
        throw new Error(asApiError(result.body).message);
      }
      localStorage.removeItem(key); setPending(null); await refresh(); setMessage("Configuração confirmada.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Resposta desconhecida. Verifique a mesma alteração."); }
    finally { setBusy(false); }
  }
  return <section className="panel"><OperationalHeading as="h2" icon="table">Atendimento pelas mesas</OperationalHeading>
    <p>{policy ? policy.enabled ? "Ativo neste estabelecimento" : "Desativado neste estabelecimento" : "Carregando configuração…"}</p>
    <p className="muted">Ativar libera início com responsável e nova comanda contextual. Desativar preserva ocupações, comandas e recuperação de operações confirmadas.</p>
    {message && <p className="notice" role="status">{message}</p>}
    <button className="buttonSecondary" disabled={busy || blocked || !policy} onClick={() => void apply()}>{busy ? "Verificando…" : pending ? "Verificar mesma alteração" : policy?.enabled ? "Desativar atendimento pelas mesas" : "Ativar atendimento pelas mesas"}</button>
  </section>;
}
