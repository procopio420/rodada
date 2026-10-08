/** Transport only: events invalidate canonical HTTP projections, never apply commands. */
export type Connectivity = "ONLINE" | "RECONNECTING" | "STALE" | "OFFLINE";
export type RealtimeEvent = { id: string; schema_version: number; type: string; aggregate_type: string; aggregate_id: string; version: number; venue_id: string; payload: Record<string, unknown> };
export type StreamMessage = { event: string; id: string; data: string };

export class SSEParser {
  private buffer = "";
  push(chunk: string): StreamMessage[] {
    this.buffer = (this.buffer + chunk).replace(/\r\n/g, "\n");
    const messages: StreamMessage[] = [];
    let boundary: number;
    while ((boundary = this.buffer.indexOf("\n\n")) >= 0) {
      const block = this.buffer.slice(0, boundary); this.buffer = this.buffer.slice(boundary + 2);
      let event = "message", id = ""; const data: string[] = [];
      for (const line of block.split("\n")) {
        const colon = line.indexOf(":");
        const field = colon < 0 ? line : line.slice(0, colon);
        const value = colon < 0 ? "" : line.slice(colon + 1).replace(/^ /, "");
        if (field === "event") event = value;
        if (field === "id") id = value;
        if (field === "data") data.push(value);
      }
      if (data.length) messages.push({ event, id, data: data.join("\n") });
    }
    return messages;
  }
}

export class EventGate {
  private seen = new Set<string>();
  private versions = new Map<string, number>();
  accept(event: RealtimeEvent): boolean {
    if (event.schema_version !== 1 || !event.id || this.seen.has(event.id)) return false;
    const key = `${event.aggregate_type}:${event.aggregate_id}`;
    if (event.version <= (this.versions.get(key) ?? -1)) return false;
    this.seen.add(event.id); this.versions.set(key, event.version);
    if (this.seen.size > 2048) this.seen.delete(this.seen.values().next().value!);
    if (this.versions.size > 2048) this.versions.delete(this.versions.keys().next().value!);
    return true;
  }
  reset() { this.seen.clear(); this.versions.clear(); }
}

export function subscribeRealtime(options: {
  base: string; headers?: Record<string, string>; refresh: () => Promise<void>;
  relevant?: (event: RealtimeEvent) => boolean;
  onState: (state: Connectivity, syncedAt?: number) => void;
  onRevoked?: () => void;
}) {
  let stopped = false, cursor = "", connected = false, attempt = 0, lastSync = 0, lastFrame = 0, apiOffline = false;
  let refreshPromise: Promise<void> | null = null;
  let controller: AbortController | null = null;
  let wake: (() => void) | undefined;
  const gate = new EventGate();
  const refresh = () => {
    if (!refreshPromise) refreshPromise = options.refresh().then(() => {
      apiOffline = false; lastSync = Date.now(); options.onState(connected ? "ONLINE" : "RECONNECTING", lastSync);
    }).catch((error) => { apiOffline = true; options.onState("OFFLINE", lastSync || undefined); throw error; }).finally(() => { refreshPromise = null; });
    return refreshPromise;
  };
  const snapshot = async () => {
    // Take cursor before fetching projections: concurrent commits replay afterwards.
    const response = await fetch(`${options.base}/snapshot/`, { headers: options.headers, cache: "no-store", signal: controller?.signal });
    if (response.status === 401 || response.status === 403) { options.onRevoked?.(); stopped = true; throw new Error("Unauthorized"); }
    if (!response.ok) throw new Error("Snapshot unavailable");
    const body = await response.json(); await refresh(); cursor = String(body.cursor ?? ""); gate.reset();
  };
  const run = async () => {
    while (!stopped) {
      controller = new AbortController(); lastFrame = Date.now();
      try {
        if (!cursor) await snapshot();
        const response = await fetch(`${options.base}/stream/?cursor=${encodeURIComponent(cursor)}`, {
          headers: { ...options.headers, Accept: "text/event-stream", ...(cursor ? { "Last-Event-ID": cursor } : {}) },
          cache: "no-store", signal: controller.signal,
        });
        if (response.status === 401 || response.status === 403) { options.onRevoked?.(); stopped = true; break; }
        if (!response.ok || !response.body) throw new Error("Stream unavailable");
        lastFrame = Date.now();
        const reader = response.body.getReader(), decoder = new TextDecoder(), parser = new SSEParser();
        while (!stopped) {
          const { value, done } = await reader.read(); if (done) break;
          lastFrame = Date.now();
          let needsRefresh = false, nextCursor = cursor;
          for (const message of parser.push(decoder.decode(value, { stream: true }))) {
            if (message.event === "reset") { cursor = ""; controller.abort(); break; }
            if (message.event === "revoked") { options.onRevoked?.(); stopped = true; controller.abort(); break; }
            if (message.event === "ready") { const ready = JSON.parse(message.data); nextCursor = message.id || String(ready.cursor ?? nextCursor); connected = true; attempt = 0; options.onState("ONLINE", lastSync); }
            if (message.event === "change") {
              const event = JSON.parse(message.data) as RealtimeEvent;
              if (event.schema_version !== 1) { cursor = ""; controller.abort(); break; }
              if (gate.accept(event) && (!options.relevant || options.relevant(event))) needsRefresh = true;
              const candidate = message.id || event.id;
              const sequence = (value: string) => Number(value.slice(value.lastIndexOf(":") + 1));
              if (candidate && sequence(candidate) > sequence(nextCursor)) nextCursor = candidate;
            }
          }
          if (!controller.signal.aborted) {
            if (needsRefresh) await refresh();
            cursor = nextCursor;
          }
        }
      } catch { gate.reset(); /* Failed refresh must be replayable. */ }
      connected = false;
      if (stopped) break;
      options.onState(apiOffline ? "OFFLINE" : Date.now() - lastSync > 30000 ? "STALE" : "RECONNECTING", lastSync || undefined);
      await new Promise<void>((resolve) => { const timer = setTimeout(resolve, Math.min(30000, 1000 * 2 ** Math.min(attempt++, 5)) * (0.75 + Math.random() * 0.5)); wake = () => { clearTimeout(timer); resolve(); }; });
    }
  };
  const watchdog = setInterval(() => { if (Date.now() - lastFrame > 45000) controller?.abort(); }, 10000);
  const fallback = setInterval(() => { if (!connected && !stopped) void refresh().catch(() => {}); }, 15000);
  const resume = () => { if (!stopped) { void refresh().catch(() => {}); controller?.abort(); wake?.(); } };
  const visible = () => { if (document.visibilityState === "visible") resume(); };
  window.addEventListener("online", resume); document.addEventListener("visibilitychange", visible);
  void run();
  return () => { stopped = true; controller?.abort(); wake?.(); clearInterval(fallback); clearInterval(watchdog); window.removeEventListener("online", resume); document.removeEventListener("visibilitychange", visible); };
}
