export type ManagementOrigin = "setup" | "customers" | "alerts" | "printing";
const key = "rodada.management.return.v1";
const origins = new Set(["setup", "customers", "alerts", "printing"]);

export function rememberManagementOrigin(id: ManagementOrigin) {
  try { sessionStorage.setItem(key, JSON.stringify({ id, scroll: window.scrollY })); } catch { /* Navigation remains available without storage. */ }
}

export function requestManagementReturn(id: ManagementOrigin) {
  try {
    const previous = JSON.parse(sessionStorage.getItem(key) ?? "null");
    if (previous?.id !== id) sessionStorage.setItem(key, JSON.stringify({ id, scroll: 0 }));
  } catch { /* A direct link still returns to Gestão. */ }
}

export function consumeManagementReturn(): { id: ManagementOrigin; scroll: number } | null {
  try {
    const saved = JSON.parse(sessionStorage.getItem(key) ?? "null");
    sessionStorage.removeItem(key);
    if (!saved || !origins.has(saved.id) || !Number.isFinite(saved.scroll) || saved.scroll < 0 || saved.scroll > 10_000_000) return null;
    return saved;
  } catch { return null; }
}
