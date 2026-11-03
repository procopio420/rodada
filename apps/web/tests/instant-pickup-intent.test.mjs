import test from "node:test";
import assert from "node:assert/strict";
import { parseProductionIntent } from "../lib/client/production-batch-intent.ts";

const intent = (state) => ({
  schema: 1, venue: "venue", staff: "staff", session: "session",
  captured_at: "2026-10-22T20:00:00.000Z",
  payload: { station: "BAR", idempotency_key: "pickup-test", target_state: "READY",
    lines: [{ item_id: "water", expected_state: state, quantity: 1, snapshot_fingerprint: "a".repeat(64) }] },
});

test("Bar instant pickup READY intent persists original NEW/ACCEPTED precondition", () => {
  for (const state of ["NEW", "ACCEPTED", "PREPARING"]) {
    assert.deepEqual(parseProductionIntent(JSON.stringify(intent(state))), intent(state));
  }
  assert.throws(() => parseProductionIntent(JSON.stringify(intent("DELIVERED"))), /Invalid batch envelope/);
});
