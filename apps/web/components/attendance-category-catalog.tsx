"use client";

import { useEffect, useState } from "react";
import { ActionDialog } from "./action-dialog";
import { ProductIcon, type IconData } from "./product-icon";
import { ProductCustomization, money, type OrderingProduct, type Selection } from "./product-customization";
import { attendanceCategory, compareAttendanceCategories, normalizeCatalogSearch } from "@/lib/client/attendance-catalog";

type Product = OrderingProduct & { fulfillment_station: string; active: boolean; availability: string; category?: string; icon?: IconData };
type Line = { product: Product; quantity: number; selection: Selection };
export const sameCatalogSelection = (a: Selection, b: Selection) => a.variant_id === b.variant_id && a.special_instructions === b.special_instructions && JSON.stringify([...a.modifier_option_ids].sort()) === JSON.stringify([...b.modifier_option_ids].sort());

export function AttendanceCategoryCatalog({ products, lines, locked, fresh, onAdd, onReview, onLayerChange }: {
  products: Product[]; lines: Line[]; locked: boolean; fresh: boolean;
  onAdd: (product: Product, selection: Selection, quantity: number) => boolean;
  onReview: () => void; onLayerChange: (open: boolean) => void;
}) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [picked, setPicked] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);
  useEffect(() => { onLayerChange(category !== null || picked !== null); return () => onLayerChange(false); }, [category, picked, onLayerChange]);
  const filtered = products.filter(p => p.active && normalizeCatalogSearch(p.name).includes(normalizeCatalogSearch(query)));
  const categories = [...new Set(filtered.map(attendanceCategory))].sort(compareAttendanceCategories);
  const visible = filtered.filter(p => category === "" || attendanceCategory(p) === category).sort((a, b) => compareAttendanceCategories(attendanceCategory(a), attendanceCategory(b)) || a.name.localeCompare(b.name, "pt-BR"));
  const current = picked ? products.find(p => p.id === picked.id) ?? { ...picked, active: false } : null;
  const capacity = (selection: Selection) => 99 - lines.filter(line => line.product.id === picked?.id && sameCatalogSelection(line.selection, selection)).reduce((sum, line) => sum + line.quantity, 0);
  return <>
    <div className="field"><label htmlFor="attendance-category-search">Buscar item no cardápio</label><input id="attendance-category-search" type="search" value={query} disabled={locked} onChange={event => setQuery(event.target.value)} /></div>
    <nav className="attendanceCategoryGrid" aria-label="Categorias do cardápio">{!!filtered.length && <button className="buttonSecondary" disabled={locked} aria-haspopup="dialog" onClick={() => setCategory("")}><strong>Todos</strong><small>{filtered.length} itens</small></button>}{categories.map(name => <button className="buttonSecondary" key={name} disabled={locked} aria-haspopup="dialog" onClick={() => setCategory(name)}><strong>{name}</strong><small>{filtered.filter(p => attendanceCategory(p) === name).length} itens</small></button>)}</nav>
    {!categories.length && <p role="status">{!fresh ? "Catálogo ainda não disponível. Atualize para tentar novamente." : query.trim() ? "Nenhum item encontrado." : "Nenhum produto no catálogo."}</p>}
    {category !== null && <ActionDialog title={category || "Todos"} dismissOnBackdrop locked={locked || picked !== null} dialogClassName="attendanceCategoryDialog" onClose={() => setCategory(null)}>
      <div className="posProducts">{visible.map(product => {
        const count = lines.filter(line => line.product.id === product.id).reduce((sum, line) => sum + line.quantity, 0);
        return <button className="buttonSecondary posProduct attendanceProductPick" key={product.id} data-product-id={product.id} data-selected={count > 0} aria-label={`Escolher ${product.name}`} disabled={locked || !fresh || !product.active || product.availability !== "AVAILABLE"} onClick={() => { setQuantity(1); setPicked(product); }}>
          <ProductIcon name={product.name} icon={product.icon} /><strong>{product.name}</strong><small>{money(product.price_cents)}</small>
          {product.availability !== "AVAILABLE" && <span>Indisponível</span>}{count > 0 && <output aria-label={`Quantidade selecionada de ${product.name}`}>{count} no pedido</output>}
        </button>;
      })}</div>
      {!filtered.some(p => category === "" || attendanceCategory(p) === category) && <p>Nenhum produto nesta categoria.</p>}
      <button className="buttonPrimary attendanceCategoryReview" disabled={locked || picked !== null} onClick={() => { setCategory(null); onReview(); }}>Ver pedido atual · {lines.reduce((sum, line) => sum + line.quantity, 0)} itens</button>
    </ActionDialog>}
    {current && <ActionDialog title={`Adicionar ${current.name}`} dismissOnBackdrop locked={locked} dialogClassName="attendanceItemDialog" onClose={() => setPicked(null)}>
      <ProductCustomization product={current} compactOptions quantity={quantity} onQuantityChange={setQuantity} quantityCapacity={capacity}
        canSubmit={!locked && fresh && current.active && current.availability === "AVAILABLE"} onCancel={() => setPicked(null)}
        onAdd={selection => { if (onAdd(current, selection, quantity)) setPicked(null); }} />
    </ActionDialog>}
  </>;
}
