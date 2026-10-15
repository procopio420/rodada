"use client";
import { sameCatalogSelection } from "@/components/attendance-category-catalog";
import { OperationalHeading } from "@/components/operational-heading";
import { CustomizationText, selectionError, unitPrice, type OrderingProduct, type Selection } from "@/components/product-customization";

export type DraftLine = { product: OrderingProduct & { active: boolean; availability: string }; quantity: number; selection: Selection };
const money = (cents: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);
export function AttendanceDraft({ rows, locked, fresh, onQuantity, onEdit, children }: {
 rows: DraftLine[]; locked: boolean; fresh: boolean; onQuantity: (index: number, delta: number) => void; onEdit: (index: number) => void; children: React.ReactNode;
}) {
 return <section className="attendanceDraft" aria-label="Pedido atual" tabIndex={-1} data-attendance-region="draft">
  <div className="attendanceDraftHeading"><OperationalHeading as="h2" icon="cart">Pedido atual</OperationalHeading><span className="muted">{rows.reduce((sum, row) => sum + row.quantity, 0)} itens</span></div>
  {!rows.length && <p className="muted">Selecione os itens no catálogo abaixo.</p>}
  {rows.map((row, index) => <article className="attendanceDraftLine" key={index}>
   <div className="attendanceDraftDescription"><strong>{row.quantity}× {row.product.name}</strong><CustomizationText snapshot={{ variant: row.product.variants?.find(v => v.id === row.selection.variant_id), modifiers: row.product.modifier_groups?.flatMap(g => g.options.filter(o => row.selection.modifier_option_ids.includes(o.id)).map(o => ({ ...o, group_name: g.name }))), special_instructions: row.selection.special_instructions }} />
    {selectionError(row.product, row.selection) && <p className="notice" data-state="danger" role="alert">{selectionError(row.product, row.selection)}</p>}
    {(!row.product.active || row.product.availability !== "AVAILABLE") && <p className="muted">Item indisponível. Retire ou revise o pedido.</p>}
   </div>
   <span className="attendanceDraftPrice">{money(unitPrice(row.product, row.selection) * row.quantity)}</span>
   <div className="attendanceDraftControls"><div className="attendanceQuantity" role="group" aria-label={`Quantidade de ${row.product.name}`}>
    <button className="buttonSecondary" aria-label={`Diminuir quantidade de ${row.product.name}`} disabled={locked} onClick={() => onQuantity(index, -1)}>−</button>
    <output aria-label={`Quantidade selecionada de ${row.product.name}`}>{row.quantity}</output>
    <button className="buttonSecondary" aria-label={`Aumentar quantidade de ${row.product.name}`} disabled={locked || !fresh || !row.product.active || row.product.availability !== "AVAILABLE" || rows.filter(line => line.product.id === row.product.id && sameCatalogSelection(line.selection, row.selection)).reduce((sum, line) => sum + line.quantity, 0) >= 99} onClick={() => onQuantity(index, 1)}>+</button>
   </div><button className="buttonQuiet" disabled={locked} onClick={() => onEdit(index)}>Editar</button></div>
  </article>)}
  {children}
 </section>;
}
