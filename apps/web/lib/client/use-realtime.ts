"use client";
import { useEffect, useRef, useState } from "react";
import { Connectivity, RealtimeEvent, RealtimeAuthError, subscribeRealtime } from "./realtime";

export function useRealtime(refresh: () => Promise<void>, options: { guestToken?: string; relevant?: (event: RealtimeEvent) => boolean; onRevoked?: (error?: RealtimeAuthError) => void } = {}) {
  const [status, setStatus] = useState<{ state: Connectivity; syncedAt?: number }>({ state: "RECONNECTING" });
  const callbacks = useRef({ refresh, ...options });
  useEffect(() => { callbacks.current = { refresh, ...options }; });
  const token = options.guestToken;
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    void navigator.serviceWorker.register("/operational-sw.js").then(async () => {
      const registration = await navigator.serviceWorker.ready;
      const urls = [location.href, ...performance.getEntriesByType("resource").map(entry => entry.name)];
      registration.active?.postMessage({ type: "CACHE_OPERATIONAL_SHELL", urls });
    }).catch(() => {});
  }, []);
  useEffect(() => {
    if (token === "") return;
    return subscribeRealtime({
      base: token ? "/api/guest/realtime" : "/api/realtime",
      headers: token ? { "X-Guest-Session": token } : undefined,
      refresh: () => callbacks.current.refresh(),
      relevant: (event) => callbacks.current.relevant?.(event) ?? true,
      onRevoked: (error) => callbacks.current.onRevoked?.(error),
      onState: (state, syncedAt) => setStatus((previous) => previous.state === state && previous.syncedAt === syncedAt ? previous : { state, syncedAt }),
    });
  }, [token]);
  return status;
}
