/** Safe read cache isolated by authenticated session; never a command result. */
export function projectionCache<T>(surface: string) {
  let key = "", restored = false;
  const initialize = async () => {
    if (key) return;
    try {
      const context = JSON.parse(sessionStorage.getItem("rodada.projection.context") || "null");
      if (context && context.expiresAt > Date.now()) { key = `rodada.projection.${context.venue}.${context.session}.${surface}`; return; }
    } catch {}
    const response = await fetch("/api/auth/me", { cache: "no-store" });
    if (!response.ok) { clear(); throw new Error("Session unavailable"); }
    const auth = await response.json();
    if (!auth.session?.id || !auth.venue?.id) throw new Error("Session unavailable");
    key = `rodada.projection.${auth.venue.id}.${auth.session.id}.${surface}`;
    try { sessionStorage.setItem("rodada.projection.context", JSON.stringify({ venue: auth.venue.id, session: auth.session.id, expiresAt: Math.min(Date.parse(auth.session.expires_at) || Date.now(), Date.now() + 15 * 60000) })); } catch {}
  };
  const clear = () => {
    for (let i = sessionStorage.length - 1; i >= 0; i--) { const name = sessionStorage.key(i); if (name?.startsWith("rodada.projection.")) sessionStorage.removeItem(name); }
    sessionStorage.removeItem("rodada.projection.context");
    key = "";
  };
  return {
    async restore(): Promise<{ data: T; fetchedAt: number } | null> {
      if (restored) return null;
      restored = true;
      try { await initialize(); const value = sessionStorage.getItem(key); return value ? JSON.parse(value) : null; } catch { return null; }
    },
    save(data: T) { if (key) try { sessionStorage.setItem(key, JSON.stringify({ data, fetchedAt: Date.now() })); } catch {} },
    clear,
  };
}
