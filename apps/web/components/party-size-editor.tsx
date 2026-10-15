"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";

type Observation = { covers_count: number | null; version: number; source: string | null };
type Intent = { covers_count: number; expected_version: number; reason: string; idempotency_key: string };

export function PartySizeEditor({ occupancyId }: { occupancyId: string }) {
  const path = `/api/attendance/hospitality/occupancies/${occupancyId}/party-size/`;
  const id = useId();
  const [current, setCurrent] = useState<Observation | null>(null);
  const [count, setCount] = useState(""), [reason, setReason] = useState("");
  const [fresh, setFresh] = useState(false), [busy, setBusy] = useState(false);
  const [error, setError] = useState(""), [notice, setNotice] = useState("");
  const [pending, setPending] = useState<Intent | null>(null);
  const sending = useRef(false);
  const load = useCallback(async () => {
    try {
      const result = await apiCall<{ current: Observation }>(path);
      if (!result.response.ok || !result.body || !("current" in result.body)) throw new Error(asApiError(result.body).message);
      setCurrent(result.body.current); setFresh(true); setError("");
    } catch (failure) { setFresh(false); setError(failure instanceof Error ? failure.message : "Não foi possível consultar pessoas."); }
  }, [path]);
  useEffect(() => { void load(); }, [load]);
  const valid = /^\d+$/.test(count) && Number(count) > 0 && Number(count) <= 2147483647;
  async function save() {
    if (sending.current || !fresh || !current || (!pending && !valid)) return;
    const intent = pending ?? { covers_count: Number(count), expected_version: current.version, reason, idempotency_key: crypto.randomUUID() };
    sending.current = true; setBusy(true); setError(""); setNotice("");
    try {
      const result = await apiCall<Observation>(path, { method: "POST", body: JSON.stringify(intent) });
      if (result.response.ok && result.body && "covers_count" in result.body) {
        setCurrent(result.body); setPending(null); setCount(""); setReason(""); setNotice("Quantidade confirmada.");
      } else if (result.response.status >= 500) {
        setPending(intent); setNotice("Resultado não confirmado. Verifique a mesma quantidade antes de editar.");
      } else {
        setPending(null); setError(asApiError(result.body).message);
        if (result.response.status === 409) { await load(); setNotice("Confira a quantidade atual e envie novamente somente se a correção ainda for necessária."); }
        else if (result.response.status === 401 || result.response.status === 403) setFresh(false);
      }
    } catch { setPending(intent); setNotice("Resultado não confirmado. Verifique a mesma quantidade antes de editar."); }
    finally { sending.current = false; setBusy(false); }
  }
  return <div>
    <h4>Pessoas na ocupação</h4>
    <p>{current ? current.covers_count === null ? "Quantidade não informada" : `${current.covers_count} pessoa(s) · ${current.source === "GUEST" ? "Informado pelo cliente" : current.source === "STAFF" ? "Informado pela equipe" : "Observação registrada"}` : "Quantidade ainda não consultada"}</p>
    {error && <p className="notice" data-state="danger" role="alert">{error}</p>}
    {notice && <p className="notice" data-state={pending ? "warning" : "info"} role="status">{notice}</p>}
    {!fresh && <button className="buttonSecondary" disabled={busy} onClick={() => void load()}>Consultar quantidade</button>}
    <p className="muted">Opcional. Não altera o saldo nem impede pedidos.</p>
    <div className="field"><label htmlFor={`${id}-count`}>Quantidade de pessoas</label><input id={`${id}-count`} inputMode="numeric" type="number" min={1} max={2147483647} value={count} disabled={busy || !!pending} onChange={event => setCount(event.target.value)} /></div>
    <div className="actions" aria-label="Quantidades rápidas">{[1, 2, 3, 4, 5, 6, 7, 8].map(value => <button className="buttonQuiet" key={value} disabled={busy || !!pending} aria-label={`Selecionar ${value} pessoa${value > 1 ? "s" : ""}`} onClick={() => setCount(String(value))}>{value}</button>)}</div>
    <div className="field"><label htmlFor={`${id}-reason`}>Motivo da correção (opcional)</label><input id={`${id}-reason`} maxLength={500} value={reason} disabled={busy || !!pending} onChange={event => setReason(event.target.value)} /></div>
    <button className="buttonSecondary" disabled={busy || !fresh || !current || (!pending && !valid)} onClick={() => void save()}>{busy ? "Verificando…" : pending ? "Verificar mesma quantidade" : "Confirmar quantidade"}</button>
  </div>;
}
