"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ActionDialog } from "./action-dialog";
import type { StaffTask } from "@/lib/client/dispatch-target";

export type DeliveryTask = StaffTask & {
  order_item_id?: string | null;
  order_id?: string;
  item_state?: string;
  tab_display_label?: string | null;
  tab_display_reference?: string | null;
};
export type DeliveryQueueItem = DeliveryTask & {
  product_name: string;
  quantity: number;
  tab_label: string;
  age_seconds: number;
};
const identity = (task: DeliveryTask) => JSON.stringify([task.id, task.order_item_id, task.order_id]);
const destination = (task: DeliveryTask) => JSON.stringify([task.target, task.destination_label]);
const isDone = (task: DeliveryTask) => task.state === "DONE" && task.item_state === "DELIVERED";
type Request = <T>(path: string, payload?: object) => Promise<T>;

export function groupDeliveries(deliveries: DeliveryQueueItem[]) {
  const groups = new Map<string, DeliveryQueueItem[]>();
  for (const item of deliveries) {
    const target = item.target;
    const key = item.target_version === 1 && target?.kind === "TAB" && target.tab_id && item.order_item_id
      ? JSON.stringify([target.tab_id, target.table_id, target.occupancy_id, target.generation])
      : item.id;
    const group = groups.get(key);
    if (group) group.push(item);
    else groups.set(key, [item]);
  }
  return [...groups.entries()];
}

export function AttendanceDeliveryGroup({ items, disabled, staffId, request, onLockChange, onResult }: {
  items: DeliveryQueueItem[];
  disabled: boolean;
  staffId: string;
  request: Request;
  onLockChange: (locked: boolean) => void;
  onResult: (completed: string[], error: string) => void;
}) {
  const [selection, setSelection] = useState<Set<string> | null>(null);
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const first = items[0];
  const label = first.tab_display_label || first.tab_label || "Comanda";
  const summary = items.slice(0, 3).map(item => `${item.quantity}× ${item.product_name}`).join(" · ");
  const selected = selection ? items.filter(item => selection.has(item.id)) : [];

  async function complete(batch: DeliveryQueueItem[]) {
    if (lock.current || disabled || !batch.length) return;
    lock.current = true;
    setBusy(true);
    onLockChange(true);
    const completed: string[] = [];
    let error = "";
    try {
      for (const item of batch) {
        const read = async () => {
          const current = await request<DeliveryTask>(`dispatch/tasks/${item.id}/`);
          if (current.task_type !== "DELIVERY" || identity(current) !== identity(item)) throw new Error("A identidade da entrega mudou.");
          return current;
        };
        const current = await read();
        if (!isDone(current)) {
          if (destination(current) !== destination(item) || current.quantity !== item.quantity) throw new Error("O destino ou a quantidade mudou. Confira a fila atualizada.");
          if (!["OPEN", "CLAIMED"].includes(current.state) || !["READY", "PICKED_UP"].includes(current.item_state || "")) throw new Error("Um item deixou de estar pronto.");
          if (current.claimed_by_id && current.claimed_by_id !== staffId) throw new Error("Outra pessoa está responsável por um dos itens.");
          try {
            await request(`dispatch/delivery/${item.id}/complete/`, {});
          } catch {
            // A lost response may still have committed. Read the same task before proceeding.
          }
          if (!isDone(await read())) throw new Error("O registro de um item ainda não foi confirmado.");
        }
        completed.push(item.id);
      }
    } catch (failure) {
      error = failure instanceof Error ? failure.message : "Não foi possível confirmar a entrega.";
    } finally {
      setSelection(null);
      lock.current = false;
      setBusy(false);
      onLockChange(false);
      onResult(completed, error);
    }
  }

  return <article className="ux2QueueItem ux2DeliveryRow">
    <button type="button" className="ux2QueueOpen ux2DeliveryCustomer" disabled={disabled} onClick={() => setSelection(new Set())}>
      <span className="ux2QueueTop"><span className="ux2Delivery">{first.destination_label || "Sem mesa"}</span><span>· {items.length} itens prontos</span></span>
      <strong className="ux2QueueTitle">{label} ›</strong>
      <span className="ux2QueueDetail">{summary}{items.length > 3 ? ` · +${items.length - 3}` : ""}</span>
    </button>
    <button type="button" className="ux2Button ghost" disabled={disabled} onClick={() => void complete(items)}>{busy ? "Confirmando…" : "Confirmar entrega"}</button>
    {selection && <ActionDialog title={`Entregas de ${label}`} locked={busy} onClose={() => setSelection(null)}>
      <p>{first.destination_label || "Sem mesa"}. Marque só os itens que já entregou.</p>
      <div className="ux2DeliveryChoices">
        {items.map(item => <label key={item.id}>
          <input type="checkbox" disabled={disabled} checked={selection.has(item.id)} onChange={event => {
            const next = new Set(selection);
            if (event.target.checked) next.add(item.id); else next.delete(item.id);
            setSelection(next);
          }} />
          <span>{item.quantity}× {item.product_name}{item.fulfillment_station === "BAR" ? " · Bar" : item.fulfillment_station === "KITCHEN" ? " · Cozinha" : ""}</span>
        </label>)}
      </div>
      <button className="buttonPrimary" disabled={disabled || !selected.length} onClick={() => void complete(selected)}>{busy ? "Confirmando…" : `Confirmar ${selected.length} selecionado(s)`}</button>
    </ActionDialog>}
  </article>;
}

