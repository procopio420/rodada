"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { useRealtime } from "@/lib/client/use-realtime";
import { OperationalIcon } from "@/components/operational-icon";
import styles from "@/app/manage/now.module.css";

type ProductSales = { order_item__product_id: string | null; order_item__product_name_snapshot: string | null; quantity: number | null };
type Ranking = { day: string; timezone: string; cutoff: number; rows: { id: string; name: string; quantity: number }[]; updated: number };

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
        const calendar = await read<{ business_date: string; timezone: string; cutoff_hour: number }>("/api/pos/management/calendar/");
        const day = encodeURIComponent(calendar.business_date);
        const report = await read<{ products: ProductSales[] }>(`/api/pos/management/reports/?start=${day}&end=${day}`);
        const products = new Map<string, Ranking["rows"][number]>();
        for (const row of report.products) {
          if (!row.order_item__product_id || !row.quantity || row.quantity < 0) continue;
          const id = row.order_item__product_id;
          const existing = products.get(id);
          if (existing) existing.quantity += row.quantity;
          else products.set(id, { id, name: row.order_item__product_name_snapshot || "Produto sem nome", quantity: row.quantity });
        }
        const rows = [...products.values()].sort((a, b) => b.quantity - a.quantity || a.name.localeCompare(b.name, "pt-BR") || a.id.localeCompare(b.id)).slice(0, 10);
        if (mounted.current && !revoked.current) {
          setRanking({ day: calendar.business_date, timezone: calendar.timezone, cutoff: calendar.cutoff_hour, rows, updated: Date.now() });
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

  return <div id="now-best-sellers" className={styles.ranking}>
    <div className={styles.rankingHeader}>
      <div><h3>Mais vendidos da noite</h3>{ranking && <p>Noite de {ranking.day.split("-").reverse().join("/")}</p>}</div>
      <span className={styles.liveStatus} data-online={connectivity.state === "ONLINE" && !error} role="status"><span aria-hidden="true" />{error ? "Sem atualização" : { ONLINE: "Ao vivo", RECONNECTING: "Reconectando", STALE: "Desatualizado", OFFLINE: "Sem conexão" }[connectivity.state]}</span>
    </div>
    {error && <p className="notice" data-state="danger" role="alert">{error}</p>}
    {!ranking && !error && <p role="status">Carregando mais vendidos…</p>}
    {ranking && <>
      {!ranking.rows.length ? <div className={styles.rankingEmpty}>
        <span className={styles.emptyIcon}><OperationalIcon name="sales" size={24} /></span>
        <strong>Nenhuma venda nesta noite.</strong>
        <p>Os produtos aparecem aqui conforme<br />os pedidos são confirmados.</p>
      </div> : <ol className={styles.rankingList} aria-label="Produtos mais vendidos">
        {ranking.rows.map((row, index) => <li key={row.id}>
          <span className={styles.rank} aria-label={`${index + 1}º lugar`}>{String(index + 1).padStart(2, "0")}</span>
          <strong className={styles.productName}>{row.name}</strong>
          <span className={styles.quantity}><strong>{row.quantity.toLocaleString("pt-BR")}</strong><small>{row.quantity === 1 ? "unidade" : "unidades"}</small></span>
        </li>)}
      </ol>}
    </>}
    <footer className={styles.rankingFooter}>
      <span>{ranking ? `Atualizado às ${new Date(ranking.updated).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}` : "Atualização automática"}</span>
      <button className="buttonQuiet" aria-label="Atualizar ranking" disabled={busy || sessionRevoked} onClick={() => void load().catch(() => {})}><OperationalIcon name="history" size={20} />{busy ? "Atualizando…" : "Atualizar"}</button>
    </footer>
    <details className={styles.rankingMethod}><summary>Como é calculado</summary><p>Os 10 produtos com maior quantidade lançada. Cancelamentos e ajustes não são deduzidos. Atualização automática a cada 15 segundos e ao receber mudanças.</p>{ranking && <p>Dia operacional: {ranking.timezone}, com corte às {ranking.cutoff}h.</p>}</details>
  </div>;
}
