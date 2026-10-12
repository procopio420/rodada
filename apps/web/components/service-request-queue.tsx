"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { OperationalHeading } from "@/components/operational-heading";
import { apiCall, asApiError } from "@/lib/client/staff-auth";

type ServiceTask = { id: string; task_type: "SERVICE_REQUEST" | "BILL_REQUEST"; state: string; destination_label: string; claimed_by_id: string | null; age_seconds?: number | null };
type PendingAction = { id: string; action: "claim" | "complete" };

export function ServiceRequestQueue({ staffId }: { staffId: string }) {
  const [tasks, setTasks] = useState<ServiceTask[]>([]);
  const [fresh, setFresh] = useState(false), [loading, setLoading] = useState(true), [busy, setBusy] = useState(false);
  const [error, setError] = useState(""), [notice, setNotice] = useState("");
  const [pending, setPending] = useState<PendingAction | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const reading = useRef(false), sending = useRef(false), active = useRef(true);
  const refresh = useCallback(async () => {
    if (reading.current || sending.current) return;
    reading.current = true;
    setRefreshing(true);
    try {
      const result = await apiCall<{ results: ServiceTask[] }>("/api/attendance/dispatch/requests/");
      if (!result.response.ok || !result.body || !("results" in result.body)) throw new Error(asApiError(result.body).message);
      if (active.current) { setTasks(result.body.results); setFresh(true); setError(""); }
    } catch (failure) {
      if (active.current) { setFresh(false); setError(failure instanceof Error ? failure.message : "Não foi possível atualizar as chamadas."); }
    } finally { reading.current = false; if (active.current) { setLoading(false); setRefreshing(false); } }
  }, []);
  useEffect(() => {
    active.current = true; void refresh();
    const timer = setInterval(() => void refresh(), 15000);
    return () => { active.current = false; clearInterval(timer); };
  }, [refresh]);

  async function act(intent: PendingAction) {
    if (sending.current || reading.current || !fresh) return;
    sending.current = true; setBusy(true); setError(""); setNotice("");
    try {
      const result = await apiCall(`/api/attendance/dispatch/requests/${intent.id}/${intent.action}/`, { method: "POST", body: "{}" });
      if (result.response.ok) { setPending(null); setNotice(intent.action === "claim" ? "Chamada assumida." : "Chamada concluída."); }
      else if (result.response.status >= 500) { setPending(intent); setNotice("Resultado não confirmado. Atualize a fila ou verifique a mesma ação."); }
      else { setPending(null); setNotice(asApiError(result.body).message); }
    } catch { setPending(intent); setNotice("Resultado não confirmado. Atualize a fila ou verifique a mesma ação."); }
    finally { sending.current = false; setBusy(false); await refresh(); }
  }

  return <section className="panel" aria-labelledby="service-queue-heading">
    <OperationalHeading as="h2" icon="people" id="service-queue-heading">Chamadas de atendimento</OperationalHeading>
    {loading && <p role="status">Carregando chamadas…</p>}
    {error && <p className="notice" data-state="danger" role="alert">{error}</p>}
    {!loading && !fresh && <p className="notice" data-state="warning">Chamadas desatualizadas. Atualize antes de agir.</p>}
    {notice && <p className="notice" data-state={pending ? "warning" : "info"} role="status">{notice}</p>}
    <button className="buttonSecondary" disabled={busy || refreshing} onClick={() => void refresh()}>Atualizar chamadas</button>
    {!loading && fresh && tasks.length === 0 && <p className="muted">Nenhuma chamada aberta.</p>}
    {pending && <div className="notice" data-state="warning"><p>Há uma ação sem confirmação. A verificação usa a mesma chamada.</p><button className="buttonSecondary" disabled={busy || refreshing || !fresh} onClick={() => void act(pending)}>Verificar mesma ação</button></div>}
    {tasks.map(task => {
      const other = !!task.claimed_by_id && task.claimed_by_id !== staffId, mine = task.claimed_by_id === staffId;
      return <article className="attendanceItem" key={task.id}>
        <h3>{task.task_type === "BILL_REQUEST" ? "Pedido de conta" : "Atendimento"} · {task.destination_label || "Destino não informado"}</h3>
        <p className="muted">{typeof task.age_seconds === "number" && task.age_seconds >= 0 ? `Solicitado há ${Math.floor(task.age_seconds / 60)} min` : "Tempo não informado"}</p>
        <p>{mine ? "Você está responsável" : other ? "Outro operador está responsável" : "Sem responsável"}</p>
        <div className="actions">
          {!mine && <button className="buttonSecondary" disabled={busy || refreshing || !fresh || other || !!pending} onClick={() => void act({ id: task.id, action: "claim" })}>Assumir chamada</button>}
          <button className="buttonPrimary" disabled={busy || refreshing || !fresh || other || !!pending} onClick={() => void act({ id: task.id, action: "complete" })}>Concluir chamada</button>
        </div>
      </article>;
    })}
  </section>;
}