/** A delivery stays operational after financial closure. No Tab/ledger read is needed. */
export function AttendanceDeliveryPage({ initialTask, staffId, request, returnFocus, onBack, onLockChange, onConfirmed }: {
  initialTask: DeliveryTask;
  staffId: string;
  request: <T>(path: string, payload?: object) => Promise<T>;
  returnFocus: HTMLElement | null;
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
  const read = useCallback(async () => {
    const current = await request<DeliveryTask>(`dispatch/tasks/${initialTask.id}/`);
    if (current.task_type !== "DELIVERY" || identity(current) !== identity(initialTask)) throw new Error("A identidade da entrega mudou. Volte à fila e confira o item.");
    return current;
  }, [initialTask, request]);
  useEffect(() => {
    alive.current = true;
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
      if (destination(current) !== destination(task)) throw new Error("O destino mudou. Confira o destino atualizado antes de confirmar.");
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
      setError(failure instanceof Error ? failure.message : "Não foi possível confirmar a entrega.");
    } finally { lock.current = false; if (alive.current) { setBusy(false); onLockChange(false); } }
  }
  const rival = !!task.claimed_by_id && task.claimed_by_id !== staffId;
  const ready = ["OPEN", "CLAIMED"].includes(task.state) && ["READY", "PICKED_UP"].includes(task.item_state || "");
  const station = task.fulfillment_station === "BAR" ? "Bar" : task.fulfillment_station === "KITCHEN" ? "Cozinha" : "Estação não informada";
  return <ActionDialog title="Registrar entrega" returnFocus={returnFocus} locked={busy} onClose={onBack}>
    <p><strong>{task.quantity}× {task.product_name}</strong> <small>· {station}</small></p>
    <p>{task.destination_label || "Sem mesa"}{task.tab_display_label ? ` · ${task.tab_display_label}` : ""}{task.tab_display_reference ? ` · ${task.tab_display_reference}` : ""}</p>
    {!ready && !unknown && <p className="ux2Notice" role="status">O status mudou. Confira a fila antes de continuar.</p>}
    {rival && <p className="ux2Notice" role="status">Outra pessoa está responsável por esta entrega.</p>}
    {!fresh && <p className="ux2Notice" role="status">Estado desatualizado. Verifique a entrega antes de continuar.</p>}
    {error && <p className="ux2Notice" role="alert">{error}</p>}
    {unknown && <p className="ux2Notice" role="status">Resultado desconhecido. Confira a mesma tarefa antes de repetir.</p>}
    <button className="buttonPrimary" disabled={busy || (!unknown && fresh && (!ready || rival))} onClick={() => void (unknown || !fresh ? verify() : complete())}>{busy ? "Aguarde…" : unknown || !fresh ? "Verificar entrega" : "Confirmar entrega"}</button>
  </ActionDialog>;
}
