"use client";
import Link from "next/link";
import { use, useCallback, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { useRealtime } from "@/lib/client/use-realtime";
import { ConnectivityNotice } from "@/components/connectivity-notice";

type Detail = {
  id: string; rule_key: string; rule_version: number; status: string; severity: string;
  source: { target: string; id: string; station?: string; state?: string; age_seconds?: number; source?: string; destination_label?: string; task_type?: string };
  history: { kind: string; occurred_at: string; metadata: { reason?: string; actor_id?: string; before?: string; after?: string } }[];
};
const sourceLabels: Record<string, string> = { FULFILLMENT_ITEM: "Item do pedido", CASH_SHIFT: "Turno de caixa", PAYMENT: "Pagamento", PRODUCT: "Produto", DISPATCH_TASK: "Solicitação de atendimento" };
const eventLabels: Record<string, string> = { ACTIVATED: "Alerta identificado", SEVERITY_CHANGED: "Gravidade aumentada", ACKNOWLEDGED: "Ciência registrada", RESOLVED: "Condição resolvida" };
export default function AlertPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [detail, setDetail] = useState<Detail>();
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    const result = await apiCall<Detail>(`/api/pos/management/alerts/${id}/`);
    if (!result.response.ok) {
      if (result.response.status === 401 || result.response.status === 403 || result.response.status === 404) setDetail(undefined);
      setError(asApiError(result.body).message);
      throw new Error("Não foi possível consultar o alerta.");
    }
    setDetail(result.body as Detail); setError("");
  }, [id]);
  const connectivity = useRealtime(load, { onRevoked: () => { setDetail(undefined); setError("Entre novamente para consultar o contexto."); } });
  return <main className="appShell managementShell">
    <header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div><h1>Contexto do alerta</h1><Link className="backLink" href="/manage">Voltar à operação →</Link></header>
    <ConnectivityNotice {...connectivity} />
    {error && <p className="notice" data-state="danger" role="alert">{error}</p>}
    {detail && <>
      <section className="panel"><h2>{detail.rule_key === "FULFILLMENT_SLA" ? "Produção acima do SLA" : detail.rule_key === "PAYMENT_PENDING" ? "Pagamento aguardando confirmação" : detail.rule_key === "STRATEGIC_PRODUCT" ? "Produto estratégico indisponível" : detail.rule_key === "GUEST_SERVICE_REQUEST_AGED" ? "Solicitação de atendimento atrasada" : "Divergência de caixa"}</h2>
        <p>{detail.status === "RESOLVED" ? "Resolvido pela condição canônica. Este alerta permanece no histórico." : detail.status === "ACKNOWLEDGED" ? "Ciência registrada. A condição continua ativa." : "Condição ativa."}</p>
        <p>Regra versão {detail.rule_version} · {detail.severity === "DANGER" ? "Crítico" : "Atenção"}</p>
        <p>Contexto: {sourceLabels[detail.source.target] ?? "Registro operacional"} · {detail.source.id}</p>
        {detail.source.destination_label && <p>Destino: {detail.source.destination_label} · {detail.source.task_type === "BILL_REQUEST" ? "Solicitação de conta" : "Atendimento"}</p>}
        {detail.source.station && <p>Estação: {detail.source.station} · etapa {detail.source.state}</p>}
        {detail.source.age_seconds !== undefined && <p>{Math.floor(detail.source.age_seconds / 60)} minutos na etapa consultada.</p>}
        <p className="muted">Origem: estado confirmado no servidor. A ciência do gerente não conclui o pedido, pagamento ou revisão de caixa.</p>
        <Link className="backLink" href={detail.source.target === "FULFILLMENT_ITEM" ? detail.source.station === "BAR" ? "/bar" : "/kitchen" : detail.source.target === "CASH_SHIFT" ? "/cash" : detail.source.target === "PRODUCT" ? "/manage/catalog" : detail.source.target === "DISPATCH_TASK" ? "/manage" : "/pos"}>Abrir operação →</Link>
      </section>
      <section className="panel"><h2>Histórico preservado</h2>{detail.history.map((event, index) => <div className="movement" key={index}><div><strong>{eventLabels[event.kind] ?? event.kind}</strong><small>{new Date(event.occurred_at).toLocaleString("pt-BR")}</small>
        {event.metadata.reason && <small>{event.metadata.reason === "CANONICAL_CONDITION_CLEARED" ? "A condição original deixou de exigir ação." : event.metadata.reason}</small>}
        {event.metadata.actor_id && <small>Operador: {event.metadata.actor_id}</small>}
        {event.metadata.before && <small>{event.metadata.before} → {event.metadata.after}</small>}
      </div></div>)}</section>
    </>}
  </main>;
}
