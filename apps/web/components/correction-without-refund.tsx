"use client";

import { useRef, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";

export function CorrectionWithoutRefund({ correction, locked, onPending, onRefresh }: {
  correction: { id: string; item_name: string }; locked: boolean;
  onPending: (pending: boolean) => void; onRefresh: () => Promise<void>;
}) {
  const sending = useRef(false);
  const [busy, setBusy] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [applied, setApplied] = useState(false);
  const [message, setMessage] = useState("");
  async function approve() {
    if (sending.current || (locked && !uncertain && !applied)) return;
    sending.current = true; setBusy(true); onPending(true);
    let resolved = false;
    try {
      if (applied) { await onRefresh(); resolved = true; return; }
      const result = await apiCall<{ status: string; refund_id: null }>(
        `/api/pos/corrections/${correction.id}/settle-without-refund/`,
        { method: "POST", body: "{}" },
      );
      if (result.response.ok && result.body && "status" in result.body && result.body.status === "APPLIED" && result.body.refund_id === null) {
        setApplied(true); setUncertain(false);
        setMessage("Correção aprovada sem devolução de dinheiro. Pagamentos preservados.");
        await onRefresh(); resolved = true;
      } else if (!result.response.ok && result.response.status < 500) {
        resolved = true; setUncertain(false);
        const error = asApiError(result.body);
        setMessage(error.code === "REAUTH_REQUIRED" ? "Confirme o PIN de gerente e aprove esta mesma correção." : error.message);
      } else {
        setUncertain(true); setMessage("Resultado não confirmado. Verifique esta mesma correção antes de continuar.");
      }
    } catch {
      setUncertain(true); setMessage("Não foi possível atualizar o resultado. Verifique esta mesma correção.");
    } finally {
      sending.current = false; setBusy(false); onPending(!resolved);
    }
  }
  return <article className="panel">
    <h3>{correction.item_name}</h3>
    <p>Aprovar a remoção deste item sem devolver dinheiro. O saldo será conferido novamente e o histórico será preservado.</p>
    {message && <p className="notice" role="status" data-state="warning">{message}</p>}
    <button className="buttonPrimary" disabled={busy || (locked && !uncertain && !applied)} onClick={() => void approve()}>
      {busy ? "Verificando…" : applied ? "Atualizar correção aprovada" : uncertain ? "Verificar mesma correção" : `Aprovar correção de ${correction.item_name} sem estorno`}
    </button>
  </article>;
}
