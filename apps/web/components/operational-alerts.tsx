"use client";

import { OperationalHeading } from "@/components/operational-heading";

import Link from "next/link";
import { useCallback, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { useRealtime } from "@/lib/client/use-realtime";

type Alert = {
  id: string; rule_key: string; status: string; severity: string;
  source: { target: string; id: string; station?: string; state?: string; age_seconds?: number; tab_id?: string };
};
const labels: Record<string, string> = {
  FULFILLMENT_SLA: "Produção acima do SLA", PAYMENT_PENDING: "Pagamento aguardando confirmação",
  STRATEGIC_PRODUCT: "Produto estratégico indisponível",
  CASH_DISCREPANCY: "Divergência de caixa aguardando revisão",
};


export function OperationalAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const [pending, setPending] = useState<string>();
  const load = useCallback(async () => {
    const result = await apiCall<{ results: Alert[] }>("/api/pos/management/alerts/");
    if (!result.response.ok) {
      setError(asApiError(result.body).message);
      throw new Error("Não foi possível atualizar alertas.");
    }
    setAlerts((result.body as { results: Alert[] }).results);
    setError("");
    setLoaded(true);
  }, []);
  const connectivity = useRealtime(load, {
    relevant: event => event.type.startsWith("alert.") || event.type.startsWith("order.") || event.type.startsWith("payment.") || event.type.startsWith("cash."),
    onRevoked: () => { setAlerts([]); setError("Entre novamente para consultar alertas."); },
  });
  async function acknowledge(id: string) {
    setPending(id);
    try {
      const result = await apiCall<Alert>(`/api/pos/management/alerts/${id}/`, { method: "POST", body: JSON.stringify({}) });
      if (!result.response.ok) throw new Error(asApiError(result.body).message);
      await load();
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Não foi possível confirmar ciência."); }
    finally { setPending(undefined); }
  }
  return <section className="panel" aria-labelledby="operational-alerts-title">
    <OperationalHeading as="h2" icon="warning" id="operational-alerts-title">Alertas operacionais</OperationalHeading>
    <Link className="backLink" href="/manage/alerts/settings">Configurar SLAs →</Link>
    {connectivity.state !== "ONLINE" && <p className="muted">Último estado confirmado. Alertas serão revalidados pela API.</p>}
    {error && <p className="notice" data-state="danger" role="alert">{error}</p>}
    {loaded && !error && !alerts.length && <p className="muted">Nenhuma exceção ativa no último estado consultado.</p>}
    {alerts.map(alert => <div className="movement" key={alert.id}>
      <div><strong>{labels[alert.rule_key] ?? alert.rule_key}</strong>
        <small>{alert.severity === "DANGER" ? "Crítico" : "Atenção"}{alert.source.station ? ` · ${alert.source.station === "BAR" ? "Bar" : "Cozinha"}` : ""}
          {alert.source.age_seconds !== undefined ? ` · ${Math.floor(alert.source.age_seconds / 60)} min nesta etapa` : ""}</small>
        <Link className="backLink" href={`/manage/alerts/${alert.id}`}>Abrir contexto →</Link>
        {alert.status === "ACKNOWLEDGED" ? <small>Ciência registrada · condição continua ativa</small> :
          <button className="buttonSecondary" disabled={!!pending || !loaded || !!error || connectivity.state === "OFFLINE"} onClick={() => void acknowledge(alert.id)}>{pending === alert.id ? "Registrando…" : "Registrar ciência"}</button>}
      </div>
    </div>)}
  </section>;
}
