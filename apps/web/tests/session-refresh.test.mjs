import assert from "node:assert/strict";
import { test } from "node:test";
import { SessionRefreshCoordinator } from "../lib/server/session-refresh.ts";

test("parallel and late requests share one successful rotation", async () => {
  const coordinator = new SessionRefreshCoordinator();
  let release;
  const held = new Promise(resolve => { release = resolve; });
  let calls = 0;
  const rotate = async () => { calls++; await held; return { ok: true, generation: calls }; };
  const requests = Array.from({ length: 8 }, () => coordinator.run("hashed-session", rotate));
  release();
  const results = await Promise.all(requests);
  assert.equal(calls, 1);
  assert.ok(results.every(result => result === results[0]));
  assert.equal(await coordinator.run("hashed-session", rotate), results[0]);
  assert.equal(calls, 1);
});

test("failures release the entry and do not prevent a later successful refresh", async () => {
  const coordinator = new SessionRefreshCoordinator();
  assert.deepEqual(await coordinator.run("a", async () => ({ ok: false })), { ok: false });
  await assert.rejects(coordinator.run("a", async () => { throw Error("offline"); }));
  assert.deepEqual(await coordinator.run("a", async () => ({ ok: true })), { ok: true });
});

test("distinct credentials are isolated and bounded pending work is retained", async () => {
  const coordinator = new SessionRefreshCoordinator(5, 1);
  let release;
  const pending = coordinator.run("a", () => new Promise(resolve => { release = resolve; }));
  await Promise.resolve();
  await assert.rejects(coordinator.run("b", async () => ({ ok: true })), /busy/);
  release({ ok: true, session: "a" });
  assert.equal((await pending).session, "a");
  await new Promise(resolve => setTimeout(resolve, 15));
  assert.equal((await coordinator.run("b", async () => ({ ok: true, session: "b" }))).session, "b");
});

test("expired success rotates again rather than retaining credentials indefinitely", async () => {
  const coordinator = new SessionRefreshCoordinator(5);
  let calls = 0;
  const rotate = async () => ({ ok: true, generation: ++calls });
  await coordinator.run("a", rotate);
  await new Promise(resolve => setTimeout(resolve, 15));
  assert.equal((await coordinator.run("a", rotate)).generation, 2);
});
