"use client";
import { useState } from "react";
import { ActionDialog } from "./action-dialog";
import { CustomizationText, type Snapshot } from "./product-customization";
import type { BatchDraft } from "@/lib/client/production-batch-intent";
export type BatchItem = { id: string; state: string; quantity: number; snapshot_fingerprint?: string; product_name: string; tab_label: string; customization_snapshot?: Snapshot };
export function ProductionBatchReview({ station, target, captured, current, unavailable, onClose, onConfirm, returnFocus }: {
  station: "BAR" | "KITCHEN"; target: "PREPARING" | "READY"; captured: BatchItem[]; current: BatchItem[];
  unavailable: boolean; returnFocus: HTMLElement | null; onClose: () => void; onConfirm: (draft: BatchDraft) => void;
}) {
  const [selected, setSelected] = useState<string[]>([]);
  const rows = captured.filter(item => selected.includes(item.id));
  const stale = rows.some(item => {
    const latest = current.find(row => row.id === item.id);
    return !latest || latest.state !== item.state || latest.quantity !== item.quantity || latest.snapshot_fingerprint !== item.snapshot_fingerprint;
  });
  return <ActionDialog title="Revisar lote de produção" onClose={onClose} returnFocus={returnFocus}>
    <p>{station === "KITCHEN" ? "Cozinha" : "Bar"} · {target === "PREPARING" ? "Iniciar preparo" : "Marcar como prontos"}</p>
    <strong>{captured[0].product_name}</strong><CustomizationText snapshot={captured[0].customization_snapshot} />
    <p>Selecione as linhas inteiras. Até 50 linhas por lote.</p>
    {captured.map(item => <label key={item.id} className="customizationChoice">
      <input type="checkbox" checked={selected.includes(item.id)} disabled={!selected.includes(item.id) && selected.length >= 50}
        onChange={event => setSelected(previous => event.target.checked ? [...previous, item.id] : previous.filter(id => id !== item.id))} />
      <span>{item.quantity} {item.product_name} · {item.tab_label || "Sem identificação"} · {item.id.slice(0, 8)}<br />{item.state === "PREPARING" ? "Em preparo" : "Aguardando preparo"}</span>
    </label>)}
    <p role="status">{rows.length} linhas · {rows.reduce((sum, item) => sum + item.quantity, 0)} unidades selecionadas</p>
    {stale && <p role="alert">A fila mudou. Volte e selecione novamente.</p>}
    {unavailable && <p role="alert">Atualize a estação antes de confirmar.</p>}
    <button className="buttonPrimary" disabled={!rows.length || stale || unavailable} onClick={() => onConfirm({ station, target_state: target,
      lines: rows.map(item => ({ item_id: item.id, expected_state: item.state, quantity: item.quantity, snapshot_fingerprint: item.snapshot_fingerprint! })) })}>
      {target === "PREPARING" ? "Iniciar preparo selecionado" : "Marcar selecionados como prontos"}
    </button>
  </ActionDialog>;
}
