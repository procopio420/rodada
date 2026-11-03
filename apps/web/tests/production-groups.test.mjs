import test from "node:test";
import assert from "node:assert/strict";
import { groupProductionItems, productionConfiguration } from "../lib/client/production-groups.ts";

const snapshot = () => ({ product_id: "product", product_name: "Item de teste", fulfillment_station: "KITCHEN", variant: null, modifiers: [], special_instructions: "", quantity: 1, unit_price_cents: 1000, line_total_cents: 1000, base_price_cents: 1000 });
const item = (id, changes = {}) => ({ id, product_id: "product", product_name: "Item de teste", quantity: 1, customization_snapshot: { ...snapshot(), ...changes } });
test("Equivalent confirmed configuration groups quantities without changing history", () => {
  const a = item("a"), b = { ...item("b", { quantity: 3, unit_price_cents: 2000, line_total_cents: 6000, base_price_cents: 2000 }), quantity: 3 };
  const before = JSON.stringify([a, b]); Object.freeze(a.customization_snapshot); Object.freeze(b.customization_snapshot);
  const groups = groupProductionItems([a, b], "KITCHEN");
  assert.equal(groups.length, 1); assert.equal(groups[0].quantity, 4); assert.deepEqual(groups[0].items, [a, b]); assert.equal(JSON.stringify([a, b]), before);
});
test("Variant, modifier identity/semantics, exact note and operational fields stay distinct", () => {
  const option = { group_id: "extras", group_name: "Adicionais", option_id: "one", name: "Queijo", semantic_kind: "ADD", price_delta_cents: 100 };
  const rows = [item("default"), item("variant", { variant: { id: "large", name: "Grande" } }), item("note", { special_instructions: "Sem sal" }),
    item("space", { special_instructions: "Sem sal " }), item("option", { modifiers: [option] }), item("remove", { modifiers: [{ ...option, semantic_kind: "REMOVE" }] }),
    item("another-id", { modifiers: [{ ...option, option_id: "two" }] }), item("renamed", { modifiers: [{ ...option, name: "Queijo novo" }] }), item("future", { recipe_version: 2 })];
  assert.equal(groupProductionItems(rows, "KITCHEN").length, rows.length);
});
test("Modifier and JSON field order are irrelevant, variant/modifier price changes are financial", () => {
  const first = { group_id: "g", group_name: "Adicionais", option_id: "a", name: "A", semantic_kind: "ADD", price_delta_cents: 100 };
  const second = { ...first, option_id: "b", name: "B" };
  const a = item("a", { variant: { id: "large", name: "Grande", price_cents: 1200 }, modifiers: [first, second] });
  const b = item("b", { variant: { name: "Grande", price_cents: 1800, id: "large" }, modifiers: [{ ...second, price_delta_cents: 200 }, first] });
  assert.equal(productionConfiguration(a, "KITCHEN"), productionConfiguration(b, "KITCHEN"));
  assert.deepEqual(a.customization_snapshot.modifiers, [first, second]);
});
test("Unknown, incomplete or mismatched history never groups by current product", () => {
  const rows = [ { ...item("missing"), customization_snapshot: undefined }, { ...item("legacy"), customization_snapshot: {} },
    item("missing-variant", { variant: undefined }), item("option-no-id", { modifiers: [{ name: "Queijo", semantic_kind: "ADD" }] }),
    item("wrong-product", { product_id: "other" }), item("wrong-station", { fulfillment_station: "BAR" }), { ...item("no-product"), product_id: undefined } ];
  const groups = groupProductionItems(rows, "KITCHEN"); assert.equal(groups.length, rows.length); assert.ok(groups.every(group => !group.knownConfiguration));
});
test("Product identity and confirmed names cannot merge on display name alone", () => {
  const a = item("a"), b = { ...item("b", { product_id: "other" }), product_id: "other" }, c = { ...item("c"), product_name: "Nome posterior" };
  assert.equal(groupProductionItems([a, b, c], "KITCHEN").length, 3);
});


test("Pickup and prepared Bar products have distinct confirmed configuration", () => {
  const base = { ...snapshot(), fulfillment_station: "BAR" };
  const pickup = { ...item("pickup"), customization_snapshot: { ...base, fulfillment_mode: "PICKUP" } };
  const prepared = { ...item("prepared"), customization_snapshot: { ...base, fulfillment_mode: "PREPARE" } };
  assert.equal(groupProductionItems([pickup, prepared], "BAR").length, 2);
  assert.ok(productionConfiguration(pickup, "BAR"));
});
