"use client";
import { useEffect, useRef, useState } from "react";
import { Connectivity, RealtimeEvent, subscribeRealtime } from "./realtime";

export function useRealtime(refresh: () => Promise<void>, options: { guestToken?: string; relevant?: (event: RealtimeEvent) => boolean; onRevoked?: () => void } = {}) {
  const [status, setStatus] = useState<{ state: Connectivity; syncedAt?: number }>({ state: "RECONNECTING" });
  const callbacks = useRef({ refresh, ...options });
  useEffect(() => { callbacks.current = { refresh, ...options }; });
  const token = options.guestToken;
  useEffect(() => {
    if (token === "") return;
    return subscribeRealtime({
      base: token ? "/api/guest/realtime" : "/api/realtime",
      headers: token ? { "X-Guest-Session": token } : undefined,
      refresh: () => callbacks.current.refresh(),
      relevant: (event) => callbacks.current.relevant?.(event) ?? true,
      onRevoked: () => callbacks.current.onRevoked?.(),
      onState: (state, syncedAt) => setStatus((previous) => previous.state === state && previous.syncedAt === syncedAt ? previous : { state, syncedAt }),
    });
  }, [token]);
  return status;
}
