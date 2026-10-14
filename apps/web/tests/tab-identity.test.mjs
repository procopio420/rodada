import { test } from "node:test";
import assert from "node:assert/strict";
import { tabPrimaryLabel, tabSecondaryLabel, tabReference, tabSearchText } from "../lib/client/tab-identity.ts";

test("two tabs sharing a table show the same physical location but distinct financial references", () => {
  const a = { id: "aaaaaaaa-1234", table_label: "Mesa 08", display_label: "João" };
  const b = { id: "bbbbbbbb-1234", table_label: "Mesa 08", display_label: "João" };
  assert.equal(tabPrimaryLabel(a), "Mesa 08");
  assert.equal(tabPrimaryLabel(b), "Mesa 08");
  assert.notEqual(tabSecondaryLabel(a), tabSecondaryLabel(b));
  assert.match(tabSecondaryLabel(a), /João/);
  assert.equal(tabReference(a), "Comanda AAAAAAAA");
});

test("a table move changes presentation without changing the tab identity", () => {
  const moved = { id: "aaaaaaaa-1234", display_label: "João", table_label: "Mesa 12", last_table_label: "Mesa 08" };
  assert.equal(tabPrimaryLabel(moved), "Mesa 12");
  assert.equal(tabSecondaryLabel(moved), "João · Comanda AAAAAAAA");
  assert.match(tabSearchText(moved), /mesa 12/);
  assert.match(tabSearchText(moved), /mesa 08/);
});

test("no table, anonymous, and closed history have safe labels", () => {
  const anonymous = { id: "ccddeeff-1234", display_label: "", table_label: null };
  assert.equal(tabPrimaryLabel(anonymous), "Comanda CCDDEEFF");
  assert.equal(tabSecondaryLabel(anonymous), "Comanda CCDDEEFF");
  const named = { ...anonymous, display_label: "Cliente balcão" };
  assert.equal(tabPrimaryLabel(named), "Cliente balcão");
  const closed = { ...anonymous, last_table_label: "Mesa 09" };
  assert.equal(tabPrimaryLabel(closed), "Comanda CCDDEEFF");
  assert.equal(tabPrimaryLabel(closed, true), "Mesa 09 (última)");
});
