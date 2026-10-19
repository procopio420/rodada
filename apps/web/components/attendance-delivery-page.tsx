"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import "./attendance-ux2-workspace.css";
import type { StaffTask } from "@/lib/client/dispatch-target";

export type DeliveryTask = StaffTask & {
  order_item_id?: string | null;
  order_id?: string;
  item_state?: string;
  tab_display_label?: string | null;
  tab_display_reference?: string | null;
};
const identity = (task: DeliveryTask) => JSON.stringify([task.id, task.order_item_id, task.order_id]);
const destination = (task: DeliveryTask) => JSON.stringify([task.target, task.destination_label]);
const isDone = (task: DeliveryTask) => task.state === "DONE" && task.item_state === "DELIVERED";

/** A delivery stays operational after financial closure. No Tab/ledger read is needed. */
export function AttendanceDeliveryPage({ initialTask, staffId, request, onBack, onLockChange, onConfirmed }: {
  initialTask: DeliveryTask;
  staffId: string;
  request: <T>(path: string, payload?: object) => Promise<T>;
  onBack: () => void;
  onLockChange: (locked: boolean) => void;
  onConfirmed: () => void;
}) {
  const [task, setTask] = useState(initialTask);
  const [error, setError] = useState("");
  const [fresh, setFresh] = useState(true);
  const [busy, setBusy] = useState(false);
  const [unknown, setUnknown] = useState(false);
  const lock = useRef(false);
  const alive = useRef(true);
  const heading = useRef<HTMLHeadingElement>(null);
  const read = useCallback(async () => {
    const current = await request<DeliveryTask>(`dispatch/tasks/${initialTask.id}/`);
    if (current.task_type !== "DELIVERY" || identity(current) !== identity(initialTask)) throw new Error("A identidade da entrega mudou. Volte à fila e confira o item.");
    return current;
  }, [initialTask, request]);
  useEffect(() => {
    alive.current = true;
    heading.current?.focus();
    const timer = setInterval(() => {
      if (lock.current) return;
      void read().then(current => { if (alive.current && !lock.current) { setTask(current); setFresh(true); } }).catch(() => { if (alive.current) setFresh(false); });
    }, 15000);
    return () => { alive.current = false; clearInterval(timer); };
  }, [read]);
  async function verify() {
    if (lock.current) return;
    lock.current = true; setBusy(true); onLockChange(true); setError("");
    try {
      const current = await read();
      if (!alive.current) return;
      setTask(current); setFresh(true); setUnknown(false);
      if (isDone(current)) onConfirmed();
    } catch (failure) { if (alive.current) { setFresh(false); setError(failure instanceof Error ? failure.message : "Não foi possível verificar a entrega."); } }
    finally { lock.current = false; if (alive.current) { setBusy(false); onLockChange(false); } }
  }
  async function complete() {
    if (lock.current || unknown) return;
    lock.current = true; setBusy(true); onLockChange(true); setError("");
    let sent = false;
    let validated = false;
    try {
      const current = await read();
      if (!alive.current) return;
      setTask(current); setFresh(true); validated = true;
      if (isDone(current)) { onConfirmed(); return; }
      if (destination(current) !== destination(task)) throw new Error("O destino mudou. Confira o destino atualizado antes de registrar.");
      if (!["OPEN", "CLAIMED"].includes(current.state) || !["READY", "PICKED_UP"].includes(current.item_state || "")) throw new Error("A entrega mudou. Confira o estado atualizado.");
      if (current.claimed_by_id && current.claimed_by_id !== staffId) throw new Error("Outra pessoa está responsável por esta entrega.");
      sent = true;
      await request(`dispatch/delivery/${current.id}/complete/`, {});
      const result = await read();
      if (!isDone(result)) throw new Error("O registro ainda não foi confirmado.");
      if (alive.current) { setTask(result); onConfirmed(); }
    } catch (failure) {
      if (!alive.current) return;
      if (!validated) setFresh(false);
      // A lost ACK is reconciled using the same task and item, never another intent.
      if (sent) {
        try {
          const result = await read();
          if (!alive.current) return;
          setTask(result); setFresh(true);
          if (isDone(result)) { setUnknown(false); onConfirmed(); return; }
          setUnknown(false);
        } catch { setUnknown(true); setFresh(false); }
      }
      setError(failure instanceof Error ? failure.message : "Não foi possível registrar a entrega.");
    } finally { lock.current = false; if (alive.current) { setBusy(false); onLockChange(false); } }
  }
  const rival = !!task.claimed_by_id && task.claimed_by_id !== staffId;
  const done = isDone(task);
  const ready = ["OPEN", "CLAIMED"].includes(task.state) && ["READY", "PICKED_UP"].includes(task.item_state || "");
  const station = task.fulfillment_station === "BAR" ? "Bar" : task.fulfillment_station === "KITCHEN" ? "Cozinha" : "Estação não informada";
  return <section className="ux2DeliveryPage" aria-labelledby="delivery-title"><div className="ux2Workspace">
    <button className="ux2Back" disabled={busy} onClick={onBack}><span aria-hidden="true">‹</span> Voltar</button>
    <div className="ux2Eyebrow">Produção · pedido pronto</div>
    <h1 id="delivery-title" ref={heading} tabIndex={-1}>Levar pedido.</h1>
    <p className="ux2Lede">{task.destination_label || "Sem mesa"}{task.tab_display_label ? ` · ${task.tab_display_label}` : ""}{task.tab_display_reference ? ` · ${task.tab_display_reference}` : ""}</p>
    <div className="ux2DeliveryContext"><strong>{done ? "Entrega concluída" : ready ? "Pronto para entrega" : "Entrega atualizada"}</strong><p>{done ? "A tarefa e o item estão confirmados como entregues no servidor." : "Os itens abaixo têm estado confirmado pela produção. Abrir a tarefa não conclui a entrega."}</p></div>
    <div className="ux2SectionHead"><h2>O que levar</h2></div>
    <div className="ux2ReviewRow"><div><strong>{task.quantity}× {task.product_name}</strong><small>Origem · {station}</small></div><span className="ux2Tag">{done ? "Entregue" : task.item_state === "READY" ? "Pronto" : task.item_state === "PICKED_UP" ? "Retirado" : "Atualizado"}</span></div>
    <div className="ux2Notice">Registre a entrega <strong>somente depois de entregar</strong>. O registro manual é uma exceção; abrir esta página não assume nem conclui a tarefa.</div>
    {rival && <p className="ux2Notice" role="status">Outra pessoa está responsável por esta entrega.</p>}
    {!fresh && <p className="ux2Notice" role="status">Estado desatualizado. Verifique a entrega antes de continuar.</p>}
    {error && <p className="ux2Notice" role="alert">{error}</p>}
    {unknown && <p className="ux2Notice" role="status">Resultado desconhecido. Confira a mesma tarefa antes de repetir.</p>}
    <button className="ux2Button ghost block" disabled={busy} onClick={onBack}>{done ? "Voltar à fila" : "Voltar sem concluir"}</button>
    </div>
    {!done && <div className="ux2TaskFoot"><button className="ux2Button primary block" disabled={busy || (!unknown && fresh && (!ready || rival))} onClick={() => void (unknown || !fresh ? verify() : complete())}>{busy ? "Verificando entrega…" : unknown || !fresh ? "Verificar entrega" : "Registrar entrega por exceção"}</button></div>}
  </section>;
}
