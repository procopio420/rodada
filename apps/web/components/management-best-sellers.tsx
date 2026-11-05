"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { useRealtime } from "@/lib/client/use-realtime";
import { OperationalIcon } from "@/components/operational-icon";
import { attendanceCategory, normalizeCatalogSearch } from "@/lib/client/attendance-catalog";
import styles from "@/app/manage/now.module.css";

type ProductSales = { order_item__product_id: string | null; order_item__product_name_snapshot: string | null; quantity: number | null };
type CatalogProduct = { id: string; name: string; category?: string };
type CategorySales = { name: string; quantity: number };
type RankedProduct = { id: string; name: string; quantity: number };
type Ranking = { day: string; rows: (RankedProduct & { category: string })[]; categories: CategorySales[] | null; updated: number };
const categoryColors = new Map([
  ["cerveja", "var(--color-accent)"], ["cervejas", "var(--color-accent)"],
  ["refrigerantes", "var(--color-info)"], ["aguas", "#71c4e7"],
  ["sucos e outras bebidas", "#45bfb4"], ["energeticos e isotonicos", "#a4bf64"],
  ["drinks", "#dfa6dc"], ["destilados", "var(--color-money)"],
  ["porcoes", "var(--color-success)"], ["petiscos e porcoes", "var(--color-success)"],
  ["salgados", "#d4a16c"], ["pratos quentes", "#ef817d"], ["caldos", "#ebad88"],
  ["outros", "var(--color-text-muted)"], ["todos", "var(--color-text-muted)"],
]);
const extraColors = ["#ef817d", "#45bfb4", "#dfa6dc", "#a4bf64", "#ab9cf7", "#d4a16c", "#71c4e7", "#ebad88"];
function categoryColor(name: string) {
  const key = normalizeCatalogSearch(name);
  const namedColor = categoryColors.get(key);
  if (namedColor) return namedColor;
  const index = Array.from(key).reduce((hash, char) => (hash * 31 + char.charCodeAt(0)) % extraColors.length, 0);
  return extraColors[index];
}

