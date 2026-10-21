"use client";

// Observations are deliberately lossy and never own a financial command.
type Origin = { api_root: string; venue: string; session: string; payload: { idempotency_key: string } };
type Outcome = "CONFIRMED" | "REJECTED" | "UNKNOWN" | "PREFLIGHT";
type Reason = "" | "SERVER_REJECTION" | "UNCERTAIN" | "SESSION_CHANGED" | "AUTH_UNAVAILABLE" | "PREPARATION_FAILED";
let active = 0;
function emit(origin: Origin, fields: Record<string, unknown>): void {
  try {
    if (origin.api_root !== "/api/attendance" || active >= 8 || !crypto.subtle) return;
    const eventId = crypto.randomUUID();
    const source = { venue: origin.venue, session: origin.session, key: origin.payload.idempotency_key };
    active += 1;
    void (async () => {
      try {
        const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(source.key));
        const intentRef = Array.from(new Uint8Array(digest), value => value.toString(16).padStart(2, "0")).join("");
        await fetch("/api/attendance-observations", {
          method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ origin_venue: source.venue, origin_session: source.session, events: [{
            event_id: eventId, intent_ref: intentRef, channel: "WEB", ux_version: "033-ux2", app_version: "web-033", ...fields,
          }] }), signal: AbortSignal.timeout(1500),
        });
      } catch { /* A dropped observation cannot change auth, queue or sale state. */ }
      finally { active -= 1; }
    })();
  } catch { /* No crypto/context capability: no observation. */ }
}
export function observeOrderIntentSaved(origin: Origin): void {
  emit(origin, { kind: "INTENT_SAVED" });
}
export function beginOrderObservation(origin: Origin, recovery: boolean): { finish: (outcome: Outcome, reason?: Reason) => void } {
  try {
    const started = performance.now(), attemptId = crypto.randomUUID();
    let finished = false;
    return { finish(outcome, reason = "") {
      try {
        if (finished) return;
        finished = true;
        const elapsed = performance.now() - started;
        emit(origin, { kind: "ATTEMPT_FINISHED", attempt_id: attemptId, outcome, reason, recovery,
          duration_ms: Number.isFinite(elapsed) && elapsed >= 0 && elapsed <= 3_600_000 ? Math.round(elapsed) : null });
      } catch { /* Passive observer, never a command guard. */ }
    } };
  } catch { return { finish() {} }; }
}
