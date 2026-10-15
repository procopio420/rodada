import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { createServer } from "node:net";
import { createInterface } from "node:readline";
import { setTimeout as delay } from "node:timers/promises";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";
import { fetchBackend } from "../lib/backend-fetch.ts";

let server;
let base;
let stderr = "";
before(async () => {
  server = spawn(process.env.RODADA_TEST_PYTHON ?? "python", [
    "-u", fileURLToPath(new URL("./backend-fetch-fixture.py", import.meta.url)),
  ], { stdio: ["ignore", "pipe", "pipe"] });
  server.stderr.on("data", chunk => { stderr += chunk.toString(); });
  const lines = createInterface({ input: server.stdout });
  const ready = new Promise((resolve, reject) => {
    lines.on("line", line => {
      const match = /^LISTENING (\d+)$/.exec(line);
      if (match) resolve(`http://127.0.0.1:${match[1]}`);
    });
    server.once("error", reject);
    server.once("exit", code => reject(new Error(`Uvicorn exited ${code}: ${stderr}`)));
  });
  base = await Promise.race([ready, delay(5000, undefined, { ref: false }).then(() => { throw new Error(`Uvicorn readiness timeout: ${stderr}`); })]);
  for (let attempt = 0; ; attempt++) {
    try { await (await fetch(`${base}/stats`)).json(); break; }
    catch (error) { if (attempt === 50) throw error; await delay(20); }
  }
});
after(async () => {
  if (server && server.exitCode === null) {
    const exited = once(server, "exit");
    server.kill("SIGTERM");
    await exited;
  }
});

async function stats() { return (await fetch(`${base}/stats`)).json(); }

test("421 JSON POSTs preserve status and body with exactly one backend request", async () => {
  const before = (await stats()).length;
  for (let index = 0; index < 50; index++) {
    const response = await fetchBackend(`${base}/reject`, {
      method: "POST", body: JSON.stringify({ token: `invalid-${index}` }),
      headers: { "Content-Type": "application/json" }, cache: "no-store",
    });
    assert.equal(response.status, 421);
    assert.deepEqual(await response.json(), { code: "VENUE_HOST_NOT_FOUND" });
  }
  const received = (await stats()).slice(before);
  assert.equal(received.length, 50, "421 must not replay writes");
  received.forEach((request, index) => assert.equal(request.body, JSON.stringify({ token: `invalid-${index}` })));
});

test("successful and forbidden JSON POSTs preserve Unicode payloads", async () => {
  for (const [path, status] of [["/ok", 200], ["/forbidden", 403]]) {
    const response = await fetchBackend(base + path, { method: "POST", body: '{"name":"João 🍋"}' });
    assert.equal(response.status, status);
    assert.deepEqual(await response.json(), { body: '{"name":"João 🍋"}' });
  }
});

test("307 cannot replay a JSON mutation to another URL", async () => {
  const before = (await stats()).length;
  await assert.rejects(fetchBackend(`${base}/redirect`, { method: "POST", body: "{}" }), TypeError);
  assert.deepEqual((await stats()).slice(before).map(request => request.path), ["/redirect"]);
});

test("real connection failures remain rejected transport errors", async () => {
  const unused = createServer();
  await new Promise(resolve => unused.listen(0, "127.0.0.1", resolve));
  const port = unused.address().port;
  await new Promise(resolve => unused.close(resolve));
  await assert.rejects(fetchBackend(`http://127.0.0.1:${port}/`, { method: "POST", body: "{}" }),
    error => error instanceof TypeError && error.cause?.code === "ECONNREFUSED");
});

test("response streaming and caller cancellation remain intact", async () => {
  const controller = new AbortController();
  const response = await fetchBackend(`${base}/stream`, { method: "POST", body: "{}", signal: controller.signal });
  const reader = response.body.getReader();
  assert.equal(new TextDecoder().decode((await reader.read()).value), "first\n");
  controller.abort();
  await assert.rejects(reader.read(), error => error.name === "AbortError");
});


test("an already cancelled mutation never reaches the backend", async () => {
  const before = (await stats()).length;
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(fetchBackend(`${base}/ok`, { method: "POST", body: "{}", signal: controller.signal }),
    error => error.name === "AbortError");
  assert.equal((await stats()).length, before);
});


test("streamed JSON retains the exact UTF8 Content-Length required by DRF", async () => {
  for (const body of ['{"name":"ação 🍺"}', '']) {
    const response = await fetchBackend(`${base}/ok`, { method: "POST", headers: { "Content-Type": "application/json", "Content-Length": "999" }, body });
    await response.text();
    const last = (await stats()).at(-1);
    assert.equal(last.body, body);
    assert.equal(last.content_length, String(Buffer.byteLength(body)));
  }
});