export function ManagementBestSellers() {
  const [ranking, setRanking] = useState<Ranking | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [sessionRevoked, setSessionRevoked] = useState(false);
  const mounted = useRef(false);
  const pending = useRef<Promise<void> | null>(null);
  const revoked = useRef(false);
  const load = useCallback((): Promise<void> => {
    if (pending.current) return pending.current;
    if (revoked.current) return Promise.resolve();
    const read = async <T,>(path: string): Promise<T> => {
      const result = await apiCall<T>(path);
      if (!result.response.ok) throw new Error(asApiError(result.body).message);
      return result.body as T;
    };
    setBusy(true);
    pending.current = (async () => {
      try {
        const calendar = await read<{ business_date: string }>("/api/pos/management/calendar/");
        const day = encodeURIComponent(calendar.business_date);
        const [report, catalog] = await Promise.all([
          read<{ products: ProductSales[] }>(`/api/pos/management/reports/?start=${day}&end=${day}`),
          read<{ results: CatalogProduct[] }>("/api/pos/catalog/products/?include_inactive=true").catch(() => null),
        ]);
        const products = new Map<string, RankedProduct>();
        for (const row of report.products) {
          if (!row.order_item__product_id || !row.quantity || row.quantity < 0) continue;
          const id = row.order_item__product_id;
          const existing = products.get(id);
          if (existing) existing.quantity += row.quantity;
          else products.set(id, { id, name: row.order_item__product_name_snapshot || "Produto sem nome", quantity: row.quantity });
        }
        const byId = new Map(catalog?.results.map(product => [product.id, product]));
        const totals = new Map<string, number>();
        const categorized = [...products.values()].map(product => {
          const current = byId.get(product.id);
          return { ...product, category: current ? attendanceCategory(current) : "Outros" };
        });
        const rows = categorized.sort((a, b) => b.quantity - a.quantity || a.name.localeCompare(b.name, "pt-BR") || a.id.localeCompare(b.id)).slice(0, 10);
        for (const product of categorized) {
          if (normalizeCatalogSearch(product.category) === "todos") continue;
          totals.set(product.category, (totals.get(product.category) ?? 0) + product.quantity);
        }
        const categories = catalog ? [...totals].map(([name, quantity]) => ({ name, quantity }))
          .sort((a, b) => b.quantity - a.quantity || a.name.localeCompare(b.name, "pt-BR")) : null;
        if (mounted.current && !revoked.current) {
          setRanking({ day: calendar.business_date, rows, categories, updated: Date.now() });
          setError("");
        }
      } catch (cause) {
        if (mounted.current && !revoked.current) { setRanking(null); setError(cause instanceof Error ? cause.message : "Não foi possível consultar os mais vendidos."); }
        throw cause;
      } finally { pending.current = null; if (mounted.current) setBusy(false); }
    })();
    return pending.current;
  }, []);
  useEffect(() => {
    mounted.current = true;
    const timer = setInterval(() => { if (document.visibilityState === "visible") void load().catch(() => {}); }, 15000);
    return () => { mounted.current = false; clearInterval(timer); };
  }, [load]);
  const connectivity = useRealtime(load, { onRevoked: () => {
    revoked.current = true; setSessionRevoked(true); setRanking(null); setError("Sessão encerrada. Entre novamente.");
  } });
  const online = connectivity.state === "ONLINE" && !error;
  const status = error ? "Sem atualização" : online ? "Ao vivo" : ranking ? "Atualiza a cada 15 s" : "Conectando";
  const maxQuantity = ranking?.rows[0]?.quantity ?? 1;
  const categoryTotal = ranking?.categories?.reduce((sum, category) => sum + category.quantity, 0) ?? 0;
  let angle = 0;
  const slices = ranking?.categories?.map(category => {
    const color = categoryColor(category.name);
    const start = angle;
    angle += 100 * category.quantity / categoryTotal;
    return { ...category, color, start, end: angle };
  });

  return <div id="now-best-sellers" className={styles.ranking}>
    <div className={styles.rankingHeader}>
      <div>
        <h3>Mais vendidos da noite</h3>
        {ranking && <p>Noite de {ranking.day.split("-").reverse().join("/")} · Atualizado às {new Date(ranking.updated).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</p>}
      </div>
      <div className={styles.rankingControls}>
        <span className={styles.liveStatus} data-online={online} role="status"><span aria-hidden="true" />{status}</span>
        <button className="buttonQuiet" aria-label="Atualizar ranking" disabled={busy || sessionRevoked} onClick={() => void load().catch(() => {})}><OperationalIcon name="history" size={20} />{busy ? "Atualizando…" : "Atualizar"}</button>
      </div>
    </div>
    {error && <p className="notice" data-state="danger" role="alert">{error}</p>}
    {!ranking && !error && <p role="status">Carregando mais vendidos…</p>}
    {ranking && <>
      {!ranking.rows.length ? <div className={styles.rankingEmpty}>
        <span className={styles.emptyIcon}><OperationalIcon name="sales" size={24} /></span>
        <strong>Nenhuma venda nesta noite.</strong>
        <p>Os produtos aparecem aqui conforme<br />os pedidos são confirmados.</p>
      </div> : <div className={styles.charts}>
        <section className={styles.chartPanel} aria-labelledby="best-seller-items">
          <h4 id="best-seller-items">Itens mais vendidos <small>· unidades lançadas</small></h4>
          <ol className={styles.rankingList} tabIndex={0} aria-label="Produtos mais vendidos">
        {ranking.rows.map((row, index) => <li key={row.id}>
          <strong className={styles.quantity}>{row.quantity.toLocaleString("pt-BR")}</strong>
          <span className={styles.barTrack} aria-hidden="true">
            <span className={styles.barFill} style={{ height: `${100 * row.quantity / maxQuantity}%`, backgroundColor: categoryColor(row.category) }} />
          </span>
          <strong className={styles.productName}><span className={styles.rank} aria-label={`${index + 1}º lugar`}>{String(index + 1).padStart(2, "0")}</span> {row.name}</strong>
        </li>)}
          </ol>
        </section>
        <section className={styles.chartPanel} aria-labelledby="best-seller-categories">
          <h4 id="best-seller-categories">Categorias mais vendidas</h4>
          {slices?.length ? <>
            <div className={styles.pie} aria-hidden="true" style={{ backgroundImage: `conic-gradient(${slices.map(slice => `${slice.color} ${slice.start}% ${slice.end}%`).join(", ")})` }} />
            <ul className={styles.categoryLegend} aria-label="Unidades por categoria">
              {slices.map(slice => <li key={slice.name}>
                <span className={styles.categorySwatch} aria-hidden="true" style={{ backgroundColor: slice.color }} />
                <strong>{slice.name}</strong>
                <span>{slice.quantity.toLocaleString("pt-BR")} un. · {(slice.quantity / categoryTotal).toLocaleString("pt-BR", { style: "percent", maximumFractionDigits: 1 })}</span>
              </li>)}
            </ul>
          </> : <p className="muted">{slices ? "Nenhuma categoria com volume nesta noite." : "Categorias indisponíveis no momento."}</p>}
        </section>
      </div>}
    </>}
  </div>;
}
