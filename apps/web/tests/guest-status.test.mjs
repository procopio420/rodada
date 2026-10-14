import { test } from "node:test";
import assert from "node:assert/strict";
import { guestItemStatus } from "../lib/client/guest-status.ts";

test("guest states remain truthful across preparation, delivery and cancellation", () => {
  for (const state of ["NEW", "ACCEPTED"]) assert.equal(guestItemStatus(state), "Recebido");
  assert.equal(guestItemStatus("PREPARING"), "Preparando");
  for (const state of ["READY", "PICKED_UP"]) assert.equal(guestItemStatus(state), "Pronto / chegando");
  assert.equal(guestItemStatus("DELIVERED"), "Entregue");
  assert.equal(guestItemStatus("CANCELLED"), "Cancelado");
  assert.equal(guestItemStatus("UNRECOGNIZED"), "Estado indisponível");
});
