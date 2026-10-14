export type GuestApiError = { code?: string; message?: string };
export async function guestApi<T>(path: string, token: string, init: RequestInit = {}): Promise<{ ok: boolean; status: number; body: T | GuestApiError }> {
  try {
    const response = await fetch(`/api/guest/${path}`, {
      ...init, cache: "no-store",
      headers: { ...(init.body ? { "Content-Type": "application/json" } : {}), ...(token ? { "X-Guest-Session": token } : {}) },
    });
    return { ok: response.ok, status: response.status, body: await response.json().catch(() => ({})) };
  } catch { return { ok: false, status: 503, body: { code: "OFFLINE", message: "Sem conexão. Os dados podem estar desatualizados. Atualize antes de continuar." } }; }
}
