import assert from "node:assert/strict";
import { test } from "node:test";
import { EventGate, SSEParser } from "../lib/client/realtime.ts";
const event = (version) => ({ id: `venue:${version}`, version, schema_version: 1, venue_id: "venue", aggregate_type: "order_item", aggregate_id: "item", type: "order_item.changed", payload: {} });
test("SSE parser handles delayed chunks and multiple frames", () => {
  const parser = new SSEParser();
  assert.deepEqual(parser.push("event: change\nid: venue:1\ndat"), []);
  assert.deepEqual(parser.push('a: {"state":"READY"}\n\nevent: ready\ndata: {}\n\n'), [
    { event: "change", id: "venue:1", data: '{"state":"READY"}' }, { event: "ready", id: "", data: "{}" },
  ]);
});
test("duplicate and reordered events invalidate once and never roll back", () => {
  const gate = new EventGate();
  assert.equal(gate.accept(event(3)), true);
  assert.equal(gate.accept(event(3)), false);
  assert.equal(gate.accept(event(2)), false);
  assert.equal(gate.accept(event(4)), true);
  gate.reset(); assert.equal(gate.accept(event(2)), true);
});
test("unknown schemas cannot be accepted as canonical", () => {
  assert.equal(new EventGate().accept({ ...event(1), schema_version: 2 }), false);
});

test("stream invalidates HTTP projections, resumes cursor, and resets to snapshot after gap", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.window = { addEventListener() {}, removeEventListener() {} };
  globalThis.document = { addEventListener() {}, removeEventListener() {}, visibilityState: "visible" };
  const { subscribeRealtime } = await import("../lib/client/realtime.ts");
  let snapshots = 0, refreshes = 0, streams = 0;
  const requested = [];
  globalThis.fetch = async (url) => {
    requested.push(String(url));
    if (String(url).includes("snapshot")) { snapshots++; return Response.json({ cursor: `venue:${snapshots === 1 ? 0 : 9}` }); }
    streams++;
    const frames = streams === 1
      ? `event: ready\ndata: {}\n\nevent: change\nid: venue:3\ndata: ${JSON.stringify(event(3))}\n\nevent: change\nid: venue:2\ndata: ${JSON.stringify(event(2))}\n\n`
      : streams === 2 ? 'event: reset\ndata: {}\n\n' : 'event: ready\ndata: {}\n\n';
    return new Response(new ReadableStream({ start(controller) { controller.enqueue(new TextEncoder().encode(frames)); if (streams < 3) controller.close(); } }), { headers: { "Content-Type": "text/event-stream" } });
  };
  const stop = subscribeRealtime({ base: "/realtime", refresh: async () => { refreshes++; }, onState() {} });
  try {
    const deadline = Date.now() + 7000;
    while (streams < 3 && Date.now() < deadline) await new Promise((resolve) => setTimeout(resolve, 20));
    assert.equal(streams, 3);
    assert.equal(snapshots, 2);
    assert.equal(refreshes, 3);
    assert.ok(requested.some((url) => url.includes("cursor=venue%3A3")));
    assert.ok(requested.some((url) => url.includes("cursor=venue%3A9")));
  } finally { stop(); globalThis.fetch = originalFetch; }
});

test("SSE unavailable keeps canonical API fallback usable without sending commands", async () => {
  const originalFetch = globalThis.fetch, originalInterval = globalThis.setInterval;
  globalThis.setInterval = (callback, delay) => originalInterval(callback, delay === 15000 ? 25 : delay);
  const { subscribeRealtime } = await import("../lib/client/realtime.ts");
  let reads = 0; const states = [], requests = [];
  globalThis.fetch = async (url, options) => { requests.push({ url, method: options?.method }); return String(url).includes("snapshot") ? Response.json({ cursor: "venue:0" }) : new Response("unavailable", { status: 503 }); };
  const stop = subscribeRealtime({ base: "/realtime", refresh: async () => { reads++; }, onState(state) { states.push(state); } });
  try {
    await new Promise((resolve) => setTimeout(resolve, 85));
    assert.ok(reads >= 3); assert.ok(states.includes("RECONNECTING"));
    assert.ok(!states.includes("OFFLINE"));
    assert.ok(requests.every((request) => !request.method || request.method === "GET"));
  } finally { stop(); globalThis.fetch = originalFetch; globalThis.setInterval = originalInterval; }
});

test("revoked subscriptions clear projections and stop reconnect", async () => {
  const originalFetch = globalThis.fetch;
  const { subscribeRealtime } = await import("../lib/client/realtime.ts");
  let revoked = 0, refreshes = 0;
  globalThis.fetch = async () => new Response("revoked", { status: 403 });
  const stop = subscribeRealtime({ base: "/guest/realtime", refresh: async () => { refreshes++; }, onState() {}, onRevoked() { revoked++; } });
  try { await new Promise((resolve) => setTimeout(resolve, 10)); assert.equal(revoked, 1); assert.equal(refreshes, 0); }
  finally { stop(); globalThis.fetch = originalFetch; }
});
