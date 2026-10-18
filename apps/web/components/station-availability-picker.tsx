"use client";

import { useState } from "react";
import { ActionDialog } from "./action-dialog";
import { ProductIcon, type IconData } from "./product-icon";
import { attendanceCategory, compareAttendanceCategories, normalizeCatalogSearch } from "@/lib/client/attendance-catalog";

export type AvailabilityProduct = {
  id: string; name: string; active?: boolean; category?: string; fulfillment_station: "BAR" | "KITCHEN";
  availability: "AVAILABLE" | "UNAVAILABLE"; availability_version?: number; icon?: IconData;
};

export function StationAvailabilityPicker({ products, target, blocked, busy, retryDisabled, pending, error, resultMessage, onConfirm, onRetry, onClose, returnFocus }: {
  products: AvailabilityProduct[]; target: "AVAILABLE" | "UNAVAILABLE";
  blocked: (product: AvailabilityProduct) => boolean; busy: boolean; retryDisabled: boolean;
  pending: (id: string) => boolean; error: (id: string) => string | undefined; resultMessage: (id: string) => string | undefined;
  onConfirm: (product: AvailabilityProduct, target: "AVAILABLE" | "UNAVAILABLE") => void;
  onRetry: (id: string) => void; onClose: () => void; returnFocus: HTMLElement | null;
}) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [picked, setPicked] = useState<AvailabilityProduct | null>(null);
  const verb = target === "UNAVAILABLE" ? "Indisponibilizar" : "Reativar";
  const eligible = products.filter(p => p.active !== false && p.availability !== target);
  const filtered = eligible.filter(p => normalizeCatalogSearch(p.name).includes(normalizeCatalogSearch(query)));
  const categories = [...new Set(filtered.map(attendanceCategory))].sort(compareAttendanceCategories);
  const visible = filtered.filter(p => category === null || category === "" || attendanceCategory(p) === category);
  const current = picked ? products.find(p => p.id === picked.id) : undefined;
  const changed = !!picked && (!current || current.active === false || current.availability !== picked.availability || current.availability_version !== picked.availability_version);
  const closeLayer = () => { if (picked) setPicked(null); else if (category !== null) setCategory(null); else onClose(); };
  const selectedPending = picked && pending(picked.id);

  return <ActionDialog title={picked ? `${verb} ${picked.name}?` : category !== null ? category || "Todos" : `${verb} item`}
    dialogClassName="attendanceCategoryDialog" returnFocus={returnFocus} locked={busy} onClose={closeLayer} dismissOnBackdrop>
    {picked ? <>
      <p>{target === "UNAVAILABLE" ? "O item ficará indisponível para novos pedidos em todos os canais. Pedidos já confirmados serão mantidos." : "O item voltará a ficar disponível para novos pedidos."}</p>
      {changed && !selectedPending && <p className="notice" role="alert">O produto mudou. Volte e escolha o item novamente.</p>}
      {resultMessage(picked.id) && <p className="notice" role="alert">{resultMessage(picked.id)}</p>}
      {error(picked.id) && <p className="notice" role="alert">{error(picked.id)}</p>}
      {selectedPending ? <button className="buttonPrimary" disabled={busy || retryDisabled} onClick={() => onRetry(picked.id)}>{busy ? "Confirmando…" : "Verificar mesma disponibilidade"}</button>
        : <button className="buttonPrimary" disabled={busy || changed || blocked(picked)} onClick={() => onConfirm(picked, target)}>{busy ? "Confirmando…" : `Sim, ${verb.toLowerCase()}`}</button>}
    </> : <>
      <div className="field"><label htmlFor="station-availability-search">Buscar item no cardápio</label><input id="station-availability-search" type="search" value={query} onChange={event => setQuery(event.target.value)} /></div>
      {category === null ? <nav className="attendanceCategoryGrid" aria-label="Categorias da disponibilidade">
        {!!filtered.length && <button className="buttonSecondary" onClick={() => setCategory("")}><strong>Todos</strong><small>{filtered.length} itens</small></button>}
        {categories.map(name => <button className="buttonSecondary" key={name} onClick={() => setCategory(name)}><strong>{name}</strong><small>{filtered.filter(p => attendanceCategory(p) === name).length} itens</small></button>)}
      </nav> : <div className="posProducts">
        {visible.map(product => <button className="buttonSecondary posProduct attendanceProductPick" key={product.id}
          aria-label={`${verb} ${product.name}`} disabled={blocked(product) || pending(product.id)} onClick={() => setPicked({ ...product })}>
          <ProductIcon name={product.name} icon={product.icon} /><strong>{product.name}</strong>
        </button>)}
      </div>}
      {!visible.length && <p role="status">{query.trim() ? "Nenhum item encontrado nesta categoria." : target === "UNAVAILABLE" ? "Nenhum item disponível nesta estação." : "Nenhum item indisponível nesta estação."}</p>}
    </>}
  </ActionDialog>;
}
