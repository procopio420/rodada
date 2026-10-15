"use client";
import { ProductIcon, type IconData } from "@/components/product-icon";
import { money, type OrderingProduct } from "@/components/product-customization";

export function AttendanceCatalogCard({ product, quantity, configurations, locked, fresh, onAdd, onReduce, onCustomize }: {
  product: OrderingProduct & { active: boolean; availability: string; icon?: IconData };
  quantity: number; configurations: number; locked: boolean; fresh: boolean;
  onAdd: () => void; onReduce: () => void; onCustomize: () => void;
}) {
  const unavailable = !product.active || product.availability !== "AVAILABLE";
  return <article className="posProduct" data-selected={quantity > 0}>
    <button className="attendanceProductPick" disabled={locked || !fresh || unavailable} onClick={onAdd}>
      <ProductIcon name={product.name} icon={product.icon} />
      <strong>{product.name}</strong><small>{money(product.price_cents)}</small>
      {unavailable && <span className="muted">Indisponível</span>}
    </button>
    <div className="attendanceCatalogQuantity" role="group" aria-label={`Quantidade de ${product.name}`}>
      <button className="buttonSecondary" aria-label={configurations > 1 ? `Revisar quantidades de ${product.name}` : `Diminuir quantidade de ${product.name}`} disabled={locked || quantity === 0} onClick={onReduce}>−</button>
      <output aria-label={`Quantidade selecionada de ${product.name}`}>{quantity}</output>
      <button className="buttonSecondary" aria-label={`Adicionar ${product.name}`} disabled={locked || !fresh || unavailable} onClick={onAdd}>+</button>
    </div>
    <button className="buttonQuiet" disabled={locked} onClick={onCustomize}>Personalizar</button>
  </article>;
}
